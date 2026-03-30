# 模拟版本的PB控制.py
# 用于在没有实际PulseBlaster硬件的情况下测试qdSpectro项目

import sys
import os

# 添加父目录到Python路径，以便找到序列Control模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sequenceControl as seqCtl

def pb_init():
    """模拟初始化PulseBlaster"""
    print('Initializing mock PulseBlaster...')

def pb_start():
    """模拟启动PulseBlaster"""
    print('Starting mock PulseBlaster...')

def pb_stop():
    """模拟停止PulseBlaster"""
    print('Stopping mock PulseBlaster...')

def programPB(sequence, sequenceArgs):
    """模拟编程序列到PulseBlaster"""
    print(f'Programming mock PulseBlaster sequence...')
    # 调用序列Control来生成序列
    channels = seqCtl.makeSequence(sequence, sequenceArgs)
    return []  # 返回空列表模拟指令数组