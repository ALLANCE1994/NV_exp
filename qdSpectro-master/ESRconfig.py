# ESR配置.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予许可，无论是否收费，任何获得本软件及相关文档
# 文件（以下简称"软件"）副本的人，有权在不受限制的情况下处理该软件，
# 包括但不限于使用、复制、修改、合并、发布、分发、再许可和/或出售软件副本，
# 以及允许向其提供软件的人这样做，但须遵守以下条件：

# 上述版权声明和本许可通知应包含在软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不提供任何形式的担保，无论是明示的还是暗示的，
# 包括但不限于适销性、特定用途适用性和非侵权性的担保。在任何情况下，
# 作者或版权持有人均不对任何索赔、损害或其他责任负责，无论是在合同行为、
# 侵权行为或其他情况下，由软件或软件的使用或其他交易引起、产生或与之相关的。

"""
电子自旋共振（ESR）实验配置

本脚本可用于配置mainControl.py以运行电子自旋共振（ESR）实验。实验会记录氮空位（NV）金刚石样品发出的荧光信号，该信号随微波驱动信号的频率变化而变化，最终数据将以制表符分隔的文本文件形式保存（保存选项详见下文）。微波频率从起始频率startFreq扫描至终止频率endFreq，共分为N_scanPts个扫描点。在每个频率点，脚本会采集2*Nsamples次荧光读数，依次交替开启和关闭微波，以此确定背景荧光水平。因此，可得到Nsamples次微波开启时的信号计数，以及Nsamples次微波关闭时的背景（参考）计数。首次完成全频率扫描后，脚本将重复扫描Navg次，并对所有扫描周期中每个频率点的对比度进行平均计算（对比度定义及平均选项详见下文）。

——对比度设置——
脚本将根据contrastMode变量设定的两种计算公式之一，利用信号计数与背景计数计算对比度。若contrastMode设为'ratio_SignalOverReference'，对比度定义为信号与背景的比值；若设为'ratio_DifferenceOverSum'，对比度则定义为信号与背景的差值同二者之和的比值。用户也可选择'signalOnly'对比度模式，该模式下仅绘制信号计数曲线，忽略背景计数。

——平均计算选项——
默认情况下，针对每个频率点，脚本会基于该频率点下Nsamples次信号读数的平均值与Nsamples次背景读数的平均值计算对比度。例如，若contrastMode设为ratio_SignalOverReference，默认计算方式为信号平均值除以背景平均值。若希望先逐次计算信号与背景样本的对比度，再对所有样本结果取平均，可将shotByShotNormalization设为True。例如，当contrastMode为ratio_SignalOverReference且shotByShotNormalization为True时，对比度将通过每次信号样本与对应后续背景样本的比值计算，再对所有比值取平均。

脚本首次对信号发生器的微波驱动频率进行扫描时，会按照频率从小到大的顺序执行。若Navg>1，脚本将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，后续所有扫描的频率点顺序均会随机打乱。若需关闭随机化功能，可将下方的randomize选项设为False。

——绘图选项——
将livePlotUpdate设为True，可在数据采集过程中实时绘制数据曲线。需注意，首次扫描完成后，绘图仅在每次后续扫描结束时更新。若livePlotUpdate设为False，则仅在实验全部结束后绘制数据曲线。

将plotPulseSequence设为True，可绘制已编程至PulseBlaster设备中的脉冲序列。需注意，程序会等待用户关闭该绘图窗口后再继续运行。

——保存选项——
用户可自主选择数据保存的频率。首次扫描时，可设置按saveSpacing_inScanPts个频率点为间隔保存数据（例如该变量设为2时，脚本会每隔一个频率点重新保存一次数据）。后续扫描时，脚本将在每次频率扫描结束后，按saveSpacing_inAverages次平均周期为间隔重新保存数据（例如该值设为3时，每完成3次平均扫描后保存一次数据）。无论上述选项如何设置，数据均会在首次频率扫描结束及实验全部结束（即最后一次平均扫描完成）时自动保存。

运行本脚本的步骤：
1）编辑connectionConfig.py，定义实验装置中PulseBlaster、斯坦福研究系统（SRS）设备及数据采集卡（DAQ）的通道连接配置。
2）编辑下文的用户输入参数区域。
3）运行脚本。在Windows命令提示符中，可通过输入python mainControl.py ESRconfig命令运行该脚本。

用户输入参数：
*startFreq：扫描范围内的最低频率，单位为赫兹（Hz）。
*endFreq：扫描范围内的最高频率，单位为赫兹（Hz）。
*N_scanPts：扫描中的频率点数量。
*microwavePower：SRS信号发生器的输出功率，单位为分贝毫瓦（dBm）。注意：该功率不得超过与SRS输出端相连的任意放大器的输入功率上限。
*t_duration：单次ESR脉冲序列迭代中信号采集半周期的持续时间。
*Nsamples：每个频率点下需采集的荧光测量样本数。
*Navg：平均运行次数（即频率扫描的重复次数）。
*plotPulseSequence：设为True时，本脚本将生成PulseBlaster输出的脉冲序列绘图。
*DAQtimeout：数据采集卡等待所需数量样本就绪（即完成采集）的时长，单位为秒（s）。
*contrastMode：根据所需对比度模式，设为'ratio_SignalOverReference'、'ratio_DifferenceOverSum'或'signalOnly'其中之一（详见上文“对比度设置”说明）。
*livePlotUpdate：设为True可在数据采集时实时更新绘图（详见上文“绘图选项”）。
*plotPulseSequence：设为True可在实验开始时绘制脉冲序列（详见上文“绘图选项”）。
*plotXaxisUnits：设置数据图的横轴单位，可选择Hz、kHz、MHz或GHz。
*xAxisLabel：设置数据图的横轴标签。
*saveSpacing_inScanPts：首次扫描期间保存数据的频率点间隔数。
*saveSpacing_inAverages：首次完整扫描后，保存数据的平均运行次数间隔。
*savePath：数据保存文件夹路径。默认情况下，数据保存在本脚本所在目录下名为Saved_Data的文件夹中。
*saveFileName：数据保存文件名。脚本运行时的日期和时间将自动追加至该文件名后。
*shotByShotNormalization：设为True可开启逐次采样对比度归一化（详见上文“平均计算选项”）。
*randomize：设为True可对首次扫描之后所有扫描的频率点顺序进行随机打乱。
"""
# 导入模块
from spinapi import ns,us,ms
from SRScontrol import Hz, kHz, MHz, GHz
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 计算得出：
t_min = 1e3/PBclk #单位为 ns

#------------------------- 用户输入 ---------------------------------------#

# 微波扫描参数:----------------------------------------------------
# 起始频率 (单位为Hz):
startFreq = 2.84e9
# 结束频率 (单位为Hz):
endFreq = 2.90e9
# 频率步进数:
N_scanPts = 121
# SRS 输出的微波功率 (dBm) - 不要超过您放大器的最大输入功率:
# 注意：此参数仅适用于 SRS 信号发生器
microwavePower = 30
# B210 设备的增益设置（dB）- 范围通常为 0-70 dB，过高的增益可能导致信号失真
# 建议增益值：50-65 dB
B210_gain = 70 
# 脉冲序列参数:----------------------------------------------------
# ESR 脉冲序列单次迭代中信号采集半周期的持续时间:
# 每个完整的ESR采集周期包括两个半周期：
# 1. 微波开启时的信号采集（持续t_duration）
# 2. 微波关闭时的背景采集（持续t_duration）
# 通过比较这两个半周期的采集结果，可以计算出真正的信号强度，去除背景噪声的影响
# 注意：t_duration值需要根据具体实验条件（如NV色心荧光强度、DAQ采样率等）进行优化
# 过长的t_duration会增加实验时间，过短则可能导致信号信噪比不足；
# 对于 ESR 实验，典型值为 50-200 微秒
# 具体值需要根据 NV 色强度和实验要求强度和实验要求进行调整
t_duration = 20*us
# 每个频率点采集的荧光测量样本数:
Nsamples = 1
# 平均运行次数:
Navg = 1
#DAQ 超时，单位为秒:
DAQtimeout = 10
# 对比度模式 - 可选值：'ratio_SignalOverReference'、'ratio_DifferenceOverSum'或'signalOnly'
contrastMode ='signalOnly'
# contrastMode ='ratio_SignalOverReference'
# contrastMode ='ratio_DifferenceOverSum'
# 绘图选项--------------------------------------------------------------
# 实时绘图更新选项
livePlotUpdate = True
# 绘制脉冲序列选项 - 设置为 true 可绘制脉冲序列
plotPulseSequence = True
# 绘制 x 轴单位 (Hz, kHz, MHz 或 GHz)
plotXaxisUnits = MHz
# 绘制 x 轴标签
xAxisLabel = 'Frequency (MHz)'
# 保存选项------------------------------------------------------------------
# 首次扫描所有频率点时的保存间隔:
saveSpacing_inScanPts = 2
# 平均运行中的保存间隔:
saveSpacing_inAverages = 1
# 数据保存文件夹路径:
savePath = os.getcwd()+"\\Saved_Data\\"
# 数据文件名称
saveFileName = "ESR_"
# 差分数据保存选项 - 设为 True 保存差分数据:
saveDifferentialData = True
# 图片保存选项 - 设为 True 保存实验图片:
savePlots = True
# 平均选项:------------------------------------------------------------
# 逐次采样对比度归一化选项:
shotByShotNormalization = False
# 随机化扫描点顺序的选项
randomize = False
#------------------------- 用户输入结束 ----------------------------------#

scannedParam = np.linspace(startFreq,endFreq, N_scanPts, endpoint=True)
# 序列字符串:
sequence = 'ESRseq'
# 扫描起始名称
scanStartName = 'startFreq'
# 扫描结束名称
scanEndName = 'endFreq'
# PB 通道
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig}
# 序列参数
sequenceArgs = [t_duration]
# 创建保存文件路径
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
# 创建参数文件路径
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
# 参数文件保存设置
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList =  ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startFreq:',scannedParam[0],'endFreq:',scannedParam[-1],'microwavePower:',microwavePower,'t_duration:',t_duration,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_duration]
	return sequenceArgs
	

def updateExpParamList():
	# 每次更新参数列表时生成新的时间戳
	dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
	# 更新文件名
	dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
	paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
	# 更新参数列表
	expParamList =  ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startFreq:',scannedParam[0],'endFreq:',scannedParam[-1],'microwavePower:',microwavePower,'B210_gain:',B210_gain,'t_duration:',t_duration,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList, dataFileName, paramFileName