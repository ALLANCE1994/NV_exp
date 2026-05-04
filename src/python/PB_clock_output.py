#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PB_clock_output.py

控制PulseBlaster脉冲板在通道7上持续输出10MHz的时钟信号
"""

from spinapi import *
import sys
import time
from connectionConfig import PBclk

# 定义通道7的位掩码（通道7对应位6）
CHANNEL_7_MASK = 0x80  # 二进制 10000000
print(f"通道7的位掩码: 0x{CHANNEL_7_MASK:02X}")

# 错误处理函数
def errorCatcher(statusVar):
    if statusVar < 0:
        print('错误:', pb_get_error())
        sys.exit()

# 配置PulseBlaster
def configurePB():
    print("正在初始化PulseBlaster...")
    pb_set_debug(1)
    status = pb_init()
    errorCatcher(status)
    print(f"PulseBlaster初始化成功，核心时钟设置为 {PBclk} MHz")
    # 注意：这里PBclk已经是MHz单位
    pb_core_clock(PBclk)
    return 0

# 编程脉冲序列
def programClockOutput():
    # 配置PulseBlaster
    configurePB()
    
    # 开始编程
    print("开始编程脉冲序列...")
    status = pb_start_programming(PULSE_PROGRAM)
    errorCatcher(status)
    
    # 计算10MHz时钟的周期（纳秒）
    # 10MHz = 10,000,000 Hz，周期为 100 ns
    # 注意：spinapi库使用纳秒作为时间单位
    clock_frequency = 1e6  # 10 MHz
    clock_period = int(1e9 / clock_frequency)  # 计算周期，单位为纳秒
    print(f"10MHz时钟频率: {clock_frequency / 1e6} MHz")
    print(f"计算得到的时钟周期: {clock_period} ns")
    
    # 计算半周期
    half_period = clock_period // 2
    print(f"半周期: {half_period} ns")
    
    # 验证核心时钟设置
    print(f"PulseBlaster核心时钟: {PBclk} MHz")
    print(f"最小时间分辨率: {1000 / PBclk} ns")
    
    # 确保半周期是最小时间分辨率的整数倍
    min_resolution = 1000 / PBclk
    if half_period % min_resolution != 0:
        # 调整半周期到最小分辨率的整数倍
        half_period = int(round(half_period / min_resolution) * min_resolution)
        print(f"调整后的半周期: {half_period} ns")
    
    # 编程两个指令，交替打开和关闭通道7
    # 第一个指令：通道7打开，持续半周期
    print(f"编程指令1：通道7打开，持续 {half_period} ns")
    start = pb_inst_pbonly(CHANNEL_7_MASK, CONTINUE, 0, half_period)
    errorCatcher(start)
    print(f"指令1地址: {start}")
    
    # 第二个指令：通道7关闭，持续半周期，然后分支回第一个指令
    print(f"编程指令2：通道7关闭，持续 {half_period} ns，分支到指令1")
    status = pb_inst_pbonly(0, BRANCH, start, half_period)
    errorCatcher(status)
    
    # 停止编程
    print("停止编程...")
    status = pb_stop_programming()
    errorCatcher(status)
    
    # 启动脉冲输出
    print("启动脉冲输出...")
    status = pb_start()
    errorCatcher(status)
    
    print("✅ PulseBlaster已启动，通道7正在输出10MHz时钟信号")
    print("输出电压范围：0-2V")
    print("按 Ctrl+C 停止输出")
    print("请检查示波器通道7的连接和设置")

# 停止脉冲输出
def stopClockOutput():
    try:
        print("停止脉冲输出...")
        pb_stop()
        pb_close()
        print("✅ 脉冲输出已停止")
    except Exception as e:
        print(f"警告：停止脉冲输出时出错: {e}")

if __name__ == "__main__":
    try:
        # 编程并启动时钟输出
        programClockOutput()
        
        # 保持程序运行，直到用户按Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，正在停止时钟输出...")
        stopClockOutput()
        sys.exit()
    except Exception as e:
        print(f"错误: {e}")
        stopClockOutput()
        sys.exit()
