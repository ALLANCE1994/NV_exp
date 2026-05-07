# DAQ 控制
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明和本许可声明应包含在本软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不提供任何形式的担保，明示或暗示，
# 包括但不限于适销性、特定用途适用性和非侵权性的担保。
# 在任何情况下，作者或版权持有人均不对任何索赔、损害或其他责任负责，
# 无论是在合同诉讼、侵权行为还是其他方面，由本软件或本软件的使用或
# 其他交易引起的或与之相关的。
import nidaqmx
import os
from  nidaqmx.constants import *
from connectionConfig import *
import sys

def configureDAQ(Nsamples):
	try:
		print(f"正在配置DAQ，样本数: {Nsamples}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"DAQ_MaxSamplingRate: {DAQ_MaxSamplingRate}")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		# 创建并配置模拟输入电压任务
		NsampsPerDAQread=2*Nsamples
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用Diff（差分）终端配置，适用于MyDAQ
		channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.DIFF,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		print("添加模拟输入通道成功")
		
		# 配置采样时钟（使用内部时钟源，myDAQ不支持外部时钟）
		readTask.timing.cfg_samp_clk_timing(DAQ_MaxSamplingRate, "", Edge.RISING, AcquisitionType.FINITE, NsampsPerDAQread)
		print("配置采样时钟（内部）成功")
		
		print("DAQ配置成功")
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

def configureDAQContinuous(buffer_size=10000):
	"""配置DAQ为连续采样模式，用于长时间采集
	
	参数:
		buffer_size: 缓冲区大小，每次读取的样本数
	
	返回:
		配置好的DAQ任务对象，如果配置失败返回None
	"""
	try:
		print(f"正在配置DAQ为连续采样模式，缓冲区大小: {buffer_size}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"DAQ_MaxSamplingRate: {DAQ_MaxSamplingRate}")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用Diff（差分）终端配置，适用于MyDAQ
		channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.DIFF,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		print("添加模拟输入通道成功")
		
		# 配置采样时钟为连续采样模式
		readTask.timing.cfg_samp_clk_timing(DAQ_MaxSamplingRate, "", Edge.RISING, AcquisitionType.CONTINUOUS, buffer_size)
		print("配置采样时钟为连续模式成功")
		
		print("DAQ连续采样模式配置成功")
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		if 'readTask' in locals():
			closeDAQTask(readTask)
		return None
	return readTask

def readDAQContinuous(task, total_samples, buffer_size=10000, timeout=10, num_averages=1000):
	"""从连续采样模式的DAQ中分批读取数据，并实时计算平均值
	
	参数:
		task: DAQ任务对象
		total_samples: 需要读取的总样本数
		buffer_size: 每次读取的缓冲区大小
		timeout: 超时时间（秒）
		num_averages: 需要计算的平均个数（即Nsamples）
	
	返回:
		读取到的数据数组（长度为 num_averages * 2，用于信号和背景交替）
	"""
	try:
		import numpy as np
		
		# 计算每个平均值需要的样本数
		samples_per_average = total_samples // num_averages
		
		print(f"    连续采样模式：总样本数={total_samples}, 平均个数={num_averages}, 每平均样本数={samples_per_average}")
		
		# 预分配结果数组（存储平均值）
		result = np.zeros(num_averages, dtype=np.float64)
		average_index = 0
		current_buffer = []
		
		# 开始任务
		task.start()
		
		remaining_samples = total_samples
		
		while remaining_samples > 0:
			# 计算本次读取的样本数
			read_size = min(buffer_size, remaining_samples)
			
			# 读取数据
			data = task.read(read_size, timeout)
			
			# 将数据添加到当前缓冲区
			current_buffer.extend(data)
			remaining_samples -= len(data)
			
			# 当缓冲区足够计算一个平均值时
			while len(current_buffer) >= samples_per_average and average_index < num_averages:
				# 取 samples_per_average 个样本计算平均值
				average_data = current_buffer[:samples_per_average]
				result[average_index] = np.mean(average_data)
				average_index += 1
				
				# 移除已处理的数据
				current_buffer = current_buffer[samples_per_average:]
			
			# 打印进度
			progress = (total_samples - remaining_samples) / total_samples * 100
			print(f"    DAQ读取进度: {progress:.1f}% ({total_samples - remaining_samples}/{total_samples})", end='\r')
		
		print()  # 换行
		
		# 如果还有剩余数据，计算最后一个平均值
		if len(current_buffer) > 0 and average_index < num_averages:
			result[average_index] = np.mean(current_buffer)
			average_index += 1
		
		# 停止任务
		task.stop()
		
		return result
	except Exception as excpt:
		print('错误：无法读取 DAQ。请检查您的 DAQ 连接。异常详情：', type(excpt).__name__,'.',excpt)
		if 'task' in locals():
			task.stop()
		sys.exit()
	return None

def readDAQ(task,N,timeout):
	try:
		counts = task.read(N,timeout)
	except Exception as excpt:
		print('错误：无法读取 DAQ。请检查您的 DAQ 连接。异常详情：', type(excpt).__name__,'.',excpt)
		sys.exit()
	return counts
	

def closeDAQTask(task):
	task.close()