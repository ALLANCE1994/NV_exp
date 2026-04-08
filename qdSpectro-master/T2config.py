# T2配置.py
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
# T2实验配置
本脚本可用于配置mainControl.py以运行T2实验。记录NV金刚石样品发射的荧光信号，该信号随T2脉冲序列中扫描延迟时长的变化而变化（详见实验方案），数据将以制表符分隔的文本文件形式保存（保存选项详见下文）。若用户选择在序列中仅设置一个π脉冲（即用户输入的numberOfPiPulses设为1），则扫描延迟为π/2脉冲与π脉冲之间的时延；若用户选择在T2序列中施加多个π脉冲（即numberOfPiPulses>1），则扫描延迟为π脉冲之间的时延。延迟将从startTau至endTau，按N_scanPts个步长进行扫描。在每个扫描点，脚本会采集2*Nsamples次荧光读数，在连续采样过程中将脉冲序列中最后一个π/2脉冲进行180°相移，从而获得两组荧光计数读数R1和R2，并据此计算对比度（详见下文“对比度设置”部分说明）。因此，第一组读数与第二组读数各包含Nsamples次采样。首次扫描完成后，脚本将重复扫描Navg次，对所有运行结果中各扫描点的对比度取平均值（对比度定义与平均选项详见下文）。

---

## 对比度设置
实验的对比度模式应设置为`ratio_DifferenceOverSum`。该模式下，对比度C通过两组读数R1和R2的差值与和值之比计算得出，即C=(R1-R2)/(R1+R2)。为便于调试，用户也可选择另外两种对比度模式：`signalOnly`（仅绘制R1数据曲线）或`ratio_SignalOverReference`（绘制R1/R2比值曲线）。

## 平均选项
默认情况下，脚本会针对每个扫描点，根据R1计数平均值（对该扫描点下Nsamples次R1读数取平均）与R2计数平均值计算对比度。若希望先逐次计算R1与R2采样值对应的对比度C，再对所有采样的对比度取平均，可将shotByShotNormalization选项设为True。例如，当contrastMode设为`ratio_DifferenceOverSum`且shotByShotNormalization设为True时，会先对每一组R1、R2采样值计算(R1-R2)/(R1+R2)，再对所有比值取平均。

脚本首次扫描延迟时，会按延迟时长从短到长的顺序执行。若Navg>1，脚本将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，其余扫描的扫描点顺序均会随机打乱。若需关闭随机化功能，可将下方的randomize选项设为False。

## 绘图选项
将livePlotUpdate设为True，可在数据采集过程中实时绘制数据曲线。需注意，首次扫描完成后，绘图界面仅在后续每次扫描结束时更新。若livePlotUpdate设为False，则仅在实验全部结束后绘制数据曲线。

将plotPulseSequence设为True，可绘制已编程至PulseBlaster中的脉冲序列。需注意，程序会等待用户关闭该绘图窗口后再继续运行。

## 保存选项
用户可自定义数据保存的频率。首次扫描时，可设置按saveSpacing_inScanPts个扫描点为间隔保存数据（例如该变量设为2时，脚本会每隔一个扫描点重新保存一次数据）。后续扫描中，脚本会在每次扫描结束后，按saveSpacing_inAverages次平均运行为间隔重新保存数据（例如该值设为3时，每完成3次平均运行便重新保存一次数据）。无论用户如何设置上述选项，数据均会在首次扫描结束及实验全部结束时（即最后一次平均运行完成后）自动保存。

## IQ补偿时延
为补偿线缆与仪器带来的时延，需在控制SRS信号源I/Q调制开启与关闭的脉冲沿，和控制微波开启与关闭的脉冲沿之间添加IQpadding时延，以确保I/Q调制在整个微波脉冲持续时间内保持开启。该时延参数仅可在示波器上仔细监测脉冲序列后进行修改。若用户需调整该参数，可在下文用户输入区域的“高级用户选项”中找到对应设置项。

---

# 脚本运行方法
1. 编辑connectionConfig.py，定义实验装置中PulseBlaster、SRS信号源与数据采集卡（DAQ）的通道连接配置。
2. 编辑下文的用户输入参数区域。
3. 运行脚本。在Windows命令提示符中，可通过执行`python mainControl.py T2config`命令运行该脚本。

---

# 用户输入参数说明
> 注：t_min为PulseBlaster板卡的时间分辨率（即t_min=1/时钟频率）。例如，500MHz板卡对应的t_min=2ns。

- **startTau**：若numberOfPiPulses设为1，该值为π/2脉冲与π脉冲之间的最小延迟（单位：ns），且必须满足>(2*IQpadding + (3/4)*t_pi + 5*t_min)；若numberOfPiPulses>1，该值为π脉冲之间的最小延迟（单位：ns），且必须满足>(2*(2*IQpadding + (3/4)*t_pi + 5*t_min))。
- **endTau**：扫描范围内的最大延迟时长，单位：ns。
- **N_scanPts**：扫描点数。需注意：本脚本中扫描的延迟为脉冲序列内π脉冲之间的时延，其数值为初始/末位π/2脉冲与首个/末位π脉冲之间时延的两倍。因此，该延迟的步长至少为2*t_min，即PulseBlaster最高时间分辨率（1/时钟频率）的两倍。
- **microwavePower**：SRS信号源输出功率，单位：dBm。**注意**：该值不得超过与SRS输出端相连的任意放大器的输入功率上限。
- **microwaveFrequency**：SRS信号源输出微波频率，单位：Hz。
- **t_AOM**：声光调制器（AOM）脉冲持续时间，单位：ns。
- **t_readoutDelay**：AOM脉冲起始至DAQ采集脉冲之间的延迟，单位：ns。最优延迟可通过optimReadoutDelay.py脚本确定（详见实验方案论文第54步）。
- **t_pi**：π脉冲持续时间，单位：ns。
- **numberOfPiPulses**：每个脉冲序列中施加的π脉冲数量。
- **Nsamples**：每个扫描点的荧光测量采样次数。
- **Navg**：平均运行次数（即延迟扫描的重复次数）。
- **DAQtimeout**：DAQ等待目标采样数就绪（即完成采集）的最长等待时间，单位：秒。
- **contrastMode**：本实验中该参数应设为`ratio_DifferenceOverSum`，其余可选模式为`ratio_SignalOverReference`和`signalOnly`（详见上文“对比度设置”说明）。
- **livePlotUpdate**：设为True可在数据采集时实时更新绘图（详见上文“绘图选项”说明）。
- **plotPulseSequence**：设为True可在实验开始时绘制脉冲序列（详见上文“绘图选项”说明）。
- **plotXaxisUnits**：设置数据曲线图横轴单位，可选ns、us、ms。
- **xAxisLabel**：设置数据曲线图横轴标签。
- **saveSpacing_inScanPts**：首次扫描过程中，数据保存的扫描点间隔数。
- **saveSpacing_inAverages**：首次完整扫描完成后，数据保存的平均运行间隔次数。
- **savePath**：数据保存文件夹路径。默认情况下，数据保存在脚本所在目录下的Saved_Data文件夹中。
- **saveFileName**：数据保存文件名。该文件名后会自动附加脚本运行的日期与时间。
- **shotByShotNormalization**：设为True可开启逐次采样对比度归一化（详见上文“平均选项”说明）。
- **randomize**：设为True可对首次扫描之后的所有扫描打乱扫描点顺序。
- **IQpadding**：控制I/Q调制开启/关闭的脉冲沿与微波开启/关闭的脉冲沿之间的延迟，单位：ns。
"""
from spinapi import ns,us,ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min, 时间分辨率 of the PulseBlaster, given by 1/(时钟频率):
t_min = 1e3/PBclk #in ns
#-------------------------  USER 输入  ---------------------------------------#

# 扫描 参数s:-------------------------------------------------------------
# 启动 延迟 持续时间 (单位为纳秒):
startTau =100
# End 延迟 持续时间 (单位为纳秒):
endTau = 10000
# 数量 延迟 steps:
N_scanPts = 100
# 微波 功率 输出 from SRS(dBm) - DO NOT EXCEED YOUR AMPLIFIER'S MAXIMUM 输入 功率:
microwavePower = -5
# 微波 频率 (Hz):
microwaveFrequency = 2.87e9 
# Pulse 序列 参数s:----------------------------------------------------
# AOM pulse 持续时间 (单位为ns)
t_AOM= 5*us
# 读取out 延迟 (单位为ns)
t_readoutDelay = 2.3*us
# Pi-pulse 持续时间 (单位为ns)
t_pi = 24
# 数量 pi 脉冲s:
numberOfPiPulses = 1
# 数量 fluorescence measurement 样本 to take at each 延迟 点:
Nsamples = 10000
# 数量 averaging 运行s to do:
Navg = 1
#DAQ 超时, 单位为秒:
DAQtimeout = 10
# 绘图 options--------------------------------------------------------------
# 对比度 mode
contrastMode ='ratio_DifferenceOverSum'
# Live 绘图 update option
livePlotUpdate = True
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = True
# 绘制 x axis unit multiplier (ns, us or ms)
plotXaxisUnits = ns
# 绘制 x axis label
xAxisLabel = 'Delay (ns)'
# 保存 options------------------------------------------------------------------
# 保存 interval for first 扫描 through all 延迟 点s:
saveSpacing_inScanPts = 2
# 保存 interval in averaging 运行s:
saveSpacing_inAverages = 3
# Path to folder where 数据 will be 保存d:
savePath = os.getcwd()+"\\Saved_Data\\"
# File name for 数据 file
saveFileName = "T2_"
# Averaging options:------------------------------------------------------------
# Option to do shot by shot 对比度 normalization:
shotByShotNormalization = False
# Option to randomize order of 扫描 点s
randomize = True
#Advanced user options--------------------------------------------------------------
# IQ padding, 单位为ns (this should be left at t_min*round(30*ns/t_min),unless the user  
# requires an especially short 自由进动 延迟 - this 参数 should only be 
# editted with close monitoring of the 脉冲序列 on the scope.
IQpadding = t_min*round(30*ns/t_min)
#------------------------- END OF USER 输入 ----------------------------------#

scannedParam = np.linspace(startTau,endTau, N_scanPts, endpoint=True) 
#序列字符串:
sequence = 'T2seq'
#扫描 start Name
scanStartName = 'startTau'
#扫描 end Name
scanEndName = 'endTau'
#PB 通道s
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig,'I':I,'Q':Q}
#序列 args
sequenceArgs = [t_AOM,t_readoutDelay,t_pi,IQpadding,numberOfPiPulses]
#Make 保存 file path
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
#Make param file path
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
#Param file 保存 settings
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startTau:',scannedParam[0],'endTau:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'numberOfPiPulses',numberOfPiPulses,'IQpadding',IQpadding,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_AOM,t_readoutDelay,t_pi,IQpadding,numberOfPiPulses]
	return sequenceArgs
	
def updateExpParamList():
	expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startTau:',scannedParam[0],'endTau:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'numberOfPiPulses',numberOfPiPulses,'IQpadding',IQpadding,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList