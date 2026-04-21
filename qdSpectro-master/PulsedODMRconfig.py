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

脉冲ODMR实验通过"激光极化 → 等待 → 微波π脉冲操控 → 激光读态"的循环来探测NV色心共振谱。
微波频率从起始频率扫描至终止频率，在每个频率点记录荧光信号与参考信号的对比度。

一个完整的脉冲ODMR测试周期包含四个阶段：

1. 自旋态初始化（极化）
   - 施加532nm激光脉冲，将电子自旋极化到基态|m_s=0⟩
   - 参数：t_p（激光脉冲宽度，通常300µs量级）

2. 等待与稳定
   - 关闭激光，等待电子通过ISC通道弛豫回基态
   - 参数：t_wait（等待时间，通常3-5µs）

3. 自旋态操控（翻转）
   - 施加微波π脉冲，频率f以步进值扫描
   - 参数：t_pi（π脉冲宽度，由Rabi实验测定）

4. 自旋态读取
   - 施加第二个激光脉冲，激发荧光并重新极化自旋
   - 参数：t_readoutLaser（读取激光脉冲宽度，用于激发荧光和ISC重新极化）
   - 荧光信号收集：仅在读取激光开始后的一小段时间窗口内积分采集
   - 参数：t_integration（积分时间，通常200-500ns）、t_readoutDelay（积分延迟）

差分设计：每个测试周期包含两个子序列（MW_on和MW_off）用于噪声抑制。
MW_on有微波脉冲，MW_off无微波脉冲。通过对比两者荧光信号，可有效抑制
激光功率抖动、探测器基线漂移等共模噪声，提高信噪比。

脉冲序列时序图（MW_on子序列）：
│ 阶段1：极化          │ 阶段2：等待   │ 阶段3：π脉冲 │ 阶段4：读取（含积分窗口）  │
├──────────────────────┼───────────────┼──────────────┼────────────────────────────┤
│ AOM: ████████████████│               │              │ ████████████████████████   │
│ Laser: ON            │ OFF           │ OFF          │ ON                        │
│ MW:  OFF             │ OFF           │ ████████████│ OFF                       │
│ DAQ积分:            │               │              │ ░░░░░░░░░░░░░░░░░░░░░░░ │

注：阶段3（π脉冲）结束后立即进入阶段4（读取），中间无延迟，避免自旋不必要的弛豫。

对比度计算：contrastMode可选择比值法(ratio)或差值法(difference)

——平均计算选项——
默认情况下，每个频率点取Nsamples次信号和背景的平均值计算对比度；
可将shotByShotNormalization设为True，先逐次计算对比度再平均。

——绘图选项——
将livePlotUpdate设为True可实时绘图；plotPulseSequence设为True可绘制脉冲序列。

——保存选项——
saveSpacing_inScanPts控制首次扫描保存间隔；saveSpacing_inAverages控制平均扫描保存间隔。

运行本脚本：python mainControl.py PulsedODMRconfig
"""

# 导入模块
from spinapi import ns, us, ms
from SRScontrol import Hz, kHz, MHz, GHz
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *

# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 计算得出：
t_min = 1e3/PBclk # 单位为 ns

#------------------------- 用户输入 ---------------------------------------#

# 微波扫描参数:----------------------------------------------------
# 起始频率 (单位为Hz):
# 注意：NV色心的典型共振频率约为2.87 GHz，具体值取决于磁场强度
startFreq = 2.85e9
# 结束频率 (单位为Hz):
endFreq = 2.89e9
# 频率步进数:
N_scanPts = 81
# SRS 信号源的微波功率输出 (dBm) - 请勿超过放大器的最大输入功率:
# 注意：此参数仅适用于SRS信号源，B210使用B210_gain参数
microwavePower = 10
# B210 设备的增益设置（dB）- 范围通常为 0-70 dB
# 注意：B210 使用增益（dB）而不是功率（dBm）
# 建议增益值：50-65 dB，过高的增益可能导致信号失真或损坏放大器
B210_gain = 60
# 初始微波频率（通常设置为startFreq）:
microwaveFrequency = startFreq

# 脉冲序列参数:----------------------------------------------------
# π脉冲持续时间 (ns) - 由Rabi振荡实验精确测定
# 典型值：100-500 ns，取决于NV色心的具体特性
# 【重要】当前值为估计值，建议先运行Rabi实验确定正确的t_pi
t_pi = 300
# 自旋极化脉冲宽度 (ns) - 激光极化脉冲的持续时间
# 典型值：百微秒量级，如300 µs或1 ms
# 【优化】从25µs增加到300µs，确保自旋充分极化
t_p = 300 * us
# 等待稳定时间 (ns) - 极化后等待微波操控的稳定时间
# 典型值：3-5 µs
t_wait = 5 * us
# 读取激光脉冲宽度 (ns) - AOM读取激光脉冲的持续时间，用于激发荧光和ISC重新极化
# 注意：该激光脉冲同时承担两个功能：激发荧光和重新极化自旋
# 重要：读取光脉冲必须紧接在微波脉冲之后，中间无延迟，以避免自旋在读取前发生不必要的弛豫
# 典型值：300 ns - 10 µs（应足够长以完成ISC重新极化）
t_readoutLaser = 1 * us
# 读取延迟 (ns) - AOM读取激光脉冲开始后延迟多久开始DAQ积分采集
# 注意：并非采集整个读取光脉冲期间的所有荧光，而是在脉冲开始后选取固定短时间窗口
# 典型值：0 ns（DAQ与读取激光同步开始）
t_readoutDelay = 0 * ns
# 积分时间 (ns) - DAQ积分窗口宽度，仅在读取激光开始后的一小段时间内采集荧光信号
# 重要：|0⟩态和|±1⟩态的荧光计数率差异在激光照射初始时刻最大，随光照时间延长趋于一致
# 【优化】缩短积分时间至200ns以获得更好的对比度
# 典型值：200-500 ns（参考《2023金刚石NV色心微波整形脉冲自旋调控方法及宽场成像.pdf》）
t_integration = 200 * ns

# 荧光测量样本数 - 每个频率点采集的荧光测量样本数:
Nsamples = 500
# 平均运行次数 - 频率扫描的重复次数:
Navg = 1
# DAQ超时，单位为秒 - 数据采集卡等待样本就绪的最长时间:
DAQtimeout = 10

# 对比度模式 - 可选：'ratio_SignalOverReference', 'ratio_DifferenceOverSum', 'signalOnly'
contrastMode = 'signalOnly'

# 绘图选项:--------------------------------------------------------------
# 实时绘图更新选项 - 设为True可在数据采集时实时更新曲线图:
livePlotUpdate = True
# 绘制脉冲序列选项 - 设为True可绘制已编程至PulseBlaster的脉冲序列:
plotPulseSequence = True
# 绘制x轴单位 (Hz, kHz, MHz 或 GHz):
plotXaxisUnits = MHz
# 绘制x轴标签:
xAxisLabel = 'Frequency (MHz)'

# 保存选项:------------------------------------------------------------------
# 首次扫描时数据保存的频率点间隔:
saveSpacing_inScanPts = 2
# 平均运行中数据保存的间隔:
saveSpacing_inAverages = 1
# 数据保存文件夹路径:
savePath = os.getcwd() + "\\Saved_Data\\"
# 数据文件名:
saveFileName = "PulsedODMR_"

# 平均选项:------------------------------------------------------------
# 逐次采样对比度归一化选项 - 设为True可先逐次计算对比度再取平均:
shotByShotNormalization = False
# 随机化扫描点顺序选项 - 设为True可打乱首次扫描后的扫描顺序:
randomize = False

#------------------------- END OF USER INPUT ----------------------------------#

scannedParam = np.linspace(startFreq, endFreq, N_scanPts, endpoint=True)
# 序列字符串:
sequence = 'PulsedODMRseq'
# 扫描起始名称:
scanStartName = 'startFreq'
# 扫描结束名称:
scanEndName = 'endFreq'
# PB通道配置:
PBchannels = {'AOM': AOM, 'uW': uW, 'DAQ': DAQ, 'STARTtrig': STARTtrig}
# 序列参数:
sequenceArgs = [t_pi, t_p, t_wait, t_readoutLaser, t_readoutDelay, t_integration]

# 创建数据文件保存路径:
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName + dateTimeStr + ".txt"
# 创建参数文件保存路径:
paramFileName = savePath + saveFileName + dateTimeStr + '_PARAMS' + ".txt"

# 参数文件保存格式设置:
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_scanPts:', N_scanPts, 'Navg:', Navg, 'Nsamples:', Nsamples, 'startFreq:', scannedParam[0], 'endFreq:', scannedParam[-1], 'microwavePower:', microwavePower, 'B210_gain:', B210_gain, 't_pi:', t_pi, 't_p:', t_p, 't_wait:', t_wait, 't_readoutLaser:', t_readoutLaser, 't_readoutDelay:', t_readoutDelay, 't_integration:', t_integration, 'shotByShotNormalization:', shotByShotNormalization, 'randomize:', randomize, 'plotPulseSequence:', plotPulseSequence, 'saveSpacing_inScanPts:', saveSpacing_inScanPts, 'saveSpacing_inAverages:', saveSpacing_inAverages, 'dataFileName:', dataFileName]

def updateSequenceArgs():
    sequenceArgs = [t_pi, t_p, t_wait, t_readoutLaser, t_readoutDelay, t_integration]
    return sequenceArgs

def updateExpParamList():
    expParamList = ['N_scanPts:', N_scanPts, 'Navg:', Navg, 'Nsamples:', Nsamples, 'startFreq:', scannedParam[0], 'endFreq:', scannedParam[-1], 'microwavePower:', microwavePower, 'B210_gain:', B210_gain, 't_pi:', t_pi, 't_p:', t_p, 't_wait:', t_wait, 't_readoutLaser:', t_readoutLaser, 't_readoutDelay:', t_readoutDelay, 't_integration:', t_integration, 'shotByShotNormalization:', shotByShotNormalization, 'randomize:', randomize, 'plotPulseSequence:', plotPulseSequence, 'saveSpacing_inScanPts:', saveSpacing_inScanPts, 'saveSpacing_inAverages:', saveSpacing_inAverages, 'dataFileName:', dataFileName]
    return expParamList, dataFileName, paramFileName