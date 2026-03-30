# 模拟版本的SRS控制.py
# 用于在没有实际SRS硬件的情况下测试qdSpectro项目

import sys

def initSRS(GPIBaddr, modelName):
    """模拟初始化SRS信号发生器"""
    print(f'Initializing mock SRS {modelName} at GPIB address {GPIBaddr}')
    return {'address': GPIBaddr, 'model': modelName}

def setSRS_RFAmplitude(SRS, amplitude):
    """模拟设置SRS RF幅度"""
    print(f'Setting SRS RF amplitude to {amplitude} dBm')

def setupSRSmodulation(SRS, sequence):
    """模拟设置SRS调制"""
    print(f'Setting up SRS modulation for sequence: {sequence}')

def setSRS_Freq(SRS, frequency):
    """模拟设置SRS频率"""
    print(f'Setting SRS frequency to {frequency} Hz')

def enableSRS_RFOutput(SRS):
    """模拟启用SRS RF输出"""
    print('Enabling SRS RF output')

def disableSRS_RFOutput(SRS):
    """模拟禁用SRS RF输出"""
    print('Disabling SRS RF output')

def SRSerrCheck(SRS):
    """模拟SRS错误检查"""
    pass