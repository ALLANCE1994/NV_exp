#!/usr/bin/env python3
# B210_SRScontrol.py
# 功能：B210 设备控制脚本，与 SRS SG384 控制脚本功能一致
# 输出通道：TX1

import os
import sys
import uhd
import numpy as np

# 频率单位定义
Hz = 1
kHz = 1e3
MHz = 1e6
GHz = 1e9

# 全局变量
usrp = None
tx_streamer = None
samples = None
metadata = None
buffer_size = 32768  # 缓冲区大小
is_rf_enabled = False  # RF 输出状态

##-------------------- 函数定义--------------------
def initSRS(GPIBaddr, modelName):
    # initSRS: 初始化 B210 设备
    # 注意：B210 不使用 GPIB 地址，这里保留参数以保持与 SRS 接口一致
    # 参数: - GPIBaddr: 整数，SRS 的 GPIB 地址（B210 忽略此参数）
    #       - modelName: 字符串，描述 SRS 型号（B210 忽略此参数）
    
    global usrp, tx_streamer, samples, metadata
    
    print("初始化 B210 设备...")
    
    try:
        # 创建 USRP 对象
        usrp = uhd.usrp.MultiUSRP()
        
        # 设置默认参数
        rate = 16000000  # 16 MHz 采样率
        gain = 50  # 50 dB 增益
        freq = 2870000000  # 2.87 GHz 频率
        
        # 配置参数
        usrp.set_tx_rate(rate, 0)
        usrp.set_tx_gain(gain, 0)
        usrp.set_tx_freq(uhd.types.TuneRequest(freq), 0)
        
        # 创建流
        stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
        tx_streamer = usrp.get_tx_stream(stream_args)
        
        # 准备数据
        samples = np.ones(buffer_size, dtype=np.complex64)
        metadata = uhd.types.TXMetadata()
        
        print("✅ B210 设备初始化成功")
        return usrp
        
    except Exception as excpt:
        print('错误: 无法初始化 B210 设备。异常详情:', type(excpt).__name__,'.', excpt)
        sys.exit()

def SRSerrCheck(SRS):
    # SRSerrCheck: 检查 B210 设备错误
    # 注意：B210 没有与 SRS 类似的错误检查机制，这里保留函数以保持接口一致
    pass

def enableSRS_RFOutput(SRS):
    # enableSRS_RFOutput: 启用 B210 的 RF 输出
    global is_rf_enabled
    
    if not is_rf_enabled:
        print("✅ 启用 B210 RF 输出")
        is_rf_enabled = True
        
        # 开始发送数据
        global tx_streamer, samples, metadata
        if tx_streamer is not None and samples is not None and metadata is not None:
            # 持续发送数据
            def send_data():
                while is_rf_enabled:
                    tx_streamer.send(samples, metadata)
            
            # 在后台线程中发送数据
            import threading
            threading.Thread(target=send_data, daemon=True).start()

def disableSRS_RFOutput(SRS):
    # disableSRS_RFOutput: 禁用 B210 的 RF 输出
    global is_rf_enabled
    
    if is_rf_enabled:
        print("❌ 禁用 B210 RF 输出")
        is_rf_enabled = False

def setSRS_RFAmplitude(SRS, RFamplitude, units='dBm'):
    # setSRS_RFAmplitude: 设置 B210 的 RF 幅度（增益）
    # 注意：B210 使用 dB 作为增益单位，这里假设 units 参数为 'dBm' 时直接使用值作为增益
    global usrp
    
    if usrp:
        usrp.set_tx_gain(RFamplitude, 0)
        print(f"✅ 设置 B210 增益为 {RFamplitude} {units}")
    else:
        print("错误: B210 设备未初始化")
        sys.exit()

def setSRS_Freq(SRS, freq, units='Hz'):
    # setSRS_Freq: 设置 B210 的输出频率
    # 参数: - freq: 浮点数，设置频率
    #       - units: 字符串，描述单位（例如 'MHz'）
    global usrp
    
    # 计算实际频率（转换为 Hz）
    if units == 'Hz':
        actual_freq = freq
    elif units == 'kHz':
        actual_freq = freq * kHz
    elif units == 'MHz':
        actual_freq = freq * MHz
    elif units == 'GHz':
        actual_freq = freq * GHz
    else:
        print(f"错误: 不支持的频率单位: {units}")
        sys.exit()
    
    if usrp:
        usrp.set_tx_freq(uhd.types.TuneRequest(actual_freq), 0)
        print(f"✅ 设置 B210 频率为 {freq} {units} ({actual_freq} Hz)")
    else:
        print("错误: B210 设备未初始化")
        sys.exit()

def setupSRSmodulation(SRS, sequence):
    # setupSRSmodulation: 为不同序列设置调制模式
    # 注意：B210 不支持 IQ 调制，这里仅打印信息
    if sequence in ['ESRseq', 'RabiSeq', 'T1seq']:
        disableModulation(SRS)
    elif sequence in ['T2seq','XY8seq','correlSpecSeq']:
        enableIQmodulation(SRS)
    else:
        print('错误: 未识别的序列名称传递给 setupSRSmodulation。')
        sys.exit()

def enableIQmodulation(SRS):
    # enableIQmodulation: 启用 IQ 调制
    # 注意：B210 不支持 IQ 调制，这里仅打印信息
    print("⚠️  B210 不支持 IQ 调制功能")

def disableModulation(SRS):
    # disableModulation: 禁用调制
    # 注意：B210 不支持调制功能，这里仅打印信息
    print("⚠️  B210 不支持调制功能")

def queryModulationStatus(SRS):
    # queryModulationStatus: 查询调制状态
    # 注意：B210 不支持调制功能，这里返回默认状态
    print("⚠️  B210 不支持调制功能")
    return '0'  # 返回 0 表示调制关闭

# 测试函数
def testB210Control():
    print("==================================")
    print(" B210 SRS 控制测试")
    print("==================================")
    
    # 初始化设备
    srs = initSRS(27, 'SG384')
    
    # 设置频率
    setSRS_Freq(srs, 2.87, 'GHz')
    
    # 设置增益
    setSRS_RFAmplitude(srs, 50, 'dBm')
    
    # 启用 RF 输出
    enableSRS_RFOutput(srs)
    
    print("\n按 Enter 键继续...")
    input()
    
    # 禁用 RF 输出
    disableSRS_RFOutput(srs)
    
    print("\n测试完成")

if __name__ == "__main__":
    testB210Control()
