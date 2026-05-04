# mainControl.py
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


# 导入模块
import connectionConfig as conCfg
import sequenceControl as seqCtl
import SRScontrol as SRSctl
import PBcontrol as PBctl

# 根据设备类型动态导入DAQ控制模块
# DAQ_DEVICE_TYPE = 0: myDAQ (使用 nidaqmx)
# DAQ_DEVICE_TYPE = 1: USB-7855R FPGA (使用 nifpga)
# DAQ_DEVICE_TYPE = 2: USB-6363 (使用 nidaqmx)
if conCfg.DAQ_DEVICE_TYPE == 1:
    # USB-7855R FPGA 必须使用 nifpga，不能使用 nidaqmx
    import DAQcontrol_USB7855R as DAQctl
else:
    # 其他设备使用 nidaqmx
    import DAQcontrol as DAQctl
import matplotlib.pyplot as plt
import numpy as np
from spinapi import ms,us,ns
from random import shuffle
from os.path import isdir 
from os import makedirs
import sys
import math
from importlib import import_module

# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 给出：
t_min = 1e3/conCfg.PBclk # 单位为纳秒
def validateUserInput(expCfg):
# 此函数验证实验配置文件（如 ESRconfig、Rabiconfig 等）中的用户输入。
	
	# 检查 N_scanPts、Nsamples、Navg 是否都是整数，且 Nsamples>=1、Navg>=1、N_scanPts>=2
	if (not isinstance(expCfg.Nsamples, int)) or (expCfg.Nsamples<1):
		print('错误：Nsamples 必须是大于等于 1 的整数。')
		sys.exit()
	if (not isinstance(expCfg.Navg, int)) or (expCfg.Navg<1):
		print('错误：Navg 必须是大于等于 1 的整数。')
		sys.exit()
	if (not isinstance(expCfg.N_scanPts, int)) or (expCfg.N_scanPts<2):
		print('错误：N_scanPts 必须是大于等于 2 的整数。')
		sys.exit()
	
	# 脉冲序列参数检查：
	# 检查 IQpadding 是否是 t_min 的倍数且大于 5*t_min：
	if expCfg.sequence in ['T2seq','XY8seq','correlSpecSeq']:
		if (expCfg.IQpadding<(5*t_min)) or (expCfg.IQpadding%t_min):
			print('错误：IQpadding 设置为', expCfg.IQpadding,'，它要么小于',5*t_min,'，要么不是',t_min,'的倍数。请编辑 IQpadding 以确保它大于',5*t_min,'纳秒且是',t_min,'的倍数。')
	# 检查 ESRseq 中的 t_duration 是否是 (2*t_min) 的倍数：
	if expCfg.sequence == 'ESRseq':
		if expCfg.t_duration%(2*t_min):
			print('警告：t_duration 设置为', expCfg.t_duration,'纳秒，它不是',(2*t_min),'纳秒的整数倍。正在将 t_duration 四舍五入到最接近的',(2*t_min),'纳秒的倍数...')
			expCfg.t_duration = (2*t_min)*round(t_duration_ns/(2*t_min))
			print('t_duration 现在设置为', expCfg.t_duration,'纳秒')
	
	# 检查 t_readoutDelay 和 t_AOM 是否是 t_min 的倍数：
	if expCfg.sequence in ['RabiSeq','T2seq','XY8seq', 'correlSpecSeq', 'T1seq']:
		if expCfg.t_readoutDelay%t_min:
			print('错误：t_readoutDelay 设置为', expCfg.t_readoutDelay,'纳秒，它不是',t_min,'纳秒的倍数。请将 t_readoutDelay 设置为',t_min,'纳秒的整数倍。')
			sys.exit()
		if expCfg.t_AOM%t_min:
			print('错误：t_AOM 设置为', expCfg.t_AOM,'纳秒，它不是',t_min,'纳秒的倍数。请将 t_AOM 设置为',t_min,'纳秒的整数倍。')
			sys.exit()
		# 检查 t_readoutDelay 和 t_AOM 是否大于 5*t_min：
		if expCfg.t_AOM<(5*t_min):
			print('错误：t_AOM 必须大于',(5*t_min),'纳秒！')
			sys.exit()
		if expCfg.t_readoutDelay<(5*t_min):
			print('错误：t_readoutDelay 必须大于',(5*t_min),'纳秒！')
			sys.exit()
	# 检查相关光谱序列中的 tau0 是否是 2*t_min 的整数倍：
	if expCfg.sequence == 'correlSpecSeq':
		if expCfg.tau0%(2*t_min):
			print('错误：tau0 设置为', expCfg.tau0,'纳秒，它不是',(2*t_min),'纳秒的倍数。请将 tau0 设置为',(2*t_min),'纳秒的整数倍。')
			sys.exit()
	# XY8 重复次数检查：
	if expCfg.sequence in ['XY8seq', 'correlSpecSeq']:
		if expCfg.N<1 or (not isinstance(expCfg.N, int)):
			print('错误：XY8 重复次数 N 必须是大于等于 1 的整数。')
			sys.exit()
	
	# Pi 脉冲长度检查：
	if expCfg.sequence == 'T1seq':
		if expCfg.t_pi<t_min or expCfg.t_pi%t_min:
			print('错误：请求的 pi 脉冲长度',expCfg.t_pi,'纳秒要么小于',t_min,'纳秒，要么不是',t_min,'纳秒的整数倍。')
			sys.exit()
	if expCfg.sequence in ['T2seq','XY8seq','correlSpecSeq']:
		# 检查用户输入的 pi 脉冲长度是否短于 (2*t_min) 或不是 2*t_min 的倍数：
		if expCfg.t_pi<(2*t_min):
			print('错误：请求的 pi 脉冲长度=',expCfg.t_pi,'纳秒，小于',(2*t_min),'纳秒。t_pi 必须至少设置为',(2*t_min),'纳秒。')
			sys.exit()
		if expCfg.t_pi%(2*t_min):
			print('警告：t_pi 设置为', expCfg.t_pi,'纳秒，它不是',(2*t_min),'纳秒的整数倍。正在将 t_pi 四舍五入到最接近的',(2*t_min),'纳秒的倍数...')
			expCfg.t_pi = (2*t_min)*round(float(expCfg.t_pi)/(2*t_min))
			print('t_pi 现在设置为', expCfg.t_pi,'纳秒')
			
	# 扫描步长检查：
	stepSize = expCfg.scannedParam[1]-expCfg.scannedParam[0]
	if (expCfg.sequence == 'ESRseq'):
		# 如果请求的频率步长小于 SRS 频率分辨率 (1uHz)，则将步长四舍五入到 1uHz：
		if ((stepSize*1e6)%1):
			roundedFreqStepSize = (1e-6)*round((1e6)*stepSize)
			expCfg.scannedParam[-1] = (expCfg.N_scanPts-1)*roundedFreqStepSize + expCfg.scannedParam[0] 
			print('警告：请求的频率步长为',stepSize,'赫兹，它不是 SRS 频率分辨率 1uHz 的整数倍。正在将步长四舍五入到最接近的 1uHz 的倍数。\n步长现在为',roundedFreqStepSize,'\n',expCfg.scanStartName,'= ',expCfg.scannedParam[0],' 和 \n',expCfg.scanEndName,'= ',expCfg.scannedParam[-1])
			expCfg.scannedParam = np.linspace(expCfg.scannedParam[0],expCfg.scannedParam[-1], expCfg.N_scanPts,endpoint= True)
	if (expCfg.sequence in ['RabiSeq', 'T1seq']) or (expCfg.sequence == 'T2seq' and expCfg.numberOfPiPulses==1):
		if stepSize<t_min:
			print('错误：请求的时间步长为',stepSize,'纳秒，短于',t_min,'纳秒。请更改 N_scanPts 或',expCfg.scanStartName,'和',expCfg.scanEndName,'以增加时间步长。')
			sys.exit()
		# 如果请求的步长大于 t_min 但不是 t_min 的倍数：
		if (stepSize%t_min):
			roundedStepSize = t_min*round(stepSize/t_min)
			expCfg.scannedParam[-1] = (expCfg.N_scanPts-1)*roundedStepSize + expCfg.scannedParam[0] 
			print('警告：请求的时间步长为',stepSize,'纳秒，它不是',t_min,'纳秒的整数倍。正在将步长四舍五入到最接近的',t_min,'纳秒的倍数：\n步长现在为',roundedStepSize,'\n',expCfg.scanStartName,'= ',expCfg.scannedParam[0],' 和 \n',expCfg.scanEndName,'= ',expCfg.scannedParam[-1])
			expCfg.scannedParam = np.linspace(expCfg.scannedParam[0],expCfg.scannedParam[-1], expCfg.N_scanPts,endpoint= True)
			
	if expCfg.sequence =='RabiSeq':
		# Pulseblaster 错误 - 我们的 PulseBlaster 板似乎无法输出 8 纳秒的脉冲。因此，检查是否请求了 8 纳秒并删除该点：
		if 8 in expCfg.scannedParam:
			expCfg.scannedParam = list(expCfg.scannedParam)
			expCfg.scannedParam.remove(8)				
			expCfg.N_scanPts = len(expCfg.scannedParam)
			print('警告：由于非官方报告提到某些 PB 板可能存在一个问题，即输出 8 纳秒脉冲的指令会生成 10 纳秒脉冲，因此不会在 8 纳秒扫描点收集数据。正在从扫描点列表中删除 8 纳秒扫描点。')	
	
	if (expCfg.sequence == 'XY8seq') or (expCfg.sequence=='T2seq' and expCfg.numberOfPiPulses > 1):
		# 检查请求的扫描步长是否太短或不是 2*t_min 的倍数：
		if stepSize<(2*t_min):
			print('错误：请求的时间步长为',stepSize,'纳秒，短于', (2*t_min),'纳秒。请更改 N_scanPts 或',expCfg.scanStartName,'和',expCfg.scanEndName,'以增加时间步长。')
			sys.exit()
		# 如果请求的步长大于 2*t_min 但不是 t_min 的倍数，则四舍五入到最接近的 (2*t_min) 的倍数并警告用户：
		if (stepSize%(2*t_min)):
			roundedStepSize = (2*t_min)*round(stepSize/(2*t_min))
			expCfg.scannedParam[-1] =  (expCfg.N_scanPts-1)*roundedStepSize + expCfg.scannedParam[0] 
			print('警告：请求的时间步长为',stepSize,'纳秒，它不是',(2*t_min),'纳秒的整数倍。正在将步长四舍五入到最接近的',(2*t_min),'纳秒的倍数：\n 步长现在为',roundedStepSize,'\n ',expCfg.scanStartName,'= ',expCfg.scannedParam[0],' 和 \n',expCfg.scanEndName,'= ',expCfg.scannedParam[-1])
			expCfg.scannedParam = np.linspace(expCfg.scannedParam[0],expCfg.scannedParam[-1], expCfg.N_scanPts,endpoint= True)
	
	# 扫描起点（最小延迟持续时间）检查：
	if (expCfg.sequence in ['RabiSeq', 'correlSpecSeq']) or (expCfg.sequence == 'T2seq' and expCfg.numberOfPiPulses==1):
	# 检查请求的起始延迟/脉冲长度是否为正数且是 t_min 的倍数：
		if expCfg.scannedParam[0]<0:
			print('错误：请求的',expCfg.scanStartName,' = ',expCfg.scannedParam[0],'小于 0。',expCfg.scanStartName,'必须大于等于 0。')
			sys.exit()
		if expCfg.scannedParam[0]%t_min:
			print('错误：',expCfg.scanStartName,'设置为', expCfg.scannedParam[0],'，它不是',t_min,'纳秒的倍数。请将', expCfg.scanStartName,'设置为',t_min,'纳秒的整数倍。')
			sys.exit()
	
	if (expCfg.sequence == 'XY8seq') or (expCfg.sequence=='T2seq' and expCfg.numberOfPiPulses > 1):
	# 检查请求的起始延迟/脉冲长度是否是 2*t_min 的倍数：
		if expCfg.scannedParam[0]%(2*t_min):
			print('错误：',expCfg.scanStartName,'设置为', expCfg.scannedParam[0],'，它不是',(2*t_min),'纳秒的倍数。请将', expCfg.scanStartName,'设置为',(2*t_min),'纳秒的整数倍。')
			sys.exit()
		
	if expCfg.sequence == 'T1seq':
		if expCfg.scannedParam[0]<(expCfg.t_readoutDelay + t_min*round((1*us)/t_min)):
			print('错误：请求的',expCfg.scanStartName,'太短。', expCfg.scanStartName,'必须大于等于 0。')
			sys.exit()
		if expCfg.scannedParam[0]%t_min:
			print('错误：',expCfg.scanStartName,'设置为', expCfg.scannedParam[0],'，它不是',t_min,'纳秒的倍数。请将', expCfg.scanStartName,'设置为',t_min,'纳秒的整数倍。')
			sys.exit()
	
	if expCfg.sequence in ['T2seq','XY8seq']:
		# 检查请求的起始延迟是否短于 3*(5*t_min)：
		if expCfg.scannedParam[0]<3*(5*t_min):
			print('错误：请求的',expCfg.scanStartName,'为',expCfg.scannedParam[0],'纳秒，太短。对于此脉冲序列，',expCfg.scanStartName,'必须至少设置为',3*(5*t_min),'纳秒')
			sys.exit()
	
	if expCfg.sequence == 'T2seq':
		if (not isinstance(expCfg.numberOfPiPulses, int)) or (expCfg.numberOfPiPulses<1):
			print('错误：numberOfPiPulses 必须是正整数！')
			sys.exit()
		if expCfg.numberOfPiPulses == 1:
			if expCfg.scannedParam[0]<(2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min)):
				# 检查起始延迟是否太短，无法允许 PB 时间分辨率：
				print('错误：',expCfg.scanStartName,'太短。对于您的 pi_pulse 长度，',expCfg.scanStartName,'必须至少为', (2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min)),'纳秒。')
				sys.exit()
		else: # pi 脉冲数量>1
			if expCfg.scannedParam[0]<(2*(2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min))):
				print('错误：',expCfg.scanStartName,'太短。对于您的 pi_pulse 长度，',expCfg.scanStartName,'必须至少为', (2*(2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min))),'纳秒。')
				sys.exit()
				
	if expCfg.sequence == 'XY8seq':
		if expCfg.scannedParam[0]<(2*(2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min))):
			print('错误：',expCfg.scanStartName,'太短。对于您的 pi_pulse 长度，',expCfg.scanStartName,'必须至少为', (2*(2*expCfg.IQpadding + (3/4)*expCfg.t_pi + (5*t_min))),'纳秒。')
			sys.exit()
		
	# 自由进动时间检查。pi 或 pi/2 脉冲的上升沿与后续 pi 脉冲的上升沿之间的间距
	# 或 T2、XY8 和相关光谱序列中的 pi/2 脉冲必须是 t_min 的整数倍。用户输入的
	# 自由进动时间定义为后续脉冲中心之间的时间。因此，对于给定的 pi 脉冲长度，
	# 我们检查用户是否选择了产生边到边时间为 t_min 倍数的起始自由进动时间。
	# 如果没有，我们将自由进动时间向量移动 t_min/2 并警告用户。
	if (expCfg.sequence=='T2seq' and expCfg.numberOfPiPulses == 1):
		if (expCfg.scannedParam[0]-(expCfg.t_pi/4))%t_min:
			expCfg.scannedParam = [x+(t_min/2) for x in expCfg.scannedParam]
			print('警告：扫描时间向量的每个元素已移动',t_min/2,'纳秒，以便微波脉冲之间的上升沿到上升沿间距为',t_min,'纳秒的倍数。\
\n详细信息：T2 和 XY8 序列中 pi 或 pi/2 脉冲的上升沿与后续 pi 或 pi/2 脉冲的上升沿之间的间距\
必须是',t_min,'纳秒的整数倍。用户输入的自由进动时间定义为后续脉冲中心之间的时间。\
您的 pi 脉冲长度为',expCfg.t_pi,'纳秒，产生的边到边时间为', (expCfg.scannedParam[0]-(expCfg.t_pi/4)),'纳秒（在扫描开始时），它不是',t_min,'纳秒的倍数。\
因此，我们将时间移动',t_min/2,'纳秒。')	
	if (expCfg.sequence =='XY8seq') or (expCfg.sequence=='T2seq' and expCfg.numberOfPiPulses > 1):
		half_t_delay = expCfg.scannedParam[0]/2
		if (half_t_delay-(expCfg.t_pi/4))%t_min:
			expCfg.scannedParam = [x+(t_min/2) for x in expCfg.scannedParam]
			print('警告：扫描时间向量的每个元素已移动',t_min/2,'纳秒，以便微波脉冲之间的上升沿到上升沿间距为',t_min,'纳秒的倍数。\
\n详细信息：T2 和 XY8 序列中 pi 或 pi/2 脉冲的上升沿与后续 pi 或 pi/2 脉冲的上升沿之间的间距\
必须是',t_min,'纳秒的整数倍。用户输入的自由进动时间定义为后续脉冲中心之间的时间。\
您的 pi 脉冲长度为',expCfg.t_pi,'纳秒，产生的边到边时间为', (half_t_delay-(expCfg.t_pi/4)),'纳秒（在扫描开始时），它不是',t_min,'纳秒的倍数。\
因此，我们将时间移动',t_min/2,'纳秒。')
	if expCfg.sequence == 'correlSpecSeq':
		half_t_delay = expCfg.tau0/2
		if (half_t_delay-(expCfg.t_pi/4))%t_min:
			expCfg.tau0 = expCfg.tau0 +(t_min/2)*ns
			print('警告：tau0 已移动',t_min/2,'纳秒，以便微波脉冲之间的上升沿到上升沿间距为',t_min,'纳秒的倍数。tau0 现在设置为', expCfg.tau0,'\
\n详细信息：XY8 序列中 pi 或 pi/2 脉冲的上升沿与后续 pi 或 pi/2 脉冲的上升沿之间的间距\
必须是',t_min,'纳秒的整数倍。用户输入的 tau0 定义为 XY8 序列中后续 pi 脉冲中心之间的时间。\
对于您的 pi 脉冲长度',expCfg.t_pi,'纳秒，您选择的 tau0 产生的边到边时间为', half_t_delay-(expCfg.t_pi/4),'纳秒，它不是',t_min,'纳秒的倍数。\
因此，我们将 tau0 移动',t_min/2,'纳秒。')
					
def calculateContrast(contrastMode,signal,background):
# 根据用户选择的对比度模式（在实验配置文件中配置，如 ESRconfig、Rabiconfig 等）计算对比度
	if contrastMode =='ratio_SignalOverReference':
		contrast = np.divide(signal,background)
	elif contrastMode =='ratio_DifferenceOverSum':
		contrast = np.divide(np.subtract(signal,background),np.add(signal,background))
	elif contrastMode == 'signalOnly':
		contrast = signal
	else:
		print('错误：无法识别的对比度模式。有效的对比度模式为：\'ratio_SignalOverReference\'、\'ratio_DifferenceOverSum\' 或 \'signalOnly\'。请编辑配置脚本中的 contrastMode 变量以匹配有效的对比度模式。')
		sys.exit()
	return contrast
	
def runExperiment(expConfigFile):
# 此函数运行实验，使用用户在实验配置文件（如 ESRconfig、Rabiconfig 等）中配置的输入参数，并绘制和保存数据。
	try:
		'''运行实验。'''
		expCfg = import_module(expConfigFile)
		expCfg.N_scanPts = len(expCfg.scannedParam) # 防止用户输入非整数的 N_scanPts。
		validateUserInput(expCfg)
		# 检查保存目录是否存在，如果不存在，则在当前目录中创建一个"Saved Data"文件夹，所有数据将保存到该目录。
		if not (isdir(expCfg.savePath)):
			makedirs(expCfg.savePath)
			print('警告：保存目录不存在，正在工作目录中创建名为 Saved_Data 的文件夹。数据将保存到此目录。')
		
		# 初始化 SRS 并对 PulseBlaster 进行编程
		SRS = SRSctl.initSRS(conCfg.GPIBaddr,conCfg.modelName)
		SRSctl.setSRS_RFAmplitude(SRS,expCfg.microwavePower)
		SRSctl.setupSRSmodulation(SRS,expCfg.sequence)
		sequenceArgs = expCfg.updateSequenceArgs()
		expParamList = expCfg.updateExpParamList()
		if expCfg.sequence != 'ESRseq':
			SRSctl.setSRS_Freq(SRS, expCfg.microwaveFrequency)
			# 对 PB 进行编程
			seqArgList = [expCfg.scannedParam[-1]]
			seqArgList.extend(sequenceArgs)
			instructionArray=PBctl.programPB(expCfg.sequence,seqArgList)
		else:
			SRSctl.setSRS_Freq(SRS, expCfg.scannedParam[0])
			# 对 PB 进行编程
			instructionArray=PBctl.programPB(expCfg.sequence,sequenceArgs)
		SRSctl.enableSRS_RFOutput(SRS)
					
		# 配置 DAQ
		DAQclosed = False
		DAQtask = DAQctl.configureDAQ(expCfg.Nsamples)
			
		if expCfg.plotPulseSequence:
		# 绘制序列
			plt.figure(0)
			[t_us,channelPulses,yTicks]=seqCtl.plotSequence(instructionArray,expCfg.PBchannels)
			for channel in channelPulses:
				plt.plot(t_us, list(channel))
				plt.yticks(yTicks)
				plt.xlabel('时间 (微秒)')
				plt.ylabel('通道')
				# 如果我们正在绘制脉冲长度 <5*t_min 的 Rabi 序列，在序列绘图标题中警告用户，发送到 PulseBlaster 微波通道的指令是针对 5*t_min 脉冲的，但同时会脉冲短脉冲标志以产生所需的脉冲长度
				if expCfg.sequence == 'RabiSeq' and (seqArgList[0]<(5*t_min)):
					plt.title('脉冲序列图（在最后一个扫描点）。关闭以继续实验...\n（注意：我们绘制发送到 PulseBlaster (PB) 每个通道的指令。对于微波脉冲<',5*t_min,'纳秒，微波\n通道 (PB_MW) 被指令脉冲',5*t_min,'纳秒，但 PB 的短脉冲标志同时被脉冲（未显示）以\n在 PB_MW 产生所需的输出脉冲长度。这可以在示波器上验证。）', fontsize=7)
				else:
					plt.title('脉冲序列图（在最后一个扫描点）\n 关闭以继续实验...')
			plt.show()
		
		# 初始化数据数组
		meanSignalCurrentRun = np.zeros(expCfg.N_scanPts)
		meanBackgroundCurrentRun = np.zeros(expCfg.N_scanPts)
		contrastCurrentRun = np.zeros(expCfg.N_scanPts)
		signal = np.zeros([expCfg.N_scanPts,expCfg.Navg])
		background = np.zeros([expCfg.N_scanPts,expCfg.Navg])
		contrast = np.zeros([expCfg.N_scanPts,expCfg.Navg])

		# 运行实验
		for i_run in range (0,expCfg.Navg):
			print('运行 ',i_run+1,' 共 ',expCfg.Navg)
			if expCfg.randomize:
				if i_run>0:
					shuffle(expCfg.scannedParam)
			for i_scanPoint in range (0, expCfg.N_scanPts):
				# 设置下一次扫描迭代（例如，对于 ESR 实验，改变微波频率；对于 T2 实验，用新的延迟重新编程 pulseblaster）
				if expCfg.sequence == 'ESRseq':
					SRSctl.setSRS_Freq(SRS, expCfg.scannedParam[i_scanPoint])
				else:
					seqArgList[0] = expCfg.scannedParam[i_scanPoint]
					instructionArray= PBctl.programPB(expCfg.sequence,seqArgList)
				print('扫描点 ',i_scanPoint+1,' 共 ',expCfg.N_scanPts)
				
				# 读取 DAQ
				cts=DAQctl.readDAQ(DAQtask,2*expCfg.Nsamples,expCfg.DAQtimeout)
		
				# 提取信号和背景计数
				sig = cts[0::2]
				bkgnd = cts[1::2]
							
				# 计算计数平均值
				meanSignalCurrentRun[i_scanPoint] = np.mean(sig)
				meanBackgroundCurrentRun[i_scanPoint] = np.mean(bkgnd)
				if expCfg.shotByShotNormalization:
					contrastCurrentRun[i_scanPoint] = np.mean(calculateContrast(expCfg.contrastMode,sig,bkgnd))
				else:
					contrastCurrentRun[i_scanPoint] = calculateContrast(expCfg.contrastMode,meanSignalCurrentRun[i_scanPoint],meanBackgroundCurrentRun[i_scanPoint])
				if i_run==0:
					if expCfg.livePlotUpdate:
						xValues=expCfg.scannedParam[0:i_scanPoint+1]
						plt.plot([x/expCfg.plotXaxisUnits for x in xValues],contrastCurrentRun[0:i_scanPoint+1], 'b-')
						plt.ylabel('对比度')
						plt.xlabel(expCfg.xAxisLabel)
						plt.draw()
						plt.pause(0.0001)
					
					# 根据 saveSpacing_inPulseLengthPts 的间隔和最终延迟点保存数据
					if (i_scanPoint%expCfg.saveSpacing_inScanPts == 0) or (i_scanPoint==expCfg.N_scanPts-1):
						data = np.zeros([i_scanPoint+1,3])
						data[:,0] = expCfg.scannedParam[0:i_scanPoint+1]
						data[:,1] = meanSignalCurrentRun[0:i_scanPoint+1]
						data[:,2] = meanBackgroundCurrentRun[0:i_scanPoint+1]
						dataFile = open(expCfg.dataFileName, 'w')
						for line in data:
							dataFile.write("%.0f\t%.8f\t%.8f\n" % tuple(line))
						paramFile = open(expCfg.paramFileName, 'w')
						expParamList[1] = i_scanPoint+1
						paramFile.write(expCfg.formattingSaveString % tuple(expParamList))
						dataFile.close()
						paramFile.close()
					
			# 按延迟递增顺序对当前运行的计数进行排序
			dataCurrentRun = np.transpose(np.array([expCfg.scannedParam,meanSignalCurrentRun,meanBackgroundCurrentRun,contrastCurrentRun]))
			sortingIndices = np.argsort(dataCurrentRun[:,0])
			dataCurrentRun = dataCurrentRun[sortingIndices]
			# 填充当前运行数据：
			sortedScanParam = dataCurrentRun[:,0]
			signal[:,i_run] = dataCurrentRun[:,1]
			background[:,i_run] = dataCurrentRun[:,2]
			contrast[:,i_run] = dataCurrentRun[:,3]
			
			# 更新绘图数量
			updatedSignal = np.mean(signal[:,0:i_run+1],1)
			updatedBackground = np.mean(background[:,0:i_run+1],1)
			updatedContrast = np.mean(contrast[:,0:i_run+1],1)
			
			# 更新绘图：
			if expCfg.livePlotUpdate: 
				plt.clf()
			plt.plot([x/expCfg.plotXaxisUnits for x in sortedScanParam] ,updatedContrast,'b-')
			plt.ylabel('对比度')
			plt.xlabel(expCfg.xAxisLabel)
			plt.draw()
			plt.pause(0.001)
			
			# 根据 saveSpacing_inAverages 的间隔和最终扫描后保存数据
			if (i_run%expCfg.saveSpacing_inAverages == 0) or (i_run==expCfg.Navg-1):
				data = np.zeros([expCfg.N_scanPts,3])
				data[:,0] = sortedScanParam
				data[:,1] = updatedSignal
				data[:,2] = updatedBackground
				dataFile = open(expCfg.dataFileName, 'w')
				for item in data:
					dataFile.write("%.0f\t%.8f\t%.8f\n" % tuple(item))
				paramFile = open(expCfg.paramFileName, 'w')
				expParamList[3] = i_run+1
				paramFile.write(expCfg.formattingSaveString % tuple(expParamList))
				dataFile.close()
				paramFile.close()
		
		# 关闭 SRS 输出
		SRSctl.disableSRS_RFOutput(SRS)

		# 关闭 DAQ 任务：
		DAQctl.closeDAQTask(DAQtask)
		DAQclosed=True
		plt.show()
	except KeyboardInterrupt:
		print('用户键盘中断。正在退出...')
		sys.exit()
	finally:
		if 'SRS' in vars():	
			# 关闭 SRS 输出
			SRSctl.disableSRS_RFOutput(SRS)
		if ('DAQtask' in vars()) and  (not DAQclosed):
			# 关闭 DAQ 任务：
			DAQctl.closeDAQTask(DAQtask)
			DAQclosed=True
	
if __name__ == "__main__":
	if len(sys.argv)>1 and (sys.argv[1] in ['ESRconfig','Rabiconfig','T1config','T2config','XY8config','correlSpecconfig']):
		expConfigFile=sys.argv[1]
	else:
		print('用法：python mainControl.py <ESRconfig|Rabiconfig|T1config|T2config|XY8config|correlSpecconfig>')
		sys.exit()
	runExperiment(expConfigFile)