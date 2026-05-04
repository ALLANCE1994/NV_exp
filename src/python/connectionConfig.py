# 连接配置.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明和本许可声明应包含在本软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不提供任何形式的担保，明示或暗示，
# 包括但不限于适销性、特定用途适用性和非侵权性的担保。
# 在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责，
# 无论是在合同诉讼、侵权行为还是其他方面，由本软件或本软件的使用或
# 其他交易引起的或与之相关的。

#-------------------------  用户输入  ---------------------------------------#
# PulseBlaster 时钟频率（单位为MHz）：
PBclk = 500

# PulseBlaster 连接配置 ----------------------------------------------
# 请在下面输入您连接仪器的 PulseBlaster 通道的位号，按照下面的定义。例如：如果您使用 SP18A ESR-PRO Pulseblaster 板，并选择位 2（对应 PulseBlaster 板上的 BNC2 连接器，如 PulseBlasterESR-PRO 手册 2017 年 9 月版本的图 10 所示）来输出开始触发脉冲，您应该输入 PB_STARTtrig = 2。

#  PB_I 是连接到 SRS 微波信号发生器的 I（或"同相"）输入的 PulseBlaster 通道的位号。
#  PB_Q 是连接到 SRS 微波信号发生器的 Q（或"正交"）输入的 PulseBlaster 通道的位号。
#  PB_STARTtrig 是用于生成脉冲的 PulseBlaster 通道的位号，这些脉冲被馈送到数据采集卡（DAQ）以在每个实验扫描点触发数据采集的开始。
#  PB_DAQ 是用于生成脉冲的 PulseBlaster 通道的位号，这些脉冲被馈送到 DAQ 以作为采样时钟来定时数据采集。
#  PB_AOM 是连接到用于打开和关闭声光调制器（AOM）的射频驱动的开关的 TTL 输入的 PulseBlaster 通道的位号。
#  PB_MW 是连接到用于打开和关闭 SRS 微波信号发生器生成的微波的开关的 TTL 输入的 PulseBlaster 通道的位号。

PB_I = 0
PB_Q = 1
PB_STARTtrig = 2
PB_DAQ = 3
PB_AOM = 4
PB_MW = 5

# DAQ 设备选择 -------------------------------------------------------
# 选择您的 DAQ 设备类型:
#   0 = myDAQ (200kS/s, 适用于简单实验)
#   1 = NI USB-7855R (FPGA采集卡, 适用于高精度同步实验)
#   2 = NI USB-6363 (高速DAQ, 适用于高速采集)
DAQ_DEVICE_TYPE = 1

# FPGA 参数配置（仅适用于 USB-7855R）----------------------------------
# FPGA 主时钟频率（Hz）
FPGA_CLK_FREQ = 40e6

# 终端配置枚举（替代nidaqmx的TerminalConfiguration）
class TerminalConfiguration:
    DIFF = 1  # 差分输入
    NRSE = 2  # 非参考单端
    RSE = 3   # 参考单端
    PSEUDO_DIFF = 4  # 伪差分

# 根据设备类型配置参数
if DAQ_DEVICE_TYPE == 0:
    # myDAQ 配置
    DAQ_APDInput = "myDAQ1/ai0"
    DAQ_SampleClk = "PFI0"
    DAQ_StartTrig = "PFI1"
    DAQ_MaxSamplingRate = 200000
    minVoltage = -10
    maxVoltage = 10
    DAQ_TerminalConfig = TerminalConfiguration.DIFF

elif DAQ_DEVICE_TYPE == 1:
    # NI USB-7855R 配置
    # 设备名称从 NI MAX 确认: RIO0
    DAQ_APDInput = "RIO0/ai0"
    DAQ_SampleClk = "PFI0"
    DAQ_StartTrig = "PFI1"
    DAQ_MaxSamplingRate = 1000000
    minVoltage = -5
    maxVoltage = 5
    DAQ_TerminalConfig = TerminalConfiguration.DIFF

elif DAQ_DEVICE_TYPE == 2:
    # NI USB-6363 配置
    DAQ_APDInput = "Dev2/ai0"
    DAQ_SampleClk = "PFI0"
    DAQ_StartTrig = "PFI1"
    DAQ_MaxSamplingRate = 2000000
    minVoltage = -10
    maxVoltage = 10
    DAQ_TerminalConfig = TerminalConfiguration.DIFF
else:
    raise ValueError("无效的 DAQ_DEVICE_TYPE，请选择 0 (myDAQ), 1 (USB-7855R) 或 2 (USB-6363)")

# SRS 连接配置 -------------------------------------------------------
# 请在下面输入您的 SRS 的 GPIB 地址和型号名称。
GPIBaddr = 27
modelName='SG386'

#------------------------- 用户输入结束 ----------------------------------#

# 将 PulseBlaster 位号转换为 PulseBlaster 寄存器地址：
I = 2**PB_I
Q = 2**PB_Q
STARTtrig = 2**PB_STARTtrig
DAQ = 2**PB_DAQ
AOM = 2**PB_AOM
uW = 2**PB_MW

# FPGA 参数计算函数 ---------------------------------------------------
def calculateFPGAparams(t_readoutDelay, Nsamples):
    """计算 FPGA DAQ_Sync_Controller 需要的参数
    
    参数:
        t_readoutDelay: 读出延迟时间（秒或纳秒）
        Nsamples: 采样次数
        
    返回:
        DAQ_DELAY: 延迟时钟周期数
        DAQ_DURATION: 采集持续时间时钟周期数
    """
    # 转换延迟时间为秒
    if hasattr(t_readoutDelay, 'to'):
        delay_sec = t_readoutDelay.to('s').magnitude
    else:
        delay_sec = float(t_readoutDelay) * 1e-9  # 假设输入为纳秒
    
    # 计算延迟周期数
    DAQ_DELAY = int(delay_sec * FPGA_CLK_FREQ)
    
    # 计算采集持续周期数
    DAQ_DURATION = int(Nsamples * FPGA_CLK_FREQ / DAQ_MaxSamplingRate)
    
    return DAQ_DELAY, DAQ_DURATION

def calculateFPGASampleCount(Nsamples):
    """计算 FPGA 需要的采集点数参数（软件配置方式）
    
    参数:
        Nsamples: 每个扫描点的采样次数
        
    返回:
        SAMPLE_COUNT: FPGA 采集点数参数（32位整数）
    """
    # 计算每个采样点需要的 FPGA 时钟周期数
    cycles_per_sample = int(FPGA_CLK_FREQ / DAQ_MaxSamplingRate)
    # 计算总时钟周期数
    total_cycles = Nsamples * cycles_per_sample
    return total_cycles

# FPGA 寄存器地址映射（软件配置接口）
FPGA_REGISTERS = {
    'SAMPLE_COUNT': 0x100,  # 采集点数寄存器地址
    'CONTROL': 0x104,       # 控制寄存器地址
    'STATUS': 0x108         # 状态寄存器地址
}