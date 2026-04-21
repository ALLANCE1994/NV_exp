# correlSpec配置.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明和本许可声明应包含在软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不附带任何形式的保证，
# 无论是明示的还是默示的，包括但不限于适销性、
# 特定用途的适用性和不侵权的保证。在任何情况下，
# 作者或版权持有人均不对任何索赔、损害或其他责任负责，
# 无论是在合同行为、侵权行为或其他情况下，
# 因软件或软件的使用或其他交易而产生或与之相关的。

"""
# 相关光谱实验配置
本脚本可用于配置mainControl.py以运行相关光谱实验。氮空位金刚石样品发射的荧光信号，将根据相关光谱脉冲序列中XY8序列之间扫描延迟时长进行记录（详见实验方案），数据将保存为制表符分隔的文本文件（保存选项详见下文）。延迟时长从start_tcorr扫描至end_tcorr，共分为N_scanPts个扫描步长。在每个扫描点，脚本将采集2*Nsamples次荧光读数，通过在连续采样中对脉冲序列最后一个π/2脉冲进行180°相移，获取两组荧光计数读数R1和R2，并据此计算对比度（详见下文"对比度设置"部分说明）。因此，第一组读数与第二组读数各包含Nsamples次采样。首次扫描完成后，脚本将重复扫描Navg次，并对所有运行结果中各扫描点的对比度取平均值（对比度定义与平均选项详见下文）。

## 对比度设置
实验的对比度模式应设置为`ratio_DifferenceOverSum`。该模式下，对比度C通过两组读数R1与R2的差值和之和的比值计算得出，即C=(R1−R2)/(R1+R2)。出于调试需求，用户也可选择另外两种对比度模式：`signalOnly`（仅绘制R1数据）或`ratio_SignalOverReference`（绘制R1/R2比值）。

## 平均选项
默认情况下，脚本在每个扫描点根据平均后的R1计数（对该扫描点下Nsamples次R1读数取平均）与平均后的R2计数计算对比度。若希望先逐次计算R1与R2采样对应的对比度C，再对所有采样的对比度取平均，可将逐次归一化（shotByShotNormalization）选项设为True。例如，当对比度模式设为`ratio_DifferenceOverSum`且逐次归一化设为True时，将对每一组R1、R2采样计算(R1−R2)/(R1+R2)比值，再对所有比值取平均。

脚本首次扫描延迟时，将按照延迟从短到长的顺序进行。若Navg＞1，脚本将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，后续所有扫描的扫描点顺序均随机打乱。若需关闭随机打乱功能，可将下方随机化（randomize）选项设为False。

## 绘图选项
将实时绘图更新（livePlotUpdate）设为True，可在数据采集过程中同步绘制图像。需注意，首次扫描完成后，图像仅在每次后续扫描结束时更新。若该选项设为False，数据将仅在实验全部结束后绘制。

将绘制脉冲序列（plotPulseSequence）设为True，可绘制已编程至脉冲发生器（PulseBlaster）中的脉冲序列。程序将等待用户关闭该绘图窗口后再继续运行。

## 保存选项
用户可自主设置数据保存频率。首次扫描时，可设置按saveSpacing_inScanPts个扫描点间隔保存数据（例如该参数设为2时，脚本将每隔一个扫描点重新保存一次数据）。后续扫描中，脚本将在每间隔saveSpacing_inAverages次平均运行的扫描结束后重新保存数据（例如该参数设为3时，每完成3次平均扫描后保存一次数据）。无论上述参数如何设置，数据均会在首次扫描结束与实验全部结束（即最后一次平均运行完成）时自动保存。

## IQ补偿延时
为补偿线缆与仪器带来的延时，需在控制SRS信号发生器I/Q调制开启与关闭的脉冲沿，和控制微波开启与关闭的脉冲沿之间添加IQpadding延时，确保I/Q调制在微波脉冲整个持续期间保持开启。该延时参数仅可在示波器严密监测脉冲序列的前提下进行修改。若用户需调整该参数，可在下文用户输入区域的"高级用户选项"中找到对应设置。

## 脚本运行步骤
1. 编辑connectionConfig.py，定义实验装置中脉冲发生器（PulseBlaster）、SRS信号发生器与数据采集卡（DAQ）的通道连接配置。
2. 编辑下文用户输入区域的参数。
3. 运行脚本。在Windows命令提示符中，可通过输入`python mainControl.py correlSpecconfig`执行该脚本。

## 用户输入参数说明
注：t_min为脉冲发生器（PulseBlaster）板卡的时间分辨率，即t_min=1/时钟频率。例如，500MHz板卡对应的t_min=2ns。
- start_tcorr：扫描最短延迟时长，单位为纳秒（ns）。需注意，系统会在start_tcorr（及扫描中所有延迟时长）基础上额外增加2微秒延时（按t_min的整数倍取整），因此XY8序列间的最小间隔为start_tcorr + t_min×round(2μs/t_min)。
- end_tcorr：扫描最长延迟时长，单位为纳秒（ns）。扫描中所有延迟时长均会额外增加2微秒延时（按t_min的整数倍取整），因此XY8序列间的最大间隔为end_tcorr + t_min×round(2μs/t_min)。
- N_scanPts：扫描总点数。
- microwavePower：SRS信号发生器输出功率，单位为分贝毫瓦（dBm）。**注意**：该值不得超过与SRS输出端相连的任意放大器的输入功率上限。
- B210_gain：B210设备的增益设置（dB）- 范围通常为0-70 dB，过高的增益可能导致信号失真。建议增益值：50-65 dB。
- microwaveFrequency：SRS信号发生器输出微波频率，单位为赫兹（Hz）。
- t_AOM：声光调制器（AOM）脉冲持续时长，单位为纳秒（ns）。
- t_readoutDelay：声光调制器脉冲起始至数据采集卡采样脉冲的延时，单位为纳秒（ns）。最优延时可通过optimReadoutDelay.py脚本获取（详见实验方案论文第54步）。
- t_pi：π脉冲持续时长，单位为纳秒（ns）。
- N：XY8脉冲序列中8个π脉冲模块的重复次数。
- tau0：XY8脉冲序列中π脉冲之间的延时，单位为纳秒（ns）。
- Nsamples：每个扫描点的荧光测量采样次数。
- Navg：平均运行次数（即延迟扫描的重复次数）。
- DAQtimeout：数据采集卡等待目标采样数就绪（即完成采集）的最长时长，单位为秒（s）。
- contrastMode：本实验中该参数需设为`ratio_DifferenceOverSum`，其余可选模式为`ratio_SignalOverReference`与`signalOnly`（详见"对比度设置"说明）。
- livePlotUpdate：设为True可在数据采集时同步更新绘图（详见"绘图选项"说明）。
- plotPulseSequence：设为True可在实验起始时绘制脉冲序列（详见"绘图选项"说明）。
- plotXaxisUnits：设置数据图横轴单位，可选纳秒（ns）、微秒（us）、毫秒（ms）。
- xAxisLabel：设置数据图横轴标签。
- saveSpacing_inScanPts：首次扫描时数据保存的扫描点间隔数。
- saveSpacing_inAverages：首次完整扫描后，数据保存的平均运行次数间隔。
- savePath：数据保存文件夹路径。默认情况下，数据将保存在脚本所在目录下名为Saved_Data的文件夹中。
- saveFileName：数据保存文件名。文件名后续将自动附加脚本运行的日期与时间。
- shotByShotNormalization：设为True可开启逐次采样对比度归一化（详见"平均选项"说明）。
- randomize：设为True可打乱首次扫描后所有扫描的扫描点顺序。
- IQpadding：IQ调制开关脉冲沿与微波开关脉冲沿之间的延时，单位为纳秒（ns）。
"""
#导入模块
from spinapi import ns,us,ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 给出：
t_min = 1e3/PBclk # 单位为 ns
#------------------------- 用户输入 ---------------------------------------#

# 扫描参数:-------------------------------------------------------------
# 起始脉冲持续时间（单位为纳秒）。注意：系统会在 start_tcorr（以及扫描中的所有延迟）基础上
# 额外增加 2μs 的延迟（按 t_min 的整数倍取整）。因此，XY8 序列之间的最小间隔为
# start_tcorr + t_min*round(2*us/t_min)。
start_tcorr = 0
# 结束脉冲持续时间（单位为纳秒）。注意：系统会在扫描中的所有延迟基础上
# 额外增加 2μs 的延迟（按 t_min 的整数倍取整）。因此，XY8 序列之间的最大间隔为
# end_tcorr + t_min*round(2*us/t_min)。
end_tcorr = 40000
# 延迟步数：
N_scanPts = 201
# SRS 输出微波功率（dBm）- 请勿超过放大器的最大输入功率：
microwavePower = -5
# B210 设备的增益设置（dB）- 范围通常为 0-70 dB，过高的增益可能导致信号失真
# 注意：B210 使用增益（dB）而不是功率（dBm）
# 建议增益值：50-65 dB
B210_gain = 70
# 微波频率（Hz）：
microwaveFrequency = 2e9
# 脉冲序列参数:----------------------------------------------------
# AOM 脉冲持续时间（单位为 ns）
t_AOM= 5*us
# 读出延迟（单位为 ns）
t_readoutDelay = 2.3*us
# π 脉冲持续时间（单位为 ns）
t_pi = 24
# XY8 脉冲序列中 8 个 π 脉冲模块的重复次数：
N =1
# XY8 脉冲序列中 π 脉冲之间的延迟（单位为 ns）：
tau0=1500
# 每个延迟点的荧光测量采样次数：
Nsamples = 10000
# 要进行的平均运行次数：
Navg = 4
# DAQ 超时，单位为秒：
DAQtimeout = 10
# 绘图选项--------------------------------------------------------------
# 对比度模式
contrastMode ='ratio_DifferenceOverSum'
# 实时绘图更新选项
livePlotUpdate = True
# 绘制脉冲序列选项 - 设置为 true 可绘制脉冲序列
plotPulseSequence = True
# 绘图 x 轴单位乘数（ns、us 或 ms）
plotXaxisUnits = ns
# 绘图 x 轴标签
xAxisLabel = 'delay (ns)'
# 保存选项------------------------------------------------------------------
# 首次扫描所有延迟点时的数据保存间隔：
saveSpacing_inScanPts = 100
# 平均运行中的保存间隔：
saveSpacing_inAverages = 3
# 数据保存文件夹路径：
savePath = os.getcwd()+"\\Saved_Data\\"
# 数据文件文件名
saveFileName = "correlationSpec_"
# 平均选项:------------------------------------------------------------
# 逐次采样对比度归一化选项：
shotByShotNormalization = False
# 随机化扫描点顺序选项
randomize = True
# 高级用户选项--------------------------------------------------------------
# IQ 补偿延时，单位为 ns（应保持为 t_min*round(30*ns/t_min)，除非用户
# 需要特别短的自由进动延迟 - 此参数仅应在示波器严密监测脉冲序列的情况下修改。
IQpadding = t_min*round(30*ns/t_min)
#------------------------- END OF USER 输入 ----------------------------------#

scannedParam = np.linspace(start_tcorr,end_tcorr, N_scanPts, endpoint=True)
# 序列字符串:
sequence = 'correlSpecSeq'
# 扫描起始名称
scanStartName = 'start_tcorr'
# 扫描结束名称
scanEndName = 'end_tcorr'
# PB 通道
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig,'I':I,'Q':Q}
# 序列参数
sequenceArgs = [tau0,t_AOM,t_readoutDelay,t_pi,IQpadding,N]
# 创建保存文件路径
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
# 创建参数文件路径
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
# 参数文件保存设置
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'start_tcorr:',scannedParam[0],'end_tcorr:',scannedParam[-1],'microwavePower:',microwavePower,'B210_gain:',B210_gain,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'N',N,'IQpadding',IQpadding,'tau0',tau0,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	"""更新序列参数"""
	sequenceArgs = [tau0,t_AOM,t_readoutDelay,t_pi,IQpadding,N]
	return sequenceArgs


def updateExpParamList():
	"""更新实验参数列表"""
	expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'start_tcorr:',scannedParam[0],'end_tcorr:',scannedParam[-1],'microwavePower:',microwavePower,'B210_gain:',B210_gain,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'N',N,'IQpadding',IQpadding,'tau0',tau0,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList, dataFileName, paramFileName