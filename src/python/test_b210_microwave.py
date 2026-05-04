#!/usr/bin/env python3
# test_b210_microwave.py
# 功能：单独测试 B210 输出微波

import os
import sys
import time

# 添加 UHD 的 bin 目录到系统 PATH 环境变量
uhd_bin_path = r"C:\Program Files\UHD\bin"
os.environ["PATH"] = uhd_bin_path + ";" + os.environ["PATH"]

# 添加 UHD 的 bin 目录到 DLL 搜索路径
os.add_dll_directory(uhd_bin_path)

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
def initB210():
    # initB210: 初始化 B210 设备
    
    global usrp, tx_streamer, samples, metadata
    
    print("初始化 B210 设备...")
    
    try:
        print("正在创建 USRP 对象...")
        # 创建 USRP 对象
        usrp = uhd.usrp.MultiUSRP()
        print("USRP 对象创建成功")
        
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

def setFrequency(freq, units='Hz'):
    # setFrequency: 设置 B210 的输出频率
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

def setGain(gain, units='dB'):
    # setGain: 设置 B210 的增益
    # 参数: - gain: 整数，设置增益（0-70 dB）
    #       - units: 字符串，描述单位（默认为 'dB'）
    global usrp
    
    if usrp:
        usrp.set_tx_gain(gain, 0)
        print(f"✅ 设置 B210 增益为 {gain} {units}")
    else:
        print("错误: B210 设备未初始化")
        sys.exit()

def enableRFOutput():
    # enableRFOutput: 启用 B210 的 RF 输出
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

def disableRFOutput():
    # disableRFOutput: 禁用 B210 的 RF 输出
    global is_rf_enabled
    
    if is_rf_enabled:
        print("❌ 禁用 B210 RF 输出")
        is_rf_enabled = False

def main():
    print("==================================")
    print(" B210 微波输出测试程序")
    print("==================================")
    
    # 初始化设备
    initB210()
    
    # 设置频率
    freq = float(input("请输入输出频率 (GHz): "))
    setFrequency(freq, 'GHz')
    
    # 设置增益
    gain = int(input("请输入输出增益 (0-70 dB): "))
    setGain(gain)
    
    # 启用 RF 输出
    enableRFOutput()
    
    print("\nB210 正在输出微波...")
    print("按 Enter 键停止输出...")
    input()
    
    # 禁用 RF 输出
    disableRFOutput()
    
    print("\n测试完成")

if __name__ == "__main__":
    main()
