# T1配置.py
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
# T1实验配置
本脚本可用于配置mainControl.py以运行T1实验。氮空位（NV）金刚石样品发射的荧光信号会随T1脉冲序列中扫描的延迟时间变化而被记录（详见实验方案），数据将以制表符分隔的文本文件形式保存（保存选项详见下文）。延迟时间从start_t到end_t按N_scanPts个步长进行扫描。在每个扫描点，脚本会采集2*Nsamples次荧光读数，并在交替采样中施加额外的微波π脉冲（以制备mₛ=-1态而非mₛ=0态），从而获得两组荧光计数读数R1和R2，后续将据此计算对比度（详见下文“对比度设置”部分说明）。因此，第一组读数R1和第二组读数R2各对应Nsamples次采样。首次扫描完成后，脚本会将扫描过程重复Navg次，并对所有运行结果中每个扫描点的对比度取平均值（对比度定义及平均选项详见下文）。

## 对比度设置
实验的对比度模式应设置为`ratio_DifferenceOverSum`。该模式下，对比度C通过两组读数R1和R2的差值与和值的比值计算得出，即C=(R1-R2)/(R1+R2)。出于调试目的，用户也可选择另外两种对比度模式：`signalOnly`（仅绘制R1数据）或`ratio_SignalOverReference`（绘制R1/R2比值）。

## 平均选项
默认情况下，脚本会针对每个扫描点，先对该点的Nsamples次R1读数和Nsamples次R2读数分别取平均值，再基于平均后的R1、R2计数计算对比度。若希望先逐次计算R1与R2采样的对比度C，再对所有采样的对比度取平均，可将`shotByShotNormalization`选项设为True。例如，当对比度模式为`ratio_DifferenceOverSum`且逐次归一化开启时，会先对每一组R1、R2采样计算(R1-R2)/(R1+R2)，再对所有比值取平均。

脚本首次扫描延迟时间时，会按延迟从短到长的顺序进行。若Navg>1，脚本将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，其余扫描的扫描点顺序均会随机打乱。若需关闭该随机化功能，可将下方的`randomize`选项设为False。

## 绘图选项
将`livePlotUpdate`设为True，可在数据采集过程中实时绘制图像。需注意，首次扫描完成后，图像仅会在后续每次扫描结束时更新。若该选项设为False，则仅在实验全部结束后绘制数据图像。

将`plotPulseSequence`设为True，可绘制已编程至PulseBlaster中的脉冲序列。需注意，程序会等待用户关闭该图像后才继续运行。

## 保存选项
用户可自主设置数据保存的频率。首次扫描时，可按`saveSpacing_inScanPts`设定的扫描点间隔保存数据（例如该变量设为2时，脚本会每隔一个扫描点重新保存一次数据）。后续扫描中，脚本会在每次扫描结束后，按`saveSpacing_inAverages`设定的平均运行次数间隔重新保存数据（例如该值设为3时，每完成3次平均运行后保存一次数据）。无论上述选项如何设置，数据均会在首次扫描结束及实验全部结束（即最后一次平均运行完成）时自动保存。

### 运行本脚本的步骤
1. 编辑connectionConfig.py，定义实验装置中PulseBlaster、斯坦福研究系统（SRS）信号源及数据采集卡（DAQ）的通道连接配置。
2. 编辑下文的用户输入参数区域。
3. 运行脚本。在Windows命令提示符中，可通过执行`python mainControl.py T1config`命令运行该脚本。

## 用户输入参数
> 注：t_min为PulseBlaster板卡的时间分辨率，即t_min=1/时钟频率。例如，500MHz的板卡对应的t_min=2纳秒。
- **start_t**：扫描的最短延迟时间，单位为纳秒。注意：若start_t<(t_readoutDelay + 2*t_min*round((1微秒)/t_min) + t_pi)，该值会自动偏移(t_readoutDelay + 2*t_min*round((1微秒)/t_min) + t_pi)，以避免脉冲重叠错误。
- **end_t**：扫描的最长延迟时间，单位为纳秒。
- **N_scanPts**：扫描的总点数。
- **microwavePower**：SRS信号源的输出功率，单位为分贝毫瓦（dBm）。注意：该值不得超过与SRS输出端相连的任意放大器的输入功率上限。
- **microwaveFrequency**：SRS信号源输出的微波频率，单位为赫兹（Hz）。
- **t_AOM**：声光调制器（AOM）脉冲持续时间，单位为纳秒。
- **t_readoutDelay**：AOM脉冲起始至DAQ采集读数的延迟时间，单位为纳秒。
- **t_pi**：π脉冲持续时间，单位为纳秒。
- **Nsamples**：每个扫描点的荧光测量采样次数。
- **Navg**：平均运行次数（即延迟扫描的重复次数）。
- **DAQtimeout**：DAQ等待目标数量采样数据就绪（即完成采集）的最长时间，单位为秒。
- **contrastMode**：本实验中该参数需设为`ratio_DifferenceOverSum`，其余可选模式为`ratio_SignalOverReference`和`signalOnly`（详见上文“对比度设置”说明）。
- **livePlotUpdate**：设为True可在数据采集时实时更新图像（详见上文“绘图选项”）。
- **plotPulseSequence**：设为True可在实验开始时绘制脉冲序列（详见上文“绘图选项”）。
- **plotXaxisUnits**：设置数据图像的横轴单位，可选纳秒（ns）、微秒（us）、毫秒（ms）。
- **xAxisLabel**：设置数据图像的横轴标签。
- **saveSpacing_inScanPts**：首次扫描过程中，数据保存的频率点数间隔。
- **saveSpacing_inAverages**：首次完整扫描后，数据保存的平均运行次数间隔。
- **savePath**：数据保存文件夹路径。默认情况下，数据保存在脚本所在目录下名为Saved_Data的文件夹中。
- **saveFileName**：数据保存文件名。该文件名后会自动附加脚本运行的日期和时间。
- **shotByShotNormalization**：设为True可开启逐次采样对比度归一化（详见上文“平均选项”）。
- **randomize**：设为True可打乱首次扫描后所有扫描的频率点顺序。
"""
#导入模块
from spinapi import ns,us,ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min, 时间分辨率 of the PulseBlaster, given by 1/(时钟频率):
t_min = 1e3/PBclk #in ns

#-------------------------  USER 输入  ---------------------------------------#
# 微波 扫描 参数s:----------------------------------------------------
# 启动 pulse 持续时间 (单位为纳秒). 注意： if 
# 启动_t<(t_readout延迟 + 2*t_min*round((1*us)/t_min) + t_pi), it will be shifted by
#(t_readout延迟 + 2*t_min*round((1*us)/t_min) + t_pi) to avoid pulse overlap 错误s:
start_t = 4.5e3
# End pulse 持续时间 (单位为纳秒):
end_t = 5e5
# 数量 延迟 steps:
N_scanPts = 100
# 微波 功率 输出 from SRS(dBm) - DO NOT EXCEED YOUR AMPLIFIER'S MAXIMUM 输入 功率:
microwavePower = -5
# 微波 频率 (Hz):
microwaveFrequency = 3e9
# Pulse 序列 参数s:----------------------------------------------------
# AOM pulse 持续时间 (单位为ns)
t_AOM= 5*us
# 读取out 延迟 (单位为ns)
t_readoutDelay = 2.3*us
# Pi-pulse 持续时间 (单位为ns)
t_pi = 24
# 数量 fluorescence measurement 样本 to take at each 延迟 点:
Nsamples = 1000
# 数量 averaging 运行s to do:
Navg = 1
#DAQ 超时, 单位为秒:
DAQtimeout = 120
# 绘图 options--------------------------------------------------------------
# 对比度 mode
contrastMode ='ratio_DifferenceOverSum'
# Live 绘图 update option
livePlotUpdate = True
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = True
# 绘制 x axis unit multiplier (ns, us or ms)
plotXaxisUnits = us
# 绘制 x axis label
xAxisLabel = 'Delay (us)'
# 保存 options------------------------------------------------------------------
# 保存 interval for first 扫描 through all 延迟 点s:
saveSpacing_inScanPts = 2
# 保存 interval in averaging 运行s:
saveSpacing_inAverages = 3
# Path to folder where 数据 will be 保存d:
savePath = os.getcwd()+"\\Saved_Data\\"
# File name for 数据 file
saveFileName = "T1_"
# Averaging options:------------------------------------------------------------
# Option to do shot by shot 对比度 normalization:
shotByShotNormalization = False
# Option to randomize order of 扫描 点s
randomize = True
#------------------------- END OF USER 输入 ----------------------------------#
scannedParam = np.linspace(start_t,end_t, N_scanPts, endpoint=True)
#If start_t<(t_readout延迟 + 2*t_min*round((1*us)/t_min) + t_pi), shift 扫描ned time 点s by (t_readout延迟 + 2*t_min*round((1*us)/t_min) + t_pi) to avoid pulse overlap 错误s and warn user:
if start_t< (t_readoutDelay + 2*t_min*round((1*us)/t_min) + t_pi):
	scannedParam = [x + (t_readoutDelay + 2*t_min*round((1*us)/t_min) + t_pi) for x in scannedParam]
	print('Note: start_t (and all subsequent scan points) have been shifted by ', (t_readoutDelay + 2*t_min*round((1*us)/t_min) + t_pi),'ns to avoid pulse overlap errors. First scan point is hence', scannedParam[0],'ns.')
#序列字符串:
sequence = 'T1seq'
#扫描 start Name
scanStartName = 'start_t'
#扫描 end Name
scanEndName = 'end_t'
#序列 arguments:
sequenceArgs = [t_AOM,t_readoutDelay,t_pi]
#PB 通道s
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig}
#Make 保存 file path
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
#Make param file path
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
#Param file 保存 settings
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'start_t:',scannedParam[0],'end_t:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_AOM,t_readoutDelay,t_pi]
	return sequenceArgs
	
def updateExpParamList():
	expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'start_t:',scannedParam[0],'end_t:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList