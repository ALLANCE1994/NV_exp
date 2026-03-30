# 连接配置.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
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

# DAQ 连接配置-------------------------------------------------------
# 请在下面输入用于数据采集的 National Instruments DAQ 通道，如下所示：
# DAQ_APDInput 是您连接光电探测器信号的 DAQ 的模拟输入通道。这里假设是参考单端（RSE）连接。如果用户希望使用差分连接，应相应修改下面的配置和 DAQcontrol.py 库中的配置（例如，如果使用 NI USB-6211 DAQ 卡，请参考 2009 年 4 月版本的 NI USB-621x 手册第 4 章，了解模拟输入连接选项）
# DAQ_SampleClk 是 DAQ 的外设功能接口（PFI）端子，您已将 PB_DAQ PulseBlaster 通道的输出连接到该端子（即生成 TTL 脉冲的 PulseBlaster 通道，作为采样时钟来定时数据采集）
# DAQ_StartTrig 是 DAQ 的外设功能接口（PFI）端子，您已将 PB_STARTtrig PulseBlaster 通道的输出连接到该端子（即生成 TTL 脉冲的 PulseBlaster 通道，在每个实验扫描点触发数据采集的开始）

# 原始NI DAQ配置
# DAQ_APDInput = "Dev2/ai1"
# DAQ_SampleClk = "PFI0"
# DAQ_StartTrig = "PFI5"
# DAQ_MaxSamplingRate = 250000

# DAQ 连接配置-------------------------------------------------------
# 请在下面输入用于数据采集的 National Instruments DAQ 通道，如下所示：
# DAQ_APDInput 是您连接光电探测器信号的 DAQ 的模拟输入通道。这里假设是差分连接（myDAQ 推荐）。
# DAQ_SampleClk 是 DAQ 的外设功能接口（PFI）端子，您已将 PB_DAQ PulseBlaster 通道的输出连接到该端子（即生成 TTL 脉冲的 PulseBlaster 通道，作为采样时钟来定时数据采集）
# DAQ_StartTrig 是 DAQ 的外设功能接口（PFI）端子，您已将 PB_STARTtrig PulseBlaster 通道的输出连接到该端子（即生成 TTL 脉冲的 PulseBlaster 通道，在每个实验扫描点触发数据采集的开始）

DAQ_APDInput = "myDAQ1/ai0"
DAQ_SampleClk = "PFI0"       #PB_DAQ (通道 3)	DIO 0	采样时钟
DAQ_StartTrig = "PFI1"       #PB_STARTtrig (通道 2)	DIO 1	触发脉冲

# 请在下面输入您的 National Instruments DAQ 的最大采样率（单位为样本/通道/秒）：
DAQ_MaxSamplingRate = 200000
# 请在下面设置最小电压和最大电压（单位为伏特），以匹配您的 DAQ 支持的 AI（模拟输入）电压范围，并适应您的光电探测器输出的电压范围（myDAQ 支持 ±10V）。
minVoltage=-10
maxVoltage=10

# SRS 连接配置-------------------------------------------------------
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