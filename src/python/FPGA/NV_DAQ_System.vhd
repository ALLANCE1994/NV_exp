-- NI USB-7855R FPGA 顶层系统模块
-- 文件3: NV_DAQ_System.vhd - 完整采集系统顶层
-- 此文件用于导入到LabVIEW FPGA项目

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity NV_DAQ_System is
    port (
        -- 40MHz FPGA时钟
        FPGA_CLK : in std_logic;
        
        -- 全局复位 (低电平有效)
        RESET_N : in std_logic;
        
        -- 外部数字触发输入 (来自PulseBlaster)
        TRIG_IN : in std_logic;
        
        -- AI0-7: 模拟输入通道 (USB-7855R有8路16位ADC)
        AI0 : in std_logic_vector(15 downto 0);
        AI1 : in std_logic_vector(15 downto 0);
        AI2 : in std_logic_vector(15 downto 0);
        AI3 : in std_logic_vector(15 downto 0);
        AI4 : in std_logic_vector(15 downto 0);
        AI5 : in std_logic_vector(15 downto 0);
        AI6 : in std_logic_vector(15 downto 0);
        AI7 : in std_logic_vector(15 downto 0);
        
        -- AO0-1: 模拟输出通道
        AO0 : out std_logic_vector(15 downto 0);
        AO1 : out std_logic_vector(15 downto 0);
        
        -- DIO0-31: 数字输入
        DIO_IN : in std_logic_vector(31 downto 0);
        -- DIO0-31: 数字输出
        DIO_OUT : out std_logic_vector(31 downto 0);
        -- DIO方向控制 (高电平为输出)
        DIO_DIR : out std_logic_vector(31 downto 0);
        
        -- LED指示 (板载LED)
        LED : out std_logic_vector(3 downto 0)
    );
end entity NV_DAQ_System;

architecture TOP of NV_DAQ_System is

    -- 内部信号定义
    signal rst : std_logic;
    signal ctrl_reg : std_logic_vector(15 downto 0) := (others => '0');
    signal stat_reg : std_logic_vector(15 downto 0);
    signal samples_reg : std_logic_vector(15 downto 0) := X"0080";  -- 默认128点
    signal divider_reg : std_logic_vector(15 downto 0) := X"0014";   -- 默认20分频 -> 1MHz
    signal trig_edge_reg : std_logic := '0';  -- 上升沿
    
    -- ADC数据
    signal adc_data : std_logic_vector(15 downto 0);
    signal adc_clk : std_logic;
    signal adc_start : std_logic;
    
    -- 差分输入信号
    signal diff_data : signed(15 downto 0);
    
    -- FIFO信号
    signal fifo_din : std_logic_vector(15 downto 0);
    signal fifo_we : std_logic;
    signal fifo_rd : std_logic;
    signal fifo_dout : std_logic_vector(15 downto 0);
    signal fifo_empty : std_logic;
    signal fifo_full : std_logic;
    signal fifo_count : std_logic_vector(10 downto 0);
    
    -- 触发信号
    signal trig_armed : std_logic;
    signal trig_busy : std_logic;
    signal trig_done : std_logic;
    
    -- 时钟域
    signal pll_locked : std_logic := '1';
    
begin

    rst <= not RESET_N;
    
    -- APD差分输入模式: AI0(+) - AI1(-)
    -- 适用于差分输出的跨阻放大器
    diff_data <= signed(AI0) - signed(AI1);
    adc_data <= std_logic_vector(diff_data);
    
    -- LED指示灯控制
    LED(0) <= trig_busy;      -- LED0: 采集进行中
    LED(1) <= trig_done;     -- LED1: 采集完成
    LED(2) <= fifo_empty;    -- LED2: FIFO空 (数据已读出)
    LED(3) <= trig_armed;    -- LED3: 等待触发
    
    -- DAQ控制器实例
    DAQ_INST : entity work.DAQ_Controller
        generic map (
            CLK_FREQ_HZ => 40_000_000,
            ADC_BITS => 16,
            MAX_SAMPLES => 1024
        )
        port map (
            CLK => FPGA_CLK,
            RST => rst,
            ADC_D => adc_data,
            ADC_CLK => adc_clk,
            ADC_START => adc_start,
            TRIG_IN => TRIG_IN,
            TRIG_EDGE => trig_edge_reg,
            REG_SAMPLES => samples_reg,
            REG_DIVIDER => divider_reg,
            REG_CONTROL => ctrl_reg,
            STAT_REG => stat_reg,
            FIFO_DIN => fifo_din,
            FIFO_WE => fifo_we
        );
    
    -- 状态信号提取
    trig_armed <= stat_reg(4);
    trig_busy <= stat_reg(0);
    trig_done <= stat_reg(1);
    
    -- FIFO实例
    FIFO_INST : entity work.DAQ_FIFO
        generic map (
            DATA_WIDTH => 16,
            DEPTH => 1024,
            ADDR_BITS => 10
        )
        port map (
            CLK => FPGA_CLK,
            RST => rst,
            WR_DATA => fifo_din,
            WR_EN => fifo_we,
            WR_FULL => fifo_full,
            WR_AFULL => open,
            RD_DATA => fifo_dout,
            RD_EN => fifo_rd,
            RD_EMPTY => fifo_empty,
            RD_AEMPTY => open,
            COUNT => fifo_count
        );
    
    -- DMA/FIFO读取控制 - 当FIFO非空时自动读取
    -- 注意: fifo_rd应由主机通过FPGA寄存器或DMA请求控制
    fifo_rd <= '0';  -- 默认不读出，由上层模块控制
    
    -- 简单的寄存器读写逻辑 (用于软件配置)
    process(FPGA_CLK, rst)
    begin
        if rst = '1' then
            ctrl_reg <= (others => '0');
            samples_reg <= X"0080";
            divider_reg <= X"0014";
            trig_edge_reg <= '0';
        elsif rising_edge(FPGA_CLK) then
            -- 软件通过DIO或内部寄存器写入
            -- 这里可以使用并行端口或FPGA接口
            -- 默认值已在初始化中设置
            null;
        end if;
    end process;
    
    -- 模拟输出保持
    AO0 <= (others => '0');
    AO1 <= (others => '0');
    
    -- DIO端口方向配置 (默认全部设为输入)
    DIO_DIR <= (others => '0');  -- '0'=输入, '1'=输出
    DIO_OUT <= (others => '0');   -- 默认输出低电平
    
end architecture TOP;