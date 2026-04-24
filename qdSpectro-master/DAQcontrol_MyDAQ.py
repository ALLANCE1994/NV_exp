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
from spinapi import ms,us,ns

# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 给出：
t_min = 1e3/PBclk # 单位为纳秒

def configureDAQ(Nsamples, t_duration_us):
	try:
		# 计算采样率：每个t_duration周期采集一个点
		# t_duration_us 单位为微秒
		sampling_rate = int(1e6 / t_duration_us)
		print(f"正在配置DAQ，样本数: {Nsamples}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"采样率: {sampling_rate} Hz")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		# 计算t_duration（纳秒）
		t_duration_ns = t_duration_us * 1000
		
		# 计算每个完整周期的时间（2*t_duration）
		t_full_cycle_ns = 2 * t_duration_ns
		
		# 计算总采集时间
		totalAcquisitionTime_sec = (t_full_cycle_ns * Nsamples) / 1e9
		
		# 创建并配置模拟输入电压任务
		NsampsPerDAQread=2*Nsamples
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 原始配置：使用RSE（参考单端）终端配置
		# channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.RSE,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		# 修改后：使用Diff（差分）终端配置，适用于MyDAQ
		channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.DIFF,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		print("添加模拟输入通道成功")
		
		# 配置采样时钟（使用内部时钟源，因为MyDAQ不支持外部时钟路由）
		readTask.timing.cfg_samp_clk_timing(sampling_rate, "", Edge.RISING, AcquisitionType.FINITE, NsampsPerDAQread)
		print("配置采样时钟成功")
		
		# 计算采样间隔（纳秒）
		sample_interval_ns = 1e9 / sampling_rate
		
		# 打印采样时序信息
		print(f"t_duration: {t_duration_us} μs")
		print(f"每个完整周期时间: {t_full_cycle_ns} ns")
		print(f"采样间隔: {sample_interval_ns} ns")
		print(f"总采集时间: {totalAcquisitionTime_sec} s")
		print("DAQ配置成功")
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		print(f'当前工作目录: {os.getcwd()}')
		print(f'DAQ_APDInput: {DAQ_APDInput}')
		# 修复：使用正确的变量名readTask
		if 'readTask' in locals():
			closeDAQTask(readTask)
		# 不要直接退出，而是返回None，让调用者处理错误
		return None
	return readTask

def configureDAQforRabi(Nsamples, t_AOM, t_readoutDelay, t_wait, t_uW):
	"""为Rabi实验配置DAQ
	
	参数:
		Nsamples: 每个扫描点的样本数
		t_AOM: AOM脉冲持续时间（纳秒）
		t_readoutDelay: 读取延迟时间（纳秒）
		t_wait: 等待稳定时间（纳秒）
		t_uW: 微波脉冲持续时间（纳秒）
	
	返回:
		配置好的DAQ任务和软件延迟时间（秒）
	
	Rabi实验的脉冲序列包含两个半周期：
	1. 信号半周期（有微波）
	2. 参考半周期（无微波）
	
	每个半周期的结构：
	- 极化激光（AOM）
	- 等待稳定（无激光）
	- 微波脉冲（信号半周期）或等待（参考半周期）
	- 读取激光（AOM）
	- DAQ采集（读取激光开始后延迟t_readoutDelay）
	
	注意：使用软件延迟确保采样点与PB脉冲窗口对齐
	"""
	try:
		print(f"为Rabi实验配置DAQ，样本数: {Nsamples}")
		print(f"DAQ_APDInput: {DAQ_APDInput}")
		print(f"minVoltage: {minVoltage}, maxVoltage: {maxVoltage}")
		
		# 计算Rabi序列的时间参数
		t_startTrig = t_min * round(300*ns/t_min)
		t_readout = t_min * round(300*ns/t_min)
		uWtoAOM_delay = t_min * round(1*us/t_min)
		start_delay = t_min * round(1*us/t_min)
		
		# 第一个半周期：信号（有微波）
		AOM_polarization1 = start_delay
		wait_end1 = AOM_polarization1 + t_AOM + t_wait
		uW_start1 = wait_end1
		AOM_readout1 = uW_start1 + t_uW + uWtoAOM_delay
		DAQ_start1 = AOM_readout1 + t_readoutDelay
		firstHalfDuration = AOM_readout1 + t_AOM
		
		# 第二个半周期：参考（无微波）
		AOM_polarization2 = firstHalfDuration
		wait_end2 = AOM_polarization2 + t_AOM + t_wait
		AOM_readout2 = wait_end2 + t_uW + uWtoAOM_delay
		DAQ_start2 = AOM_readout2 + t_readoutDelay
		
		# 计算每个完整Rabi周期的时间
		t_rabi_cycle_ns = AOM_readout2 + t_AOM
		t_rabi_cycle_us = t_rabi_cycle_ns / 1000
		
		# 计算PB的DAQ脉冲窗口
		pb_pulse_start_1 = DAQ_start1
		pb_pulse_end_1 = DAQ_start1 + t_readout
		pb_pulse_start_2 = DAQ_start2
		pb_pulse_end_2 = DAQ_start2 + t_readout
		
		# 计算理想的采样时刻（窗口中心）
		sample_time_1 = pb_pulse_start_1 + t_readout / 2
		sample_time_2 = pb_pulse_start_2 + t_readout / 2
		
		# 关键修改：调整采样率，使采样点自然对齐到DAQ脉冲窗口
		# 方法：使采样间隔等于Rabi周期的一半（即每个半周期采集一个点）
		t_half_cycle_ns = t_rabi_cycle_ns / 2
		sampling_rate = int(1e9 / t_half_cycle_ns)
		
		# 确保采样率不超过MyDAQ的最大采样率
		if sampling_rate > DAQ_MaxSamplingRate:
			sampling_rate = DAQ_MaxSamplingRate
			print(f"警告：计算的采样率超过MyDAQ最大采样率，已调整为{sampling_rate} Hz")
		
		# 总样本数
		NsampsPerDAQread = 2 * Nsamples
		
		# 计算总采集时间
		totalAcquisitionTime_sec = (t_rabi_cycle_ns * Nsamples) / 1e9
		
		# 计算采样间隔（纳秒）
		sample_interval_ns = 1e9 / sampling_rate
		
		# 关键修改：计算软件延迟，确保第一个采样点在第一个PB脉冲窗口内
		# 方法：计算需要延迟多少个采样间隔，使采样点落在窗口中心
		# 理想的第一个采样时刻是sample_time_1
		# myDAQ从t=0开始采样，第i个采样点在t=i*sample_interval_ns
		# 我们需要找到k，使得k*sample_interval_ns ≈ sample_time_1
		k = round(sample_time_1 / sample_interval_ns)
		# 调整后的第一个采样时刻
		adjusted_sample_time_1 = k * sample_interval_ns
		
		# 计算软件延迟时间（秒）
		software_delay_sec = adjusted_sample_time_1 / 1e9
		
		# 验证采样点是否落在PB的DAQ脉冲窗口内
		# myDAQ从t=0开始采样，第1个采样点在t=0，第2个在t=sample_interval_ns，以此类推
		print("\n验证采样点与PB脉冲窗口的对齐:")
		for i in range(min(4, NsampsPerDAQread)):
			sample_time = adjusted_sample_time_1 + i * sample_interval_ns
			# 计算当前采样点在Rabi周期中的位置
			cycle_position = sample_time % t_rabi_cycle_ns
			
			# 判断采样点是否在DAQ脉冲窗口内
			in_window_1 = pb_pulse_start_1 <= cycle_position <= pb_pulse_end_1
			in_window_2 = pb_pulse_start_2 <= cycle_position <= pb_pulse_end_2
			
			if i % 2 == 0:
				# 偶数索引：应该在第一个窗口（信号）
				print(f"  采样点 {i} (信号): 时间 = {sample_time:.2f} ns, 周期位置 = {cycle_position:.2f} ns, 在窗口内 = {in_window_1}")
			else:
				# 奇数索引：应该在第二个窗口（参考）
				print(f"  采样点 {i} (参考): 时间 = {sample_time:.2f} ns, 周期位置 = {cycle_position:.2f} ns, 在窗口内 = {in_window_2}")
		
		# 创建并配置模拟输入电压任务
		readTask = nidaqmx.Task()
		print("\n创建DAQ任务成功")
		
		# 使用Diff（差分）终端配置
		channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.DIFF,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		print("添加模拟输入通道成功")
		
		# 配置采样时钟（使用内部时钟源）
		readTask.timing.cfg_samp_clk_timing(sampling_rate, "", Edge.RISING, AcquisitionType.FINITE, NsampsPerDAQread)
		print("配置采样时钟成功")
		
		# 打印采样时序信息
		print(f"\nRabi周期时间: {t_rabi_cycle_us:.2f} μs")
		print(f"半周期时间: {t_half_cycle_ns:.2f} ns")
		print(f"采样率: {sampling_rate} Hz")
		print(f"采样间隔: {sample_interval_ns:.2f} ns")
		print(f"总采集时间: {totalAcquisitionTime_sec:.4f} s")
		
		# 打印关键时间点
		print(f"\n关键时间点:")
		print(f"  信号半周期DAQ采集开始: {DAQ_start1:.2f} ns")
		print(f"  参考半周期DAQ采集开始: {DAQ_start2:.2f} ns")
		print(f"  DAQ采集窗口宽度: {t_readout:.2f} ns")
		print(f"  PB脉冲窗口1: {pb_pulse_start_1:.2f} - {pb_pulse_end_1:.2f} ns")
		print(f"  PB脉冲窗口2: {pb_pulse_start_2:.2f} - {pb_pulse_end_2:.2f} ns")
		print(f"  理想采样时刻1: {sample_time_1:.2f} ns")
		print(f"  调整后采样时刻1: {adjusted_sample_time_1:.2f} ns")
		print(f"  软件延迟: {software_delay_sec:.6f} s")
		
		print("\nRabi实验DAQ配置成功")
		
		# 返回DAQ任务和软件延迟时间
		return readTask, software_delay_sec
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
		print(f'当前工作目录: {os.getcwd()}')
		print(f'DAQ_APDInput: {DAQ_APDInput}')
		# 修复：使用正确的变量名readTask
		if 'readTask' in locals():
			closeDAQTask(readTask)
		# 不要直接退出，而是返回None，让调用者处理错误
		return None
	return readTask
		
		# 配置开始触发（MyDAQ不支持，已注释）
		# readStartTrig = readTask.triggers.start_trigger
		# readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig,Edge.RISING)
		


def configureDAQbyTime(acquisitionTime_ns, Nsamples):
	"""根据采集时间和样本数配置DAQ
	
	参数:
		acquisitionTime_ns: 每个样本组的采集时间（纳秒）
		Nsamples: 样本组数
	
	返回:
		配置好的DAQ任务、实际样本数和初始延迟时间（秒）
	
	这个函数根据脉冲序列长度和样本数计算需要的采样率和样本数
	与PB的DAQ通道序列保持一致：
	- PB的DAQ脉冲在每个半周期末尾的采样窗口内
	- 采样窗口位置：t_duration - t_readoutBuffer 到 t_duration - t_readoutBuffer + t_readout
	- 调整采样率，使采样点恰好落在PB的DAQ脉冲窗口内
	- 确保每个t_duration周期只采集一个点
	- 确保第一个周期采集有微波信号，第二个周期采集无微波信号
	
	注意：使用软件延迟确保采样点与PB脉冲窗口对齐
	"""
	try:
		# 计算每个样本组的时间（2*t_duration）
		t_sampleGroup_ns = acquisitionTime_ns
		# 计算每个半周期的时间（t_duration）
		t_halfCycle_ns = t_sampleGroup_ns / 2
		
		# 计算t_duration（微秒）
		t_duration_us = t_halfCycle_ns / 1000
		
		# 计算采样率：每个t_duration周期采集一个点
		# 每个完整周期（2*t_duration）采集2个点（信号+背景）
		sampling_rate = int(1e6 / t_duration_us)
		
		# PB的采样窗口参数
		t_readoutBuffer = 2000  # 2μs，与sequenceControl.py中的设置一致
		t_readout = 300  # 300ns，与sequenceControl.py中的设置一致
		
		# 计算PB的DAQ脉冲窗口位置
		pb_pulse_start_1 = t_halfCycle_ns - t_readoutBuffer
		pb_pulse_end_1 = pb_pulse_start_1 + t_readout
		pb_pulse_start_2 = 2 * t_halfCycle_ns - t_readoutBuffer
		pb_pulse_end_2 = pb_pulse_start_2 + t_readout
		
		# 计算理想的采样时刻（窗口中心）
		sample_time_1 = pb_pulse_start_1 + t_readout / 2
		sample_time_2 = pb_pulse_start_2 + t_readout / 2
		
		# 总样本数：每个周期2个样本（信号+背景），共Nsamples个周期
		totalSamples = 2 * Nsamples
		
		# 计算总采集时间
		totalAcquisitionTime_ns = t_sampleGroup_ns * Nsamples
		totalAcquisitionTime_sec = totalAcquisitionTime_ns / 1e9
		
		# 但MyDAQ的采样率有上限
		actualSampleRate = min(sampling_rate, DAQ_MaxSamplingRate)
		
		# 重新计算实际总样本数
		actualTotalSamples = int(actualSampleRate * totalAcquisitionTime_sec)
		# 确保样本数是偶数（每个周期2个样本）
		if actualTotalSamples % 2 != 0:
			actualTotalSamples += 1
		
		# 重新计算实际样本组数
		actualNsamples = actualTotalSamples // 2
		
		# 计算实际采样点时刻
		actual_sample_interval = 1e9 / actualSampleRate  # 纳秒
		
		# 关键修改：计算软件延迟，确保第一个采样点在第一个PB脉冲窗口内
		# 方法：计算需要延迟多少个采样间隔，使采样点落在窗口中心
		# 理想的第一个采样时刻是sample_time_1
		# myDAQ从t=0开始采样，第i个采样点在t=i*actual_sample_interval
		# 我们需要找到k，使得k*actual_sample_interval ≈ sample_time_1
		k = round(sample_time_1 / actual_sample_interval)
		# 调整后的第一个采样时刻
		adjusted_sample_time_1 = k * actual_sample_interval
		
		# 计算软件延迟时间（秒）
		software_delay_sec = adjusted_sample_time_1 / 1e9
		
		# 生成采样时刻，从调整后的时间开始
		sample_times = [adjusted_sample_time_1 + i * actual_sample_interval for i in range(actualTotalSamples)]
		
		# 验证采样点是否落在PB的DAQ脉冲窗口内
		samples_in_window = 0
		print("\n验证采样点与PB脉冲窗口的对齐:")
		for i, sample_time in enumerate(sample_times[:4]):
			# 计算当前周期的位置
			cycle_position = sample_time % (2 * t_halfCycle_ns)
			if i % 2 == 0:
				# 信号样本，应该在第一个窗口内（有微波）
				in_window = pb_pulse_start_1 <= cycle_position <= pb_pulse_end_1
				print(f"  采样点 {i} (信号): 时间 = {sample_time:.2f} ns, 周期位置 = {cycle_position:.2f} ns, 在窗口内 = {in_window}")
				if in_window:
					samples_in_window += 1
			else:
				# 背景样本，应该在第二个窗口内（无微波）
				in_window = 0 <= cycle_position <= pb_pulse_end_2 - 2 * t_halfCycle_ns
				print(f"  采样点 {i} (背景): 时间 = {sample_time:.2f} ns, 周期位置 = {cycle_position:.2f} ns, 在窗口内 = {in_window}")
				if in_window:
					samples_in_window += 1
		
		print(f"  前4个采样点中，{samples_in_window}个在窗口内")
		
		print(f"\n根据时间和样本数配置DAQ（匹配PB脉冲序列）:")
		print(f"  t_duration: {t_duration_us} μs")
		print(f"  每个样本组时间: {t_sampleGroup_ns} ns")
		print(f"  每个半周期时间: {t_halfCycle_ns} ns")
		print(f"  理想采样时刻1: {sample_time_1:.2f} ns")
		print(f"  调整后采样时刻1: {adjusted_sample_time_1:.2f} ns")
		print(f"  软件延迟: {software_delay_sec:.6f} s")
		print(f"  样本组数: {Nsamples}")
		print(f"  总采集时间: {totalAcquisitionTime_ns} ns = {totalAcquisitionTime_sec} s")
		print(f"  计算采样率: {sampling_rate} Hz")
		print(f"  实际采样率: {actualSampleRate} Hz")
		print(f"  总样本数: {actualTotalSamples}")
		print(f"  实际样本组数: {actualNsamples}")
		print(f"  PB采样窗口1: {pb_pulse_start_1} ns - {pb_pulse_end_1} ns")
		print(f"  PB采样窗口2: {pb_pulse_start_2} ns - {pb_pulse_end_2} ns")
		print(f"  理想采样时刻1: {sample_time_1} ns")
		print(f"  理想采样时刻2: {sample_time_2} ns")
		print(f"  实际采样间隔: {actual_sample_interval} ns")
		print(f"  采样点在窗口内的比例: {samples_in_window/actualTotalSamples*100:.2f}%")
		
		# 创建并配置模拟输入电压任务
		readTask = nidaqmx.Task()
		print("创建DAQ任务成功")
		
		# 使用Diff（差分）终端配置
		channel = readTask.ai_channels.add_ai_voltage_chan(DAQ_APDInput,"",TerminalConfiguration.DIFF,minVoltage,maxVoltage,VoltageUnits.VOLTS)
		print("添加模拟输入通道成功")
		
		# 配置采样时钟
		readTask.timing.cfg_samp_clk_timing(actualSampleRate, "", Edge.RISING, AcquisitionType.FINITE, actualTotalSamples)
		print("配置采样时钟成功")
		
		print("DAQ时间配置成功")
		
		# 返回DAQ任务、实际样本数和软件延迟时间
		return readTask, actualTotalSamples, software_delay_sec
		
	except Exception as excpt:
		print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。')
		print(f'异常类型: {type(excpt).__name__}')
		print(f'异常信息: {excpt}')
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