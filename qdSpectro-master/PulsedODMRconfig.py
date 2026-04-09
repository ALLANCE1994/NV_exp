# PulsedODMR配置.py
# 版权所有 2026 NV色心实验团队

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明和本许可声明应包含在软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不附带任何形式的明示或暗示的保证，
# 包括但不限于对适销性、特定用途的适用性和非侵权性的保证。
# 在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责，
# 无论是在合同行为、侵权行为或其他方面，由软件或软件的使用或其他交易引起的。

"""
脉冲ODMR（Optical Detected Magnetic Resonance）实验配置

本脚本可用于配置mainControl.py以运行脉冲ODMR实验。
实验会记录氮空位（NV）金刚石样品发出的荧光信号，该信号随微波驱动信号的频率变化而变化，
最终数据将以制表符分隔的文本文件形式保存。

脉冲ODMR实验的核心流程是"激光极化 → 等待 → 微波π脉冲操控 → 激光读态"的循环，
并通过扫描微波频率来获取共振谱。

——对比度设置——
脚本将根据contrastMode变量设定的计算公式，利用信号计数与背景计数计算对比度。
若contrastMode设为'ratio_SignalOverReference'，对比度定义为信号与背景的比值；
若设为'ratio_DifferenceOverSum'，对比度则定义为信号与背景的差值同二者之和的比值；
用户也可选择'signalOnly'对比度模式，该模式下仅绘制信号计数曲线，忽略背景计数。

——平均计算选项——
默认情况下，针对每个频率点，脚本会基于该频率点下Nsamples次信号读数的平均值与Nsamples次背景读数的平均值计算对比度。
若希望先逐次计算信号与背景样本的对比度，再对所有样本结果取平均，可将shotByShotNormalization设为True。

——绘图选项——
将livePlotUpdate设为True，可在数据采集过程中实时绘制数据曲线。
将plotPulseSequence设为True，可绘制已编程至PulseBlaster设备中的脉冲序列。

——保存选项——
用户可自主选择数据保存的频率。
首次扫描时，可设置按saveSpacing_inScanPts个频率点为间隔保存数据。
后续扫描时，脚本将在每次频率扫描结束后，按saveSpacing_inAverages次平均周期为间隔重新保存数据。

运行本脚本的步骤：
1）编辑connectionConfig.py，定义实验装置中PulseBlaster、斯坦福研究系统（SRS）设备及数据采集卡（DAQ）的通道连接配置。
2）编辑下文的用户输入参数区域。
3）运行脚本。在Windows命令提示符中，可通过输入python mainControl.py PulsedODMRconfig命令运行该脚本。

用户输入参数：
*startFreq：扫描范围内的最低频率，单位为赫兹（Hz）。
*endFreq：扫描范围内的最高频率，单位为赫兹（Hz）。
*N_scanPts：扫描中的频率点数量。
*microwavePower：SRS信号发生器的输出功率，单位为分贝毫瓦（dBm）。
*t_pi：π脉冲的持续时间，单位为纳秒（ns）。
*t_readoutDelay：AOM脉冲起始至DAQ采集脉冲的延迟时间，单位为纳秒（ns）。
*t_AOM：声光调制器（AOM）脉冲持续时间，单位为纳秒（ns）。
*Nsamples：每个频率点下需采集的荧光测量样本数。
*Navg：平均运行次数（即频率扫描的重复次数）。
*DAQtimeout：数据采集卡等待所需数量样本就绪的时长，单位为秒（s）。
"""

# 导入模块
from spinapi import ns, us, ms
from SRScontrol import Hz, kHz, MHz, GHz
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *

# 定义 t_min, 时间分辨率 of the PulseBlaster, given by 1/(时钟频率):
t_min = 1e3/PBclk # in ns

#-------------------------  USER 输入  ---------------------------------------#

# 微波 扫描 参数s:----------------------------------------------------
# 启动 频率 (单位为Hz):
startFreq = 2.82e9
# End 频率 (单位为Hz):
endFreq = 2.92e9
# 数量 频率 steps:
N_scanPts = 101
# 微波 功率 输出 from SRS(dBm) - DO NOT EXCEED YOUR AMPLIFIER'S MAXIMUM 输入 功率:# 微波参数
microwavePower = 10
microwaveFrequency = startFreq

# Pulse 序列 参数s:----------------------------------------------------# π脉冲持续时间 (ns):
t_pi = 32  # 由Rabi振荡实验精确测定
# 自旋极化脉冲宽度 (ns):
t_p = 1 * ms  # 典型值为百微秒量级，如300 µs或1 ms
# 等待稳定时间 (ns):
t_wait = 4 * us  # 典型值为3-5 µs
# 读取脉冲宽度 (ns):
t_r = 300 * ns  # 典型值为数百纳秒，如300 ns
# AOM pulse 持续时间 (ns):
t_AOM = 5 * us
# 读取out 延迟 (ns):
t_readoutDelay = 2.3 * us

# 数量 fluorescence measurement 样本 to take at each 频率 点:
Nsamples = 1000
# 数量 averaging 运行s to do:
Navg = 1
# DAQ 超时, 单位为秒:
DAQtimeout = 10

# 对比度 mode
contrastMode = 'ratio_SignalOverReference'

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
savePath = os.getcwd() + "\\Saved_Data\\"
# File name for 数据 file
saveFileName = "PulsedODMR_"

# Averaging options:------------------------------------------------------------
# Option to do shot by shot 对比度 normalization:
shotByShotNormalization = False
# Option to randomize order of 扫描 点s
randomize = True

#------------------------- END OF USER 输入 ----------------------------------#

scannedParam = np.linspace(startFreq, endFreq, N_scanPts, endpoint=True)
# 序列字符串:
sequence = 'PulsedODMRseq'
# 扫描 start Name
scanStartName = 'startFreq'
# 扫描 end Name
scanEndName = 'endFreq'
# PB 通道s
PBchannels = {'AOM': AOM, 'uW': uW, 'DAQ': DAQ, 'STARTtrig': STARTtrig}
# 序列 args
sequenceArgs = [t_pi, t_readoutDelay, t_AOM]

# Make 保存 file path
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName + dateTimeStr + ".txt"
# Make param file path
paramFileName = savePath + saveFileName + dateTimeStr + '_PARAMS' + ".txt"

# Param file 保存 settings
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:', N_scanPts, 'Navg:', Navg, 'Nsamples:', Nsamples, 'startFreq:', scannedParam[0], 'endFreq:', scannedParam[-1], 'microwavePower:', microwavePower, 't_pi:', t_pi, 't_readoutDelay:', t_readoutDelay, 't_AOM:', t_AOM, 'shotByShotNormalization:', shotByShotNormalization, 'randomize:', randomize, 'plotPulseSequence:', plotPulseSequence, 'saveSpacing_inScanPts:', saveSpacing_inScanPts, 'saveSpacing_inAverages:', saveSpacing_inAverages, 'dataFileName:', dataFileName]

def updateSequenceArgs():
    sequenceArgs = [t_pi, t_p, t_wait, t_r, t_readoutDelay, t_AOM]
    return sequenceArgs
    
def updateExpParamList():
    expParamList = ['N_scanPts:', N_scanPts, 'Navg:', Navg, 'Nsamples:', Nsamples, 'startFreq:', scannedParam[0], 'endFreq:', scannedParam[-1], 'microwavePower:', microwavePower, 't_pi:', t_pi, 't_p:', t_p, 't_wait:', t_wait, 't_r:', t_r, 't_readoutDelay:', t_readoutDelay, 't_AOM:', t_AOM, 'shotByShotNormalization:', shotByShotNormalization, 'randomize:', randomize, 'plotPulseSequence:', plotPulseSequence, 'saveSpacing_inScanPts:', saveSpacing_inScanPts, 'saveSpacing_inAverages:', saveSpacing_inAverages, 'dataFileName:', dataFileName]
    return expParamList
