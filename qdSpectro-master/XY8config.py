# XY8配置.py
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
# XY8实验配置
本脚本可用于配置mainControl.py以运行XY8实验。氮空位（NV）金刚石样品发出的荧光信号，会随XY8脉冲序列中π脉冲间扫描延时的时长变化而被记录（详见实验方案），数据将以制表符分隔的文本文件形式保存（保存选项详见下文）。延时扫描范围为从startTau至endTau，共分为N_scanPts个扫描步长。

在每个扫描点，脚本会采集2*Nsamples次荧光读数，通过在连续采样中对脉冲序列最后一个π/2脉冲进行180°相移，得到两组荧光计数读数R1和R2，并据此计算对比度（详见下文"对比度设置"部分说明）。其中，第一组读数与第二组读数各采集Nsamples次。首次扫描完成后，脚本会将扫描过程重复Navg次，并对所有扫描轮次中各扫描点的对比度取平均值（对比度定义与平均选项详见下文）。

---

## 对比度设置
实验的对比度模式需设置为`ratio_DifferenceOverSum`。该模式下，对比度C通过两组读数R1、R2的差值与和值之比计算得出，即`C=(R1-R2)/(R1+R2)`。

为便于调试，用户也可选择另外两种对比度模式：
- `signalOnly`：仅绘制R1信号曲线
- `ratio_SignalOverReference`：绘制R1/R2的比值曲线

---

## 平均选项
默认情况下，脚本会先对每个扫描点下的Nsamples次R1读数、Nsamples次R2读数分别取平均，再基于平均后的R1、R2计数计算对比度。

若希望先逐组计算R1与R2样本的对比度C，再对所有样本的C值取平均，可将`shotByShotNormalization`选项设为True。例如，当对比度模式为`ratio_DifferenceOverSum`且逐次归一化开启时，会先对每一组R1、R2样本计算`(R1-R2)/(R1+R2)`，再对所有比值取平均。

脚本首次扫描延时参数时，会按延时从短到长的顺序执行。若Navg＞1，脚本将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，后续所有扫描的扫描点顺序均会随机打乱。若需关闭随机排序，可将下方`randomize`选项设为False。

---

## 绘图选项
将`livePlotUpdate`设为True，可在数据采集过程中实时绘制曲线。需注意，首次扫描完成后，绘图仅在每轮后续扫描结束时更新。若设为False，数据将仅在实验全部结束后统一绘制。

将`plotPulseSequence`设为True，可绘制已编程至脉冲发生器（PulseBlaster）中的脉冲序列。程序会等待用户关闭该序列绘图窗口后再继续运行。

---

## 保存选项
用户可自定义数据保存频率：
- 首次扫描时，可按`saveSpacing_inScanPts`设定的扫描点间隔保存数据（例如设为2时，每隔一个扫描点重新保存一次数据）
- 后续扫描中，脚本会在每轮扫描结束后，按`saveSpacing_inAverages`设定的平均轮次间隔重新保存数据（例如设为3时，每完成3轮平均后保存一次）

无论上述参数如何设置，数据均会在首次扫描结束、以及整个实验（即最后一轮平均）完成时自动保存。

---

## IQ补偿延时
为补偿线缆与仪器带来的延时，需在SRS信号源I/Q调制的开关脉冲沿与微波开关脉冲沿之间添加延时参数`IQpadding`，确保I/Q调制在整个微波脉冲持续时间内保持开启。该延时参数需配合示波器观测脉冲序列后谨慎修改，若需调整，可在下文用户输入区的"高级用户选项"中找到对应设置。

---

# 脚本运行步骤
1. 编辑connectionConfig.py，定义实验系统中脉冲发生器（PulseBlaster）、SRS信号源与数据采集卡（DAQ）的通道连接配置
2. 编辑下文的用户输入参数区
3. 运行脚本：在Windows命令提示符中，输入`python mainControl.py XY8config`执行

---

# 用户输入参数说明
注：t_min为脉冲发生器（PulseBlaster）板卡的时间分辨率，即`t_min=1/时钟频率`。例如，500MHz板卡对应的t_min=2ns。

- **startTau**：扫描的最短延时（单位：ns），要求必须满足`＞2*(2*IQpadding + (3/4)*t_pi + 5*t_min)`
- **endTau**：扫描的最长延时（单位：ns）
- **N_scanPts**：扫描总点数
  注：本脚本扫描的延时为脉冲序列中π脉冲之间的间隔，该时长是初始/末位π/2脉冲与首个/末个π脉冲间延时的两倍。因此，该延时的步长至少为脉冲发生器最高时间分辨率（t_min）的两倍
- **microwavePower**：SRS信号源输出功率（单位：dBm）
  警告：该值不得超过与SRS输出端相连的任意放大器的输入功率上限
- **B210_gain**：B210设备的增益设置（dB）- 范围通常为0-70 dB，过高的增益可能导致信号失真。建议增益值：50-65 dB。
- **microwaveFrequency**：SRS信号源输出微波频率（单位：Hz）
- **t_AOM**：声光调制器（AOM）脉冲持续时间（单位：ns）
- **t_readoutDelay**：AOM脉冲启动至DAQ采集脉冲的延时（单位：ns），最优延时可通过optimReadoutDelay.py脚本确定（详见实验方案论文第54步）
- **t_pi**：π脉冲持续时间（单位：ns）
- **N**：XY8脉冲序列中8个π脉冲组成的脉冲块的重复次数
- **Nsamples**：每个扫描点的荧光测量采样次数
- **Navg**：平均轮次（即延时扫描的重复次数）
- **DAQtimeout**：DAQ等待目标采样数就绪（即完成采集）的最长等待时间（单位：秒）
- **contrastMode**：本实验需设为`ratio_DifferenceOverSum`，可选模式还包括`ratio_SignalOverReference`与`signalOnly`（详见前文"对比度设置"）
- **livePlotUpdate**：设为True可在数据采集时实时更新绘图（详见前文"绘图选项"）
- **plotPulseSequence**：设为True可在实验开始时绘制脉冲序列（详见前文"绘图选项"）
- **plotXaxisUnits**：数据绘图的横轴单位，可选ns、us、ms
- **xAxisLabel**：数据绘图的横轴标签
- **saveSpacing_inScanPts**：首次扫描中数据保存的扫描点间隔数
- **saveSpacing_inAverages**：首次完整扫描后，数据保存的平均轮次间隔数
- **savePath**：数据保存文件夹路径，默认保存在脚本所在目录下的Saved_Data文件夹中
- **saveFileName**：数据保存文件名，运行脚本时会自动在文件名后追加执行日期与时间
- **shotByShotNormalization**：设为True可开启逐次采样对比度归一化（详见前文"平均选项"）
- **randomize**：设为True可对首次扫描后的所有扫描打乱扫描点顺序
- **IQpadding**：IQ调制开关脉冲沿与微波开关脉冲沿之间的延时（单位：ns）
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

# 扫描 参数s:-------------------------------------------------------------
# 启动 延迟 持续时间 (单位为纳秒), must be >(2*(2*IQpadding + (3/4)*t_pi + (5*t_min))):
startTau = 300
# End 延迟 持续时间 (单位为纳秒):
endTau = 480
# 数量 延迟 steps:
N_scanPts = 45
# 微波 功率 输出 from SRS(dBm) - DO NOT EXCEED YOUR AMPLIFIER'S MAXIMUM 输入 功率:
microwavePower = -5
# B210 设备的增益设置（dB）- 范围通常为 0-70 dB，过高的增益可能导致信号失真
# 注意：B210 使用增益（dB）而不是功率（dBm）
# 建议增益值：50-65 dB
B210_gain = 70
# 微波 频率 (Hz):
microwaveFrequency = 2e9
# Pulse 序列 参数s:----------------------------------------------------
# AOM pulse 持续时间 (单位为ns)
t_AOM= 5*us
# 读取out 延迟 (单位为ns)
t_readoutDelay = 2.3*us
# Pi-pulse 持续时间 (单位为ns)
t_pi = 24
# 数量 repeats of the block of 8 pi-pulses in the XY8 脉冲序列:
N =12
# 数量 fluorescence measurement 样本 to take at each 延迟 点:
Nsamples = 10000
# 数量 averaging 运行s to do:
Navg = 5
#DAQ 超时, 单位为秒:
DAQtimeout = 10
# 绘图 options--------------------------------------------------------------
# 对比度 mode
contrastMode ='ratio_DifferenceOverSum'
# Live 绘图 update option
livePlotUpdate = True
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = True
# 绘制 x axis unit multiplier
plotXaxisUnits = ns
# 绘制 x axis label (ns, us or ms)
xAxisLabel = 'Delay (ns)'
# 差分数据保存选项 - 设为 True 保存差分数据:
saveDifferentialData = True
# 图片保存选项 - 设为 True 保存实验图片:
savePlots = True
# 保存 options------------------------------------------------------------------
# 保存 interval for first 扫描 through all 延迟 点s:
saveSpacing_inScanPts = 5
# 保存 interval in averaging 运行s:
saveSpacing_inAverages = 3
# Path to folder where 数据 will be 保存d:
savePath = os.getcwd()+"\\Saved_Data\\"
# File name for 数据 file
saveFileName = "XY8_"
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
sequence = 'XY8seq'
#扫描 start Name
scanStartName = 'startTau'
#扫描 end Name
scanEndName = 'endTau'
#PB 通道s
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig,'I':I,'Q':Q}
#序列 args
sequenceArgs = [t_AOM,t_readoutDelay,t_pi,IQpadding,N]
#Make 保存 file path
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
#Make param file path
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
#Param file 保存 settings
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startTau:',scannedParam[0],'endTau:',scannedParam[-1],'microwavePower:',microwavePower,'B210_gain:',B210_gain,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'N',N,'IQpadding',IQpadding,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_AOM,t_readoutDelay,t_pi,IQpadding,N]
	return sequenceArgs

def updateExpParamList():
	expParamList = ['N_scanPts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startTau:',scannedParam[0],'endTau:',scannedParam[-1],'microwavePower:',microwavePower,'B210_gain:',B210_gain,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'t_pi',t_pi,'N',N,'IQpadding',IQpadding,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList, dataFileName, paramFileName