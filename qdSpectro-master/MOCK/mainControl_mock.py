# 模拟版本的主控制程序
# 用于在没有实际硬件的情况下测试qdSpectro项目

import sys
import numpy as np
import matplotlib.pyplot as plt
import time
import os

# 添加当前目录到Python路径，以便导入模拟模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入模拟版本的模块
import SRScontrol_mock as SRSctl
import DAQcontrol_mock as DAQctl
import PBcontrol_mock as PBctl

# 导入配置文件
try:
    expConfigFile = sys.argv[1]
    exec('import ' + expConfigFile + ' as expCfg')
except IndexError:
    print('Error: No experiment config file provided. Please provide the name of the experiment config file (e.g. "ESRconfig") as a command line argument.')
    sys.exit()
except ImportError:
    print('Error: Could not import experiment config file. Please check the file name and ensure it is in the same directory as mainControl.py.')
    sys.exit()

def runExperiment(expConfigFile):
    print('Running experiment with config file:', expConfigFile)
    
    # 模拟初始化SRS信号发生器
    print('Initializing SRS SG386 at GPIB address 27')
    SRS = SRSctl.initSRS(27, 'SG386')
    
    # 模拟设置SRS参数
    print('Setting SRS RF amplitude to', expCfg.microwavePower, 'dBm')
    SRSctl.setSRS_RFAmplitude(SRS, expCfg.microwavePower)
    
    # 模拟设置SRS调制
    print('Setting up SRS modulation for sequence:', expCfg.sequence)
    SRSctl.setupSRSmodulation(SRS, expCfg.sequence)
    
    # 模拟配置DAQ
    print('Configuring DAQ...')
    readTask = DAQctl.configureDAQ(expCfg.Nsamples)
    
    # 模拟初始化PulseBlaster
    print('Initializing PulseBlaster...')
    PBctl.pb_init()
    
    # 准备频率扫描点
    if hasattr(expCfg, 'scannedParam'):
        frequencies = expCfg.scannedParam
        print('Generated', len(frequencies), 'frequency scan points from', frequencies[0], 'Hz to', frequencies[-1], 'Hz')
    elif hasattr(expCfg, 'startFreq') and hasattr(expCfg, 'endFreq') and hasattr(expCfg, 'N_scanPts'):
        # 对于ESR实验，使用startFreq、endFreq和N_scanPts生成频率扫描点
        frequencies = np.linspace(expCfg.startFreq, expCfg.endFreq, expCfg.N_scanPts)
        print('Generated', len(frequencies), 'frequency scan points from', frequencies[0], 'Hz to', frequencies[-1], 'Hz')
    elif hasattr(expCfg, 'microwaveFrequency'):
        # 对于其他实验，使用microwaveFrequency作为固定频率
        frequencies = [expCfg.microwaveFrequency]
        print('Using fixed frequency from config:', frequencies[0], 'Hz')
    else:
        # 如果没有相关属性，使用默认频率
        frequencies = [2.7e9]
        print('Using default frequency:', frequencies[0], 'Hz')
    
    # 实现频率扫描和多次平均
    all_data = []
    for avg in range(expCfg.Navg):
        print(f'\n--- Average run {avg+1}/{expCfg.Navg} ---')
        
        # 随机化频率顺序（如果启用）
        if expCfg.randomize and avg > 0:
            np.random.shuffle(frequencies)
            print('Randomized frequency scan order')
        
        run_data = []
        for i, frequency in enumerate(frequencies):
            print(f'\nProcessing frequency {i+1}/{len(frequencies)}: {frequency} Hz')
            
            # 模拟设置SRS频率
            print('Setting SRS frequency to', frequency, 'Hz')
            SRSctl.setSRS_Freq(SRS, frequency)
            
            # 模拟启用SRS RF输出
            print('Enabling SRS RF output')
            SRSctl.enableSRS_RFOutput(SRS)
            
            # 模拟编程PulseBlaster
            print('Programming PulseBlaster with sequence:', expCfg.sequence)
            # 根据序列类型准备参数
            if expCfg.sequence == 'RabiSeq':
                # Rabi序列需要三个参数：t_uW, t_AOM, t_readoutDelay
                # 使用默认的t_uW值
                t_uW = 100  # 默认微波脉冲长度
                sequence_args = [t_uW] + expCfg.sequenceArgs
            elif expCfg.sequence == 'T1seq':
                # T1序列需要四个参数：t_延迟, t_AOM, t_readoutDelay, t_pi
                # 使用默认的t_延迟值
                t_delay = 1000  # 默认延迟时间
                sequence_args = [t_delay] + expCfg.sequenceArgs
            elif expCfg.sequence == 'T2seq':
                # T2序列需要多个参数：t_延迟, t_AOM, t_readoutDelay, t_pi, IQpadding, numberOfPiPulses
                # 使用默认的t_延迟值
                t_delay = 1000  # 默认延迟时间
                sequence_args = [t_delay] + expCfg.sequenceArgs
            elif expCfg.sequence == 'XY8seq':
                # XY8序列需要多个参数：t_延迟, t_AOM, t_readoutDelay, t_pi, IQpadding, numberOfRepeats
                # 使用默认值
                t_delay = 1000  # 默认延迟时间
                t_pi = 50  # 默认pi脉冲长度
                IQpadding = 10  # 默认IQ padding
                numberOfRepeats = 1  # 默认重复次数
                sequence_args = [t_delay] + expCfg.sequenceArgs + [t_pi, IQpadding, numberOfRepeats]
            elif expCfg.sequence == 'correlSpecSeq':
                # 相关光谱序列需要多个参数：t_延迟_betweenXY8seqs, t_延迟, t_AOM, t_readoutDelay, t_pi, IQpadding, numberOfRepeats
                # 使用默认值
                t_delay_betweenXY8seqs = 5000  # 默认XY8序列间延迟
                t_delay = 1000  # 默认延迟时间
                t_pi = 50  # 默认pi脉冲长度
                IQpadding = 10  # 默认IQ padding
                numberOfRepeats = 1  # 默认重复次数
                sequence_args = [t_delay_betweenXY8seqs, t_delay] + expCfg.sequenceArgs + [t_pi, IQpadding, numberOfRepeats]
            else:
                sequence_args = expCfg.sequenceArgs
            instructionArray = PBctl.programPB(expCfg.sequence, sequence_args)
            
            # 模拟启动PulseBlaster
            print('Starting PulseBlaster...')
            PBctl.pb_start()
            
            # 模拟读取DAQ数据
            print('Reading data from DAQ...')
            counts = DAQctl.readDAQ(readTask, expCfg.Nsamples, expCfg.DAQtimeout)
            
            # 模拟停止PulseBlaster
            print('Stopping PulseBlaster...')
            PBctl.pb_stop()
            
            # 模拟禁用SRS RF输出
            print('Disabling SRS RF output...')
            SRSctl.disableSRS_RFOutput(SRS)
            
            # 保存数据
            run_data.append(counts)
            
            # 按间隔保存数据（首次扫描）
            if avg == 0 and (i+1) % expCfg.saveSpacing_inScanPts == 0:
                print(f'Saving data at scan point {i+1}...')
                # 这里可以添加实际的数据保存逻辑
        
        # 保存本次平均运行的数据
        all_data.append(run_data)
        
        # 按间隔保存数据（平均运行）
        if (avg+1) % expCfg.saveSpacing_inAverages == 0:
            print(f'Saving data after {avg+1} average runs...')
            # 这里可以添加实际的数据保存逻辑
    
    # 模拟关闭DAQ任务
    print('\nClosing DAQ task...')
    DAQctl.closeDAQTask(readTask)
    
    # 模拟数据处理
    print('Processing data...')
    time.sleep(1)  # 模拟处理时间
    
    # 计算平均数据
    print('Calculating average data...')
    all_data = np.array(all_data)
    avg_data = np.mean(all_data, axis=0)
    
    # 模拟数据可视化
    print('Plotting data...')
    plt.figure(figsize=(10, 6))
    
    # 绘制原始数据
    plt.subplot(2, 1, 1)
    for i, run in enumerate(all_data):
        plt.plot(frequencies, np.mean(run, axis=1), label=f'Run {i+1}')
    plt.title('Raw Data from Each Run')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Intensity')
    plt.legend()
    
    # 绘制平均数据
    plt.subplot(2, 1, 2)
    plt.plot(frequencies, np.mean(avg_data, axis=1), 'r-', linewidth=2)
    plt.title('Average Data')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Intensity')
    
    plt.tight_layout()
    plt.show()
    
    print('Experiment completed successfully!')

if __name__ == '__main__':
    runExperiment(expConfigFile)