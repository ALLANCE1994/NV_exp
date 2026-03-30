# 模拟版本的DAQ控制.py
# 用于在没有实际DAQ硬件的情况下测试qdSpectro项目

import numpy as np

def configureDAQ(Nsamples):
    """模拟配置DAQ"""
    print(f'Configuring mock DAQ with {Nsamples} samples...')
    return {'Nsamples': Nsamples}

def readDAQ(readTask, Nsamples, timeout):
    """模拟从DAQ读取数据"""
    print('Reading data from DAQ...')
    # 生成随机数据模拟DAQ读数
    return np.random.rand(Nsamples) * 5.0  # 模拟0-5V的读数

def closeDAQTask(readTask):
    """模拟关闭DAQ任务"""
    print('Closing DAQ task...')