# ESR配置.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予许可, free of charge, to any person 
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:

# 上述版权声明 and this permission notice shall be
# included in all copies or substantial portions of the Software.

# 本软件按"原样"提供 "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
#导入模块
from spinapi import ns,us,ms
from SRScontrol import Hz, kHz, MHz, GHz
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min, 时间分辨率 of the PulseBlaster, given by 1/(时钟频率):
t_min = 1e3/PBclk #in ns

#-------------------------  USER 输入  ---------------------------------------#

# 微波 扫描 参数s:----------------------------------------------------
# 启动 频率 (单位为Hz):
startFreq = 2.7e9
# End 频率 (单位为Hz):
endFreq = 3.0e9
# 数量 频率 steps:
N_scanPts = 101
# 微波 功率 输出 from SRS(dBm) - DO NOT EXCEED YOUR AMPLIFIER'S MAXIMUM 输入 功率:
microwavePower = -5 
# Pulse 序列 参数s:----------------------------------------------------
# 持续时间 of the 信号-aquisition half of one iteration of ESR 脉冲序列:
t_duration = 80*us
# 数量 fluorescence measurement 样本 to take at each 频率 点:
Nsamples = 1000
# 数量 averaging 运行s to do:
Navg = 1
#DAQ 超时, 单位为秒:
DAQtimeout = 10
# 对比度 mode
contrastMode ='ratio_SignalOverReference'
# 绘图 options--------------------------------------------------------------
# Live 绘图 update option
livePlotUpdate = True
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = True
# 绘制 x axis units (Hz, kHz, MHz or GHz)
plotXaxisUnits = Hz
# 绘制 x axis label
xAxisLabel = 'Frequency (Hz)'
# 保存 options------------------------------------------------------------------
# 保存 interval for first 扫描 through all 频率 点s:
saveSpacing_inScanPts = 2
# 保存 interval in averaging 运行s:
saveSpacing_inAverages = 1
# Path to folder where 数据 will be 保存d:
savePath = os.getcwd()+"\\Saved_Data\\"
# File name for 数据 file
saveFileName = "ESR_"
# Averaging options:------------------------------------------------------------
# Option to do shot by shot 对比度 normalization:
shotByShotNormalization = False
# Option to randomize order of 扫描 点s
randomize = True
#------------------------- END OF USER 输入 ----------------------------------#

scannedParam = np.linspace(startFreq,endFreq, N_scanPts, endpoint=True)
#序列字符串:
sequence = 'ESRseq'
#扫描 start Name
scanStartName = 'startFreq'
#扫描 end Name
scanEndName = 'endFreq'
#PB 通道s
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig}
#序列 args
sequenceArgs = [t_duration]
#Make 保存 file path
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
#Make param file path
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
#Param file 保存 settings
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList =  ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startFreq:',scannedParam[0],'endFreq:',scannedParam[-1],'microwavePower:',microwavePower,'t_duration:',t_duration,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_duration]
	return sequenceArgs
	
def updateExpParamList():
	expParamList =  ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startFreq:',scannedParam[0],'endFreq:',scannedParam[-1],'microwavePower:',microwavePower,'t_duration:',t_duration,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList