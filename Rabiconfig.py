
# Rabiconfig.py
# 自动生成的配置文件

import numpy as np

# 实验参数
Nsamples = 1000
Navg = 1
N_scanPts = 101

# 保存路径
savePath = "./Saved_Data"

# 实验控制参数
plotPulseSequence = False
randomize = False
livePlotUpdate = True
saveSpacing_inScanPts = 1
saveSpacing_inAverages = 1
DAQtimeout = 10.0

# 实验特定参数

# 扫描参数
startPulseLength = 0
endPulseLength = 200
scannedParam = np.linspace(startPulseLength, endPulseLength, N_scanPts, endpoint=True)
scanStartName = 'startPulseLength'
scanEndName = 'endPulseLength'

# 微波参数
microwavePower = 10.0
microwaveFrequency = 2.7e9

# Rabi特定参数
t_readoutDelay = 2300
t_AOM = 5000

# 序列参数
sequence = 'RabiSeq'

# 更新序列参数的函数
def updateSequenceArgs():
    return [t_readoutDelay, t_AOM]

# 更新实验参数列表的函数
def updateExpParamList():
    return ['N_scanPts:', N_scanPts, 'Navg:', Navg, 'Nsamples:', Nsamples, 'startPulseLength:', startPulseLength, 'endPulseLength:', endPulseLength, 't_readoutDelay:', t_readoutDelay, 't_AOM:', t_AOM, 'shotByShotNormalization:', False, 'randomize:', randomize, 'plotPulseSequence:', plotPulseSequence, 'saveSpacing_inScanPts:', saveSpacing_inScanPts, 'saveSpacing_inAverages:', saveSpacing_inAverages, 'dataFileName:', 'Rabi_data.txt']
