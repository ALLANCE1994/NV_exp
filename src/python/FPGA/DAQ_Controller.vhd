-- NI USB-7855R FPGA 数据采集核心模块
-- 用于NV色心实验的数据采集控制
-- 兼容LabVIEW FPGA编译工具
-- 文件1: DAQ_Controller.vhd - 核心采集控制器

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity DAQ_Controller is
    generic (
        CLK_FREQ_HZ : natural := 40_000_000;
        ADC_BITS : natural := 16;
        MAX_SAMPLES : natural := 1024
    );
    port (
        CLK : in std_logic;
        RST : in std_logic;
        
        -- ADC接口
        ADC_D : in std_logic_vector(ADC_BITS-1 downto 0);
        ADC_CLK : out std_logic;
        ADC_START : out std_logic;
        
        -- 触发接口
        TRIG_IN : in std_logic;
        TRIG_EDGE : in std_logic;  -- '0'=上升沿, '1'=下降沿
        
        -- 配置寄存器
        REG_SAMPLES : in std_logic_vector(15 downto 0);
        REG_DIVIDER : in std_logic_vector(15 downto 0);
        REG_CONTROL : in std_logic_vector(15 downto 0);
        
        -- 状态输出
        STAT_REG : out std_logic_vector(15 downto 0);
        
        -- FIFO接口
        FIFO_DIN : out std_logic_vector(ADC_BITS-1 downto 0);
        FIFO_WE : out std_logic
    );
end entity DAQ_Controller;

architecture RTL of DAQ_Controller is

    -- 常量定义
    constant DIVIDER_MIN : natural := 1;
    constant DIVIDER_MAX : natural := 65535;
    
    -- 状态机类型
    type STATE_T is (
        S_IDLE,
        S_ARM,
        S_WAIT,
        S_SAMPLE,
        S_DONE,
        S_ERROR
    );
    signal state : STATE_T := S_IDLE;
    signal next_state : STATE_T;
    
    -- 内部信号
    signal sample_cnt : unsigned(15 downto 0) := (others => '0');
    signal desired_samples : unsigned(15 downto 0);
    signal divider : unsigned(15 downto 0);
    signal clk_div_cnt : unsigned(15 downto 0) := (others => '0');
    signal adc_clk_int : std_logic := '0';
    signal adc_clk_en : std_logic := '0';
    
    -- 触发同步
    signal trig_sync : std_logic_vector(2 downto 0) := (others => '0');
    signal trig_detected : std_logic := '0';
    
    -- 控制寄存器位
    alias ctrl_start : std_logic is REG_CONTROL(0);
    alias ctrl_reset : std_logic is REG_CONTROL(1);
    alias ctrl_enable : std_logic is REG_CONTROL(2);
    
    -- 状态寄存器内部信号
    signal stat_reg_int : std_logic_vector(15 downto 0) := (others => '0');
    
    -- 状态寄存器位别名
    alias stat_busy : std_logic is stat_reg_int(0);
    alias stat_done : std_logic is stat_reg_int(1);
    alias stat_fifo_full : std_logic is stat_reg_int(2);
    alias stat_error : std_logic is stat_reg_int(3);
    alias stat_trigarmed : std_logic is stat_reg_int(4);
    
begin

    desired_samples <= unsigned(REG_SAMPLES);
    divider <= unsigned(REG_DIVIDER) when unsigned(REG_DIVIDER) >= DIVIDER_MIN else to_unsigned(DIVIDER_MIN, 16);
    
    -- 状态寄存器输出
    STAT_REG <= stat_reg_int;

    -- ADC时钟分频
    process(CLK, RST)
    begin
        if RST = '1' then
            clk_div_cnt <= (others => '0');
            adc_clk_int <= '0';
        elsif rising_edge(CLK) then
            if state = S_IDLE or state = S_ARM then
                clk_div_cnt <= (others => '0');
                adc_clk_int <= '0';
            elsif clk_div_cnt >= divider then
                clk_div_cnt <= (others => '0');
                adc_clk_int <= not adc_clk_int;
            else
                clk_div_cnt <= clk_div_cnt + 1;
            end if;
        end if;
    end process;
    
    -- ADC时钟使能 - 只在S_SAMPLE状态产生
    adc_clk_en <= adc_clk_int when state = S_SAMPLE else '0';
    ADC_CLK <= adc_clk_int;

    -- 触发同步和边沿检测
    process(CLK, RST)
    begin
        if RST = '1' then
            trig_sync <= (others => '0');
            trig_detected <= '0';
        elsif rising_edge(CLK) then
            trig_sync <= trig_sync(1 downto 0) & TRIG_IN;
            
            if TRIG_EDGE = '0' then
                trig_detected <= trig_sync(2) and not trig_sync(1);
            else
                trig_detected <= not trig_sync(2) and trig_sync(1);
            end if;
        end if;
    end process;

    -- 状态机注册
    process(CLK, RST)
    begin
        if RST = '1' then
            state <= S_IDLE;
        elsif rising_edge(CLK) then
            state <= next_state;
        end if;
    end process;

    -- 状态机组合逻辑
    process(state, trig_detected, ctrl_start, ctrl_reset, ctrl_enable,
            sample_cnt, desired_samples, adc_clk_int)
    begin
        next_state <= state;
        ADC_START <= '0';
        FIFO_WE <= '0';
        stat_busy <= '0';
        stat_done <= '0';
        stat_error <= '0';
        
        case state is
            when S_IDLE =>
                stat_trigarmed <= '0';
                if ctrl_enable = '1' then
                    next_state <= S_ARM;
                end if;
                
            when S_ARM =>
                stat_trigarmed <= '1';
                if trig_detected = '1' then
                    next_state <= S_WAIT;
                elsif ctrl_reset = '1' then
                    next_state <= S_IDLE;
                end if;
                
            when S_WAIT =>
                stat_busy <= '1';
                ADC_START <= '1';
                if adc_clk_int = '1' then
                    next_state <= S_SAMPLE;
                end if;
                
            when S_SAMPLE =>
                stat_busy <= '1';
                FIFO_WE <= '1';
                if adc_clk_int = '1' then
                    if sample_cnt >= desired_samples - 1 then
                        next_state <= S_DONE;
                    end if;
                end if;
                
            when S_DONE =>
                stat_done <= '1';
                if trig_detected = '1' and ctrl_enable = '1' then
                    next_state <= S_WAIT;
                elsif ctrl_reset = '1' then
                    next_state <= S_IDLE;
                end if;
                
            when others =>
                stat_error <= '1';
                next_state <= S_ERROR;
        end case;
    end process;

    -- 数据输出和计数器
    process(CLK, RST)
    begin
        if RST = '1' then
            sample_cnt <= (others => '0');
            FIFO_DIN <= (others => '0');
        elsif rising_edge(CLK) then
            if state = S_ARM or state = S_IDLE then
                sample_cnt <= (others => '0');
            elsif state = S_SAMPLE and adc_clk_int = '1' then
                FIFO_DIN <= ADC_D;
                if sample_cnt < desired_samples - 1 then
                    sample_cnt <= sample_cnt + 1;
                end if;
            end if;
        end if;
    end process;

end architecture RTL;