#!/usr/bin/env python3
# maincontrol_SER.py
# 功能：根据ESRconfig.py参数配置，控制B210输出SER实验的微波信号

import sys
import os
import time
import numpy as np
from time import localtime, strftime

# 频率单位定义
Hz = 1
kHz = 1e3
MHz = 1e6
GHz = 1e9

# ESR实验参数配置
# 微波扫描参数
startFreq = 2.7e9  # 起始频率 (Hz)
endFreq = 3.0e9    # 终止频率 (Hz)
N_scanPts = 101    # 扫描点数
microwavePower = -5  # 微波功率 (dBm)
microwaveGain = 50   # B210增益设置 (dB)

# 脉冲序列参数
t_duration = 80e-6  # 信号采集半周期持续时间 (s)
Nsamples = 1000     # 每个频率点的样本数
Navg = 1            # 平均运行次数
DAQtimeout = 10     # DAQ超时时间 (s)

# 对比度模式
contrastMode = 'ratio_SignalOverReference'  # 对比度计算模式

# 绘图选项
livePlotUpdate = True     # 实时绘图更新
plotPulseSequence = True  # 绘制脉冲序列
plotXaxisUnits = Hz       # x轴单位
xAxisLabel = 'Frequency (Hz)'  # x轴标签

# 保存选项
saveSpacing_inScanPts = 2  # 首次扫描保存间隔
saveSpacing_inAverages = 1  # 平均运行保存间隔
savePath = os.getcwd() + "\\Saved_Data\\"  # 保存路径
saveFileName = "ESR_"  # 保存文件名

# 平均选项
shotByShotNormalization = False  # 逐次采样对比度归一化
randomize = True  # 随机化扫描点顺序

# 计算扫描参数
scannedParam = np.linspace(startFreq, endFreq, N_scanPts, endpoint=True)

# 序列信息
sequence = 'ESRseq'
scanStartName = 'startFreq'
scanEndName = 'endFreq'
PBchannels = {'AOM': 0, 'uW': 1, 'DAQ': 2, 'STARTtrig': 3}  # 模拟通道配置
sequenceArgs = [t_duration]

# 生成文件名
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName + dateTimeStr + ".txt"
paramFileName = savePath + saveFileName + dateTimeStr + '_PARAMS' + ".txt"

# 参数列表
expParamList = [
    'N_scanPts:', N_scanPts,
    'Navg:', Navg,
    'Nsamples:', Nsamples,
    'startFreq:', scannedParam[0],
    'endFreq:', scannedParam[-1],
    'microwavePower:', microwavePower,
    't_duration:', t_duration,
    'shotByShotNormalization:', shotByShotNormalization,
    'randomize:', randomize,
    'plotPulseSequence:', plotPulseSequence,
    'saveSpacing_inScanPts:', saveSpacing_inScanPts,
    'saveSpacing_inAverages:', saveSpacing_inAverages,
    'dataFileName:', dataFileName
]


# 导入B210控制函数（已包含SRScontrol.py的功能）
sys.path.append(os.path.join(os.path.dirname(__file__), 'NV_exp', 'qdSpectro-master'))
from SRScontrol import (
    initSRS, enableSRS_RFOutput, disableSRS_RFOutput,
    setSRS_Freq, setSRS_RFAmplitude, setupSRSmodulation
)

# 主函数
def main():
    print("==================================")
    print(" B210 SER 实验控制")
    print("==================================")
    
    # 初始化B210设备
    print("初始化 B210 设备...")
    srs = initSRS(27, 'SG384')  # 参数仅为保持接口一致
    
    # 设置B210增益（注意：B210中增益控制输出功率）
    print(f"设置 B210 增益: {microwaveGain} dB")
    setSRS_RFAmplitude(srs, microwaveGain, 'dB')
    
    # 为ESR序列设置调制
    print("为ESR序列设置调制...")
    setupSRSmodulation(srs, 'ESRseq')
    
    # 计算频率步进
    freq_steps = np.linspace(startFreq, endFreq, N_scanPts, endpoint=True)
    
    # 准备数据存储
    signal_data = np.zeros(N_scanPts)
    reference_data = np.zeros(N_scanPts)
    contrast_data = np.zeros(N_scanPts)
    
    print(f"\n开始SER实验：")
    print(f"频率范围: {startFreq/1e9:.3f} GHz - {endFreq/1e9:.3f} GHz")
    print(f"扫描点数: {N_scanPts}")
    print(f"平均次数: {Navg}")
    print(f"每个频率点样本数: {Nsamples}")
    
    # 主实验循环
    # 首先启用RF输出，保持持续输出
    enableSRS_RFOutput(srs)
    
    for avg in range(Navg):
        print(f"\n=== 平均次数: {avg+1}/{Navg} ===")
        
        # 随机化频率点顺序（如果启用）
        if randomize and avg > 0:
            np.random.shuffle(freq_steps)
        
        # 频率扫描
        for i, freq in enumerate(freq_steps):
            # 只显示当前频率
            print(f"\r频率点 {i+1}/{N_scanPts}: {freq/1e9:.3f} GHz", end='', flush=True)
            
            # 设置频率
            setSRS_Freq(srs, freq, 'Hz')
            
            # 等待频率稳定
            time.sleep(0.2)
            
            # 模拟数据采集
            # 注意：这里只是模拟，实际实验中需要连接DAQ进行真实数据采集
            signal_counts = np.random.normal(1000, 50, Nsamples)  # 模拟信号计数
            
            # 等待背景稳定
            time.sleep(0.2)
            
            # 模拟背景采集
            reference_counts = np.random.normal(800, 30, Nsamples)  # 模拟背景计数
            
            # 计算对比度
            if contrastMode == 'ratio_SignalOverReference':
                if shotByShotNormalization:
                    contrast = np.mean(signal_counts / reference_counts)
                else:
                    contrast = np.mean(signal_counts) / np.mean(reference_counts)
            elif contrastMode == 'ratio_DifferenceOverSum':
                if shotByShotNormalization:
                    contrast = np.mean((signal_counts - reference_counts) / (signal_counts + reference_counts))
                else:
                    contrast = (np.mean(signal_counts) - np.mean(reference_counts)) / (np.mean(signal_counts) + np.mean(reference_counts))
            elif contrastMode == 'signalOnly':
                contrast = np.mean(signal_counts)
            else:
                print(f"\n错误: 未知的对比度模式: {contrastMode}")
                sys.exit()
            
            # 存储数据
            signal_data[i] = np.mean(signal_counts)
            reference_data[i] = np.mean(reference_counts)
            contrast_data[i] = contrast
            
            # 按间隔保存数据
            if (i + 1) % saveSpacing_inScanPts == 0:
                save_data(dataFileName, freq_steps, signal_data, reference_data, contrast_data)
        
        # 按平均间隔保存数据
        if (avg + 1) % saveSpacing_inAverages == 0:
            save_data(dataFileName, freq_steps, signal_data, reference_data, contrast_data)
            save_params(paramFileName)
    
    # 实验结束
    print("\n=== 实验完成 ===")
    
    # 最终保存数据
    save_data(dataFileName, freq_steps, signal_data, reference_data, contrast_data)
    save_params(paramFileName)
    
    # 禁用RF输出
    disableSRS_RFOutput(srs)
    
    print("\n✅ SER实验完成，数据已保存")

# 保存数据函数
def save_data(filename, frequencies, signal, reference, contrast):
    """保存实验数据到文件"""
    # 确保保存目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 保存数据
    with open(filename, 'w') as f:
        f.write("Frequency (Hz)\tSignal Counts\tReference Counts\tContrast\n")
        for freq, sig, ref, cont in zip(frequencies, signal, reference, contrast):
            f.write(f"{freq}\t{sig}\t{ref}\t{cont}\n")
    
    # print(f"✅ 数据已保存到: {filename}")

# 保存参数函数
def save_params(filename):
    """保存实验参数到文件"""
    # 确保保存目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 保存参数
    with open(filename, 'w') as f:
        for param in expParamList:
            if isinstance(param, str) and param.endswith(':'):
                f.write(f"{param}\n")
            else:
                f.write(f"{param}\n")
    
    print(f"✅ 参数已保存到: {filename}")

if __name__ == "__main__":
    main()
