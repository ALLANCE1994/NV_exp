# DAQ 控制 - NI USB-7855 版本
# 支持外部采样时钟和开始触发

import nidaqmx
import os
from nidaqmx.constants import *
from connectionConfig import *
import sys

def configureDAQ(Nsamples):
	"""配置NI USB-7855 DAQ
	
	参数:
		Nsamples: 每个扫描点的样本数
	
	返回:
		配置好的DAQ任务
	
	注意：NI USB-7855支持外部采样时钟和触发，比MyDAQ更适合高精度测量
	"""
	try:
		# 计算每个扫描点的总样本数（信号+背景）
		NsampsPerDAQread = 2 * Nsamples
		
		print(f"正在配置NI USB-7855 DAQ，样本数: {Nsamples}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"DAQ_SampleClk: {DAQ_SampleClk}")
		print(f"DAQ_StartTrig: {DAQ_StartTrig}")
		print(f"采样率: {DAQ_MaxSamplingRate} Hz")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		# 创建并配置模拟输入电压任务
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用RSE（参考单端）终端配置
		channel = readTask.ai_channels.add_ai_voltage_chan(
			DAQ_APDInput, "", 
			TerminalConfiguration.RSE, 
			minVoltage, maxVoltage, 
			VoltageUnits.VOLTS
		)
		print("添加模拟输入通道成功")
		
		# 配置外部采样时钟
		# DAQ_SampleClk 是PB_DAQ通道，用于定时数据采集
		readTask.timing.cfg_samp_clk_timing(
			DAQ_MaxSamplingRate,		# 最大采样率
			DAQ_SampleClk,				# 外部采样时钟源
			Edge.RISING,				# 上升沿触发
			AcquisitionType.FINITE,		# 有限采集
			NsampsPerDAQread			# 样本数
		)
		print("配置采样时钟成功（外部时钟）")
		
		# 配置转换时钟
		readTask.timing.ai_conv_src = DAQ_SampleClk
		readTask.timing.ai_conv_active_edge = Edge.RISING
		print("配置转换时钟成功")
		
		# 配置开始触发
		# DAQ_StartTrig 是PB_STARTtrig通道，用于触发采集开始
		readStartTrig = readTask.triggers.start_trigger
		readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)
		print("配置开始触发成功（外部触发）")
		
		print("NI USB-7855 DAQ配置成功")
		
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		print(f'当前工作目录: {os.getcwd()}')
		print(f'DAQ_APDInput: {DAQ_APDInput}')
		if 'readTask' in locals():
			closeDAQTask(readTask)
		return None
		
	return readTask

def configureDAQforRabi(Nsamples, t_AOM, t_readoutDelay, t_wait, t_uW):
	"""为Rabi实验配置NI USB-7855 DAQ
	
	参数:
		Nsamples: 每个扫描点的样本数
		t_AOM: AOM脉冲持续时间（纳秒）
		t_readoutDelay: 读取延迟时间（纳秒）
		t_wait: 等待稳定时间（纳秒）
		t_uW: 微波脉冲持续时间（纳秒）
	
	返回:
		配置好的DAQ任务
	
	Rabi实验的脉冲序列包含两个半周期：
	1. 信号半周期（有微波）
	2. 参考半周期（无微波）
	"""
	try:
		NsampsPerDAQread = 2 * Nsamples
		
		print(f"为Rabi实验配置NI USB-7855 DAQ，样本数: {Nsamples}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		# 创建并配置模拟输入电压任务
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用RSE（参考单端）终端配置
		channel = readTask.ai_channels.add_ai_voltage_chan(
			DAQ_APDInput, "", 
			TerminalConfiguration.RSE, 
			minVoltage, maxVoltage, 
			VoltageUnits.VOLTS
		)
		print("添加模拟输入通道成功")
		
		# 配置外部采样时钟
		readTask.timing.cfg_samp_clk_timing(
			DAQ_MaxSamplingRate,
			DAQ_SampleClk,
			Edge.RISING,
			AcquisitionType.FINITE,
			NsampsPerDAQread
		)
		print("配置采样时钟成功（外部时钟）")
		
		# 配置转换时钟
		readTask.timing.ai_conv_src = DAQ_SampleClk
		readTask.timing.ai_conv_active_edge = Edge.RISING
		
		# 配置开始触发
		readStartTrig = readTask.triggers.start_trigger
		readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)
		print("配置开始触发成功（外部触发）")
		
		print("Rabi实验 NI USB-7855 DAQ配置成功")
		
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		if 'readTask' in locals():
			closeDAQTask(readTask)
		return None
		
	return readTask

def configureDAQbyTime(acquisitionTime_ns, Nsamples):
	"""根据采集时间和样本数配置NI USB-7855 DAQ
	
	参数:
		acquisitionTime_ns: 每个样本组的采集时间（纳秒）
		Nsamples: 样本组数
	
	返回:
		配置好的DAQ任务、实际样本数和初始延迟时间（秒）
	
	注意：NI USB-7855使用外部时钟，此函数保留接口兼容性
	"""
	try:
		NsampsPerDAQread = 2 * Nsamples
		
		print(f"根据时间和样本数配置NI USB-7855 DAQ")
		print(f"样本组数: {Nsamples}")
		print(f"总样本数: {NsampsPerDAQread}")
		
		# 创建并配置模拟输入电压任务
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用RSE（参考单端）终端配置
		channel = readTask.ai_channels.add_ai_voltage_chan(
			DAQ_APDInput, "", 
			TerminalConfiguration.RSE, 
			minVoltage, maxVoltage, 
			VoltageUnits.VOLTS
		)
		print("添加模拟输入通道成功")
		
		# 配置外部采样时钟
		readTask.timing.cfg_samp_clk_timing(
			DAQ_MaxSamplingRate,
			DAQ_SampleClk,
			Edge.RISING,
			AcquisitionType.FINITE,
			NsampsPerDAQread
		)
		print("配置采样时钟成功（外部时钟）")
		
		# 配置转换时钟
		readTask.timing.ai_conv_src = DAQ_SampleClk
		readTask.timing.ai_conv_active_edge = Edge.RISING
		
		# 配置开始触发
		readStartTrig = readTask.triggers.start_trigger
		readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)
		print("配置开始触发成功（外部触发）")
		
		print("NI USB-7855 DAQ时间配置成功")
		
		# NI USB-7855使用外部时钟，不需要软件延迟
		return readTask, 0, 0
		
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		if 'readTask' in locals():
			closeDAQTask(readTask)
		return None, 0, 0

def readDAQ(task, N, timeout):
	"""读取DAQ数据
	
	参数:
		task: DAQ任务对象
		N: 要读取的样本数
		timeout: 超时时间（秒）
	
	返回:
		读取的计数数据
	"""
	try:
		counts = task.read(N, timeout)
	except Exception as excpt:
		print('错误：无法读取 DAQ。请检查您的 DAQ 连接。异常详情：', type(excpt).__name__,'.',excpt)
		sys.exit()
	return counts

def closeDAQTask(task):
	"""关闭DAQ任务"""
	task.close()