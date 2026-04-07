#PBcontrol.py
# Copyright 2018 Diana Prado Lopes Aude Craik

# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from ctypes import *
from spinapi import *
import numpy as np
import sequenceControl as seqCtl
from connectionConfig import *
import sys


def errorCatcher(statusVar):
	if statusVar<0:
		print ('Error: ', pb_get_error())
		sys.exit()
		
# 全局变量，用于跟踪PulseBlaster是否已经初始化
_pb_initialized = False

def configurePB():
	global _pb_initialized
	pb_set_debug(1)
	
	# 只有当PulseBlaster还未初始化时才调用pb_init()
	if not _pb_initialized:
		status = pb_init()
		errorCatcher(status)
		_pb_initialized = True
		print("PulseBlaster初始化成功")
	else:
		print("PulseBlaster已经初始化，跳过初始化步骤")
	
	# 每次都设置核心时钟，确保时钟设置正确
	pb_core_clock(PBclk)
	return 0

def pb_inst_pbonly(flags,inst,inst_data,length):
	return spinapi.pb_inst_pbonly(flags, inst, inst_data, length)
	
def programPB(sequence,sequenceArgs):
	channels=seqCtl.makeSequence(sequence, sequenceArgs)
	channelBitMasks = seqCtl.sequenceEventCataloguer(channels)
	instructionArray=programSequence(channelBitMasks)
	return instructionArray
	
def programSequence(channelBitMasks):
	# 定义时钟通道的位掩码（通道7，对应位6，值为0x80）
	CLOCK_CHANNEL_MASK = 0x80
	
	# 计算10MHz时钟的周期（纳秒）
	clock_frequency = 10e6  # 10 MHz
	clock_period = int(1e9 / clock_frequency)  # 计算周期，单位为纳秒
	half_period = clock_period // 2  # 半周期
	
	# 确保半周期是最小时间分辨率的整数倍
	min_resolution = 1000 / PBclk
	if half_period % min_resolution != 0:
		# 调整半周期到最小分辨率的整数倍
		half_period = int(round(half_period / min_resolution) * min_resolution)
	
	# 确保半周期不小于最小时间分辨率
	if half_period < min_resolution:
		half_period = int(min_resolution)
	
	# 为了安全起见，设置一个最小延迟时间
	min_delay = max(min_resolution, 10)  # 至少10ns
	
	eventTimes = list(channelBitMasks.keys())
	numEvents = len(eventTimes)
	eventDurations =list(np.zeros(numEvents-1))
	numInstructions = numEvents-1
	for i in range(0,numInstructions):
		if i == numInstructions-1:
			eventDurations[i] = eventTimes[i+1]-eventTimes[i]
		else:
			eventDurations[i] = eventTimes[i+1]-eventTimes[i]
	instructionArray = []
	bitMasks = list(channelBitMasks.values())
	start = [0]
	
	# 生成时钟信号和实验信号的混合指令
	# 对于每个实验事件，我们需要生成多个时钟周期的指令
	for i in range(0,numEvents-1):
		current_mask = bitMasks[i]
		duration = eventDurations[i]
		
		# 确保事件持续时间不小于最小延迟时间
		if duration < min_delay:
			duration = min_delay
		
		# 计算这个事件需要多少个时钟周期
		num_clock_cycles = int(duration // clock_period)
		remaining_time = duration % clock_period
		
		# 生成完整的时钟周期
		for j in range(num_clock_cycles):
			# 时钟高电平，同时输出实验信号
			flags = current_mask | CLOCK_CHANNEL_MASK
			# 确保延迟时间不小于最小延迟时间
			instruction_delay = max(half_period, min_delay)
			if i == numEvents-2 and j == num_clock_cycles-1 and remaining_time == 0:
				# 最后一个事件的最后一个时钟周期，分支回开始
				instructionArray.extend([[flags, spinapi.BRANCH, start[0], instruction_delay]])
			else:
				# 其他情况，继续下一个指令
				instructionArray.extend([[flags, spinapi.CONTINUE, 0, instruction_delay]])
			
			# 时钟低电平，同时输出实验信号
			flags = current_mask
			# 确保延迟时间不小于最小延迟时间
			instruction_delay = max(half_period, min_delay)
			if i == numEvents-2 and j == num_clock_cycles-1 and remaining_time == 0:
				# 最后一个事件的最后一个时钟周期，分支回开始
				instructionArray.extend([[flags, spinapi.BRANCH, start[0], instruction_delay]])
			else:
				# 其他情况，继续下一个指令
				instructionArray.extend([[flags, spinapi.CONTINUE, 0, instruction_delay]])
		
		# 处理剩余时间
		if remaining_time > 0:
			# 确保剩余时间不小于最小延迟时间
			if remaining_time < min_delay:
				remaining_time = min_delay
			
			# 计算剩余时间包含多少个半周期
			num_half_cycles = int(remaining_time // half_period)
			final_remaining = remaining_time % half_period
			
			# 生成剩余的半周期
			for j in range(num_half_cycles):
				# 交替时钟电平，同时输出实验信号
				if j % 2 == 0:
					flags = current_mask | CLOCK_CHANNEL_MASK
				else:
					flags = current_mask
				
				# 确保延迟时间不小于最小延迟时间
				instruction_delay = max(half_period, min_delay)
				if i == numEvents-2 and j == num_half_cycles-1 and final_remaining == 0:
					# 最后一个事件的最后一个半周期，分支回开始
					instructionArray.extend([[flags, spinapi.BRANCH, start[0], instruction_delay]])
				else:
					# 其他情况，继续下一个指令
					instructionArray.extend([[flags, spinapi.CONTINUE, 0, instruction_delay]])
			
			# 处理最后的剩余时间
			if final_remaining > 0:
				# 确保最终剩余时间不小于最小延迟时间
				if final_remaining < min_delay:
					final_remaining = min_delay
				
				# 最后一个短指令，使用剩余时间
				flags = current_mask | CLOCK_CHANNEL_MASK if num_half_cycles % 2 == 0 else current_mask
				if i == numEvents-2:
					# 最后一个事件，分支回开始
					instructionArray.extend([[flags, spinapi.BRANCH, start[0], final_remaining]])
				else:
					# 其他情况，继续下一个指令
					instructionArray.extend([[flags, spinapi.CONTINUE, 0, final_remaining]])

	#Program Pulseblaster
	configurePB()
	status = pb_start_programming(PULSE_PROGRAM)
	errorCatcher(status)
	startDone = False
	for i in range(0, len(instructionArray)):
		if startDone:
			status = pb_inst_pbonly(instructionArray[i][0],instructionArray[i][1],instructionArray[i][2],instructionArray[i][3])
			errorCatcher(status)
		else:
			start[0]= pb_inst_pbonly(instructionArray[0][0],instructionArray[0][1],instructionArray[0][2],instructionArray[0][3])
			errorCatcher(start[0])
			startDone = True
	status = pb_stop_programming()
	errorCatcher(status)
	status = pb_start()
	errorCatcher(status)
	
	# 不要关闭PulseBlaster，保持时钟信号运行
	# status = pb_close()
	# errorCatcher(status)
	
	return instructionArray
	
	
	