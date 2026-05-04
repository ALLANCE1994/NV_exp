-- NI USB-7855R FPGA FIFO缓冲模块
-- 文件2: DAQ_FIFO.vhd - 数据FIFO缓冲控制器

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity DAQ_FIFO is
    generic (
        DATA_WIDTH : natural := 16;
        DEPTH : natural := 1024;
        ADDR_BITS : natural := 10
    );
    port (
        CLK : in std_logic;
        RST : in std_logic;
        
        -- 写入接口
        WR_DATA : in std_logic_vector(DATA_WIDTH-1 downto 0);
        WR_EN : in std_logic;
        WR_FULL : out std_logic;
        WR_AFULL : out std_logic;
        
        -- 读取接口
        RD_DATA : out std_logic_vector(DATA_WIDTH-1 downto 0);
        RD_EN : in std_logic;
        RD_EMPTY : out std_logic;
        RD_AEMPTY : out std_logic;
        
        -- 计数输出
        COUNT : out std_logic_vector(ADDR_BITS downto 0)
    );
end entity DAQ_FIFO;

architecture RTL of DAQ_FIFO is

    -- FIFO存储数组
    type FIFO_MEM is array (0 to DEPTH-1) of std_logic_vector(DATA_WIDTH-1 downto 0);
    signal mem : FIFO_MEM := (others => (others => '0'));
    
    -- 读写指针
    signal wr_ptr : unsigned(ADDR_BITS-1 downto 0) := (others => '0');
    signal rd_ptr : unsigned(ADDR_BITS-1 downto 0) := (others => '0');
    signal count_int : unsigned(ADDR_BITS downto 0) := (others => '0');
    
    -- 标志信号
    signal full_flag : std_logic := '0';
    signal empty_flag : std_logic := '1';
    signal afull_flag : std_logic := '0';
    signal aempty_flag : std_logic := '1';
    
begin

    -- 常量赋值
    WR_FULL <= full_flag;
    RD_EMPTY <= empty_flag;
    WR_AFULL <= afull_flag;
    RD_AEMPTY <= aempty_flag;
    COUNT <= std_logic_vector(count_int);
    
    -- FIFO满标志 (ADDR_BITS精确比较)
    full_flag <= '1' when count_int = DEPTH else '0';
    
    -- FIFO空标志
    empty_flag <= '1' when count_int = 0 else '0';
    
    -- Almost Full (距离满4个位置)
    afull_flag <= '1' when count_int >= DEPTH - 4 else '0';
    
    -- Almost Empty (距离空4个位置)
    aempty_flag <= '1' when count_int <= 4 else '0';
    
    -- 写操作
    process(CLK, RST)
    begin
        if RST = '1' then
            wr_ptr <= (others => '0');
        elsif rising_edge(CLK) then
            if WR_EN = '1' and full_flag = '0' then
                mem(to_integer(wr_ptr)) <= WR_DATA;
                if wr_ptr = DEPTH-1 then
                    wr_ptr <= (others => '0');
                else
                    wr_ptr <= wr_ptr + 1;
                end if;
            end if;
        end if;
    end process;
    
    -- 读操作
    process(CLK, RST)
    begin
        if RST = '1' then
            rd_ptr <= (others => '0');
            RD_DATA <= (others => '0');
        elsif rising_edge(CLK) then
            if RD_EN = '1' and empty_flag = '0' then
                RD_DATA <= mem(to_integer(rd_ptr));
                if rd_ptr = DEPTH-1 then
                    rd_ptr <= (others => '0');
                else
                    rd_ptr <= rd_ptr + 1;
                end if;
            end if;
        end if;
    end process;
    
    -- 计数器更新
    process(CLK, RST)
    begin
        if RST = '1' then
            count_int <= (others => '0');
        elsif rising_edge(CLK) then
            if WR_EN = '1' and RD_EN = '0' then
                if full_flag = '0' then
                    count_int <= count_int + 1;
                end if;
            elsif WR_EN = '0' and RD_EN = '1' then
                if empty_flag = '0' then
                    count_int <= count_int - 1;
                end if;
            end if;
        end if;
    end process;

end architecture RTL;