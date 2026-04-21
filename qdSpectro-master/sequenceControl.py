#序列控制.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明和本许可声明应包含在软件的所有副本或实质性部分中。

# 本软件按"原样"提供，不附带任何形式的保证，
# 无论是明示的还是默示的，包括但不限于适销性、
# 特定用途的适用性和不侵权的保证。在任何情况下，
# 作者或版权持有人均不对任何索赔、损害或其他责任负责，
# 无论是在合同行为、侵权行为或其他情况下，
# 因软件或软件的使用或其他交易而产生或与之相关的。

import matplotlib.pyplot as plt
import math
import numpy as np
import sys
from collections import namedtuple
from spinapi import *
from connectionConfig import *

PBchannel = namedtuple('PBchannel',['channelNumber','startTimes','pulseDurations']) 

# 定义 t_min，PulseBlaster 的时间分辨率，由 1/(时钟频率) 给出：
t_min = 1e3/PBclk # 单位为 ns 

# 短脉冲标志：
ONE_PERIOD = 0x200000
TWO_PERIOD = 0x400000
THREE_PERIOD = 0x600000
FOUR_PERIOD = 0x800000 
FIVE_PERIOD= 0xA00000

def plotSequence(instructions,channelMasks):
	scalingFactor = 0.8
	t_ns = [0,0]
	pulses ={}
	tDone = False
	channelPulses=[]
	for channelMask in channelMasks.values():
		pulses[channelMask]=[0,channelMask&instructions[0][0]]
		for i in range(0, len(instructions)):
			currentPulseLength = instructions[i][3]
			if not tDone:
				previousEdgeTime = t_ns[-1]
				nextEdgeTime = previousEdgeTime + currentPulseLength
				t_ns.append(nextEdgeTime)
				t_ns.append(nextEdgeTime)
				if i == (len(instructions)-1):
					tDone = True
			if i==len(instructions)-1:
				pulses[channelMask].append(channelMask&instructions[i][0])
				pulses[channelMask].append(channelMask&instructions[i][0])
			else:
				pulses[channelMask].append(channelMask&instructions[i][0])
				pulses[channelMask].append(channelMask&instructions[i+1][0])
		t_us = np.divide(t_ns,1e3)
		channelPulses.append(list(np.add(math.log(channelMask,2),np.multiply(list(pulses[channelMask]),scalingFactor/channelMask))))
	yTicks = np.arange(math.log(min(channelMasks.values()),2), 1+math.log(max(channelMasks.values()),2),1)
	return [t_us,channelPulses,yTicks]



def sequenceEventCataloguer(channels):
	# 按照提供的通道上的连续上升沿对序列事件进行分类。返回一个字典 channelBitMasks，
	# 其键是事件（上升/下降沿）时间，值是指示此时哪些通道开启的通道位掩码。
	eventCatalog ={} # 字典，键是上升/下降沿时间，值是在该时间开启/关闭的通道位掩码
	for channel in channels:
		channelMask = channel.channelNumber
		endTimes = [startTime + pulseDuration for startTime, pulseDuration in zip(channel.startTimes,channel.pulseDurations)]
		for eventTime in channel.startTimes+endTimes:
			eventChannelMask = channelMask
			if eventTime in eventCatalog.keys():
				eventChannelMask = eventCatalog[eventTime]^channelMask 
				# 这里使用异或而不是或，以防序列中有人使用零长度脉冲。在这种情况下，
				# 异或确保通道在脉冲开始/结束时间不会开启。如果在这里使用或，它会开启并
				# 仅在下一个事件（本应是上升沿）时关闭，这会导致意外行为。
			eventCatalog[eventTime]=eventChannelMask
	channelBitMasks = {}
	currentBitMask=0
	channelBitMasks[0]=currentBitMask
	for event in sorted(eventCatalog.keys()):
		channelBitMasks[event]=currentBitMask^eventCatalog[event]
		currentBitMask = channelBitMasks[event]
	return channelBitMasks

################--------------------------------------------- PulseBlaster 序列s---------------------------------------------------###################
def makeSequence(sequence, args):
	"""根据序列名称和参数创建相应的脉冲序列
	
	参数:
		sequence: 序列名称字符串
		args: 传递给序列生成函数的参数
	
	返回:
		通道列表，每个通道包含通道号、脉冲开始时间和脉冲持续时间
	"""
	if sequence == 'ESRseq':
		return makeESRseq(*args)
	elif sequence == 'RabiSeq':
		return makeRabiSeq(*args)
	elif sequence == 'T1seq':
		return makeT1Seq(*args)
	elif sequence == 'T2seq':
		return makeT2Seq(*args)
	elif sequence == 'XY8seq':
		return makeXY8seq(*args)
	elif sequence == 'correlSpecSeq':
		return makecorrelationSpectSeq(*args)
	elif sequence == 'optimReadoutSeq':
		return makeReadoutDelaySweep(*args)
	elif sequence == 'PulsedODMRseq':
		return makePulsedODMRseq(*args)
	else:
		print('错误： 请求的序列未被识别。')
		sys.exit

def makeESRseq(t_duration):
	"""创建 ESR（电子自旋共振）序列
	
	参数:
		t_duration: 信号和参考脉冲的持续时间
	
	返回:
		通道列表，包括 AOM、DAQ、微波和起始触发通道
	"""
	t_sigAndref = 2*t_duration
	t_startTrig = t_min*round(300*ns/t_min)
	t_readout = t_min*round(300*ns/t_min)
	t_readoutBuffer= t_min*round(2*us/t_min)
	AOMchannel = PBchannel(AOM,[0],[t_sigAndref])
	uWchannel = PBchannel(uW,[0],[t_sigAndref/2])
	DAQchannel = PBchannel(DAQ,[(t_sigAndref/2)-t_readoutBuffer,t_sigAndref-t_readoutBuffer],[t_readout,t_readout])
	STARTtrigchannel = PBchannel(STARTtrig,[0],[t_startTrig])
	channels = [AOMchannel,DAQchannel,uWchannel, STARTtrigchannel]
	return channels

def makeReadoutDelaySweep(t_readoutDelay,t_AOM):
	"""创建读出延迟扫描序列
	
	参数:
		t_readoutDelay: 读出延迟时间
		t_AOM: AOM 脉冲持续时间
	
	返回:
		通道列表，包括 AOM、DAQ 和起始触发通道
	"""
	t_startTrig = t_min*round(300*ns/t_min)
	start_delay = t_min*round(5*us/t_min)-t_startTrig
	t_readout = t_min*round(300*ns/t_min)
	AOMchannel = PBchannel(AOM,[start_delay],[t_AOM])
	DAQchannel = PBchannel(DAQ,[start_delay+t_readoutDelay],[t_readout])
	STARTtrigchannel = PBchannel(STARTtrig,[start_delay+t_AOM],[2*t_min*round(5*us/t_min)+t_startTrig])
	channels=[AOMchannel,DAQchannel, STARTtrigchannel]
	return channels
	
def makeRabiSeq(t_uW,t_AOM,t_readoutDelay,t_wait):
	"""创建 Rabi 序列
	
	完整的 Rabi 测量周期包含两个半周期（信号和参考），每个半周期内：
	
	1. 自旋态初始化（光学极化）
	   - 施加 532nm 激光脉冲（AOM），将电子自旋极化到 |m_s=0⟩
	
	2. 等待与稳定
	   - 关闭激光，等待 ISC 通道弛豫回基态
	
	3. 自旋态相干操控（微波脉冲）
	   - 信号半周期：施加微波脉冲 (t_uW)
	   - 参考半周期：不施加微波（等待相同时间）
	
	4. 自旋态读取
	   - 施加读取激光脉冲（AOM），激发荧光
	   - DAQ 在读取激光开始后延迟 t_readoutDelay 开始采集
	
	参数:
		t_uW: 微波脉冲持续时间（扫描变量）
		t_AOM: AOM 脉冲持续时间（极化和读取激光）
		t_readoutDelay: 读取激光开始后延迟多久开始 DAQ 积分
		t_wait: 等待稳定时间（ISC 弛豫时间）
	
	返回:
		通道列表，包括微波（可能包含短脉冲通道）、AOM、DAQ 和起始触发通道
	"""
	t_startTrig = t_min * round(300*ns/t_min)
	t_readout = t_min * round(300*ns/t_min)
	uWtoAOM_delay = t_min * round(1*us/t_min)
	start_delay = t_min * round(1*us/t_min)
	
	# ============== 第一个半周期：信号（有微波） ==============
	# 阶段1：自旋态初始化 - 极化激光
	AOM_polarization1 = start_delay
	# 阶段2：等待与稳定
	wait_end1 = AOM_polarization1 + t_AOM + t_wait
	# 阶段3：微波脉冲
	uW_start1 = wait_end1
	# 阶段4：读取激光
	AOM_readout1 = uW_start1 + t_uW + uWtoAOM_delay
	# DAQ 采集
	DAQ_start1 = AOM_readout1 + t_readoutDelay
	firstHalfDuration = AOM_readout1 + t_AOM
	
	# ============== 第二个半周期：参考（无微波） ==============
	# 阶段1：极化激光
	AOM_polarization2 = firstHalfDuration
	# 阶段2：等待与稳定
	wait_end2 = AOM_polarization2 + t_AOM + t_wait
	# 阶段3：无微波（仅等待 t_uW 时间）
	# 阶段4：读取激光
	AOM_readout2 = wait_end2 + t_uW + uWtoAOM_delay
	# DAQ 采集
	DAQ_start2 = AOM_readout2 + t_readoutDelay
	
	# ============== 创建通道 ==============
	# AOM 通道：4 个脉冲 [极化1, 读取1, 极化2, 读取2]
	AOMchannel = PBchannel(AOM,
		[AOM_polarization1, AOM_readout1, AOM_polarization2, AOM_readout2],
		[t_AOM, t_AOM, t_AOM, t_AOM])
	
	# 微波通道：仅在信号半周期开启
	if t_uW <= 5*t_min and t_uW > 0:
		uWchannel = PBchannel(uW, [uW_start1], [5*t_min])
		shortpulseFLAG = int((t_uW/2) * ONE_PERIOD)
		shortPulseChannel = PBchannel(shortpulseFLAG, [uW_start1], [5*t_min])
		channels = [shortPulseChannel, uWchannel]
	else:
		uWchannel = PBchannel(uW, [uW_start1], [t_uW])
		channels = [uWchannel]
	
	# DAQ 通道：在两个半周期的读出窗口采集
	DAQchannel = PBchannel(DAQ, [DAQ_start1, DAQ_start2], [t_readout, t_readout])
	
	# 起始触发
	STARTtrigchannel = PBchannel(STARTtrig, [0], [t_startTrig])
	
	channels.extend([AOMchannel, DAQchannel, STARTtrigchannel])
	return channels

def makeT1Seq(t_delay,t_AOM,t_readoutDelay,t_pi):
	"""创建 T1 序列
	
	参数:
		t_delay: 自旋弛豫延迟时间
		t_AOM: AOM 脉冲持续时间
		t_readoutDelay: 读出延迟时间
		t_pi: π 脉冲持续时间
	
	返回:
		通道列表，包括 AOM、DAQ、微波和起始触发通道
	"""
	t_startTrig = t_min*round(300*ns/t_min)
	t_readout = t_min*round(300*ns/t_min)
	uWtoAOM_delay =t_min*round(1*us/t_min)
	AOMstartTime1 = t_delay
	firstHalfDuration=AOMstartTime1+t_AOM
	AOMstartTime2 =  firstHalfDuration+AOMstartTime1 
	AOMchannel = PBchannel(AOM,[AOMstartTime1,AOMstartTime2],[t_AOM,t_AOM])
	uWchannel = PBchannel(uW,[firstHalfDuration +t_readoutDelay + t_min*round(1*us/t_min)],[t_pi])
	DAQchannel = PBchannel(DAQ,[AOMstartTime1+t_readoutDelay, AOMstartTime2+t_readoutDelay],[t_readout,t_readout])
	STARTtrigchannel = PBchannel(STARTtrig,[0],[t_startTrig])
	channels = [AOMchannel,DAQchannel,uWchannel, STARTtrigchannel]
	return channels
	
def makeT2Seq(t_delay,t_AOM,t_readoutDelay,t_pi,IQpadding, numberOfPiPulses):
	"""创建 T2 序列（使用 CPMG 脉冲序列）
	
	参数:
		t_delay: π 脉冲之间的延迟时间
		t_AOM: AOM 脉冲持续时间
		t_readoutDelay: 读出延迟时间
		t_pi: π 脉冲持续时间
		IQpadding: IQ 调制补偿延时
		numberOfPiPulses: π 脉冲数量
	
	返回:
		通道列表，包括 AOM、DAQ、微波、I 和 Q 通道以及起始触发通道
	"""
	t_piby2=t_pi/2
	t_startTrig = t_min*round(300*ns/t_min)
	t_readout = t_min*round(300*ns/t_min)
	uWtoAOM_delay =t_min*round(1*us/t_min)
	start_delay = (t_min*round(1*us/t_min) + t_readoutDelay) 
	# 为序列的信号半部分创建脉冲：
	[uWstartTimes1,uWdurations,IstartTimes1,Idurations,QstartTimes1,Qdurations]= makeCPMGpulses(start_delay,numberOfPiPulses,t_delay,t_pi, t_piby2,IQpadding)
	CPMGduration = uWstartTimes1[-1]+t_piby2-start_delay
	AOMstartTime1 = start_delay+CPMGduration +uWtoAOM_delay
	DAQstartTime1 = AOMstartTime1+t_readoutDelay
	firstHalfDuration = AOMstartTime1+t_AOM 
	# 为序列的背景半部分创建脉冲：
	uWstartTimes2 =[x+firstHalfDuration for x in uWstartTimes1]
	# IstartTimes2 = [x+firstHalfDuration for x in IstartTimes1]
	QstartTimes2nd = QstartTimes1[:-1]
	QstartTimes2 = [x+firstHalfDuration for x in QstartTimes2nd]
	AOMstartTime2 = firstHalfDuration + AOMstartTime1
	DAQstartTime2 = firstHalfDuration + DAQstartTime1
	# 创建完整的微波、I 和 Q 脉冲列表
	uWstartTimes=uWstartTimes1 +uWstartTimes2
	# 创建通道：
	AOMchannel 		 = PBchannel(AOM,[AOMstartTime1,AOMstartTime2],[t_AOM,t_AOM])
	DAQchannel 		 = PBchannel(DAQ,[DAQstartTime1,DAQstartTime2],[t_readout,t_readout])
	uWchannel  		 = PBchannel(uW,uWstartTimes1 +uWstartTimes2,uWdurations+uWdurations)
	Ichannel   		 = PBchannel(I,IstartTimes1,Idurations)
	Qchannel   		 = PBchannel(Q,QstartTimes1+QstartTimes2,Qdurations+Qdurations[:-1])
	STARTtrigchannel = PBchannel(STARTtrig,[0],[t_startTrig])
	channels=[AOMchannel,DAQchannel, uWchannel, Ichannel, Qchannel, STARTtrigchannel]
	return channels
	
def makeXY8seq(t_delay,t_AOM,t_readoutDelay,t_pi,IQpadding, numberOfRepeats):
	"""创建 XY8 序列
	
	参数:
		t_delay: π 脉冲之间的延迟时间
		t_AOM: AOM 脉冲持续时间
		t_readoutDelay: 读出延迟时间
		t_pi: π 脉冲持续时间
		IQpadding: IQ 调制补偿延时
		numberOfRepeats: XY8 脉冲序列的重复次数
	
	返回:
		通道列表，包括 AOM、DAQ、微波、I 和 Q 通道以及起始触发通道
	"""
	t_piby2=t_pi/2
	t_startTrig = t_min*round(300*ns/t_min)
	t_readout = t_min*round(300*ns/t_min)
	uWtoAOM_delay =t_min*round(1*us/t_min)
	start_delay = (t_min*round(1*us/t_min) + t_readoutDelay) 
	# 为序列的信号半部分创建脉冲：
	[uWstartTimes1,uWdurations,IstartTimes1,Idurations,QstartTimes1,Qdurations]= makeXY8pulses(start_delay,numberOfRepeats,t_delay,t_pi, t_piby2,IQpadding)
	XY8duration = uWstartTimes1[-1]+t_pi/2-start_delay
	AOMstartTime1 = start_delay+XY8duration +uWtoAOM_delay
	DAQstartTime1 = AOMstartTime1+t_readoutDelay
	firstHalfDuration = AOMstartTime1+t_AOM 
	# 为序列的背景半部分创建脉冲：
	uWstartTimes2 =[x+firstHalfDuration for x in uWstartTimes1]
	QstartTimes2nd = QstartTimes1[:-1]
	QstartTimes2 = [x+firstHalfDuration for x in QstartTimes2nd]
	AOMstartTime2 = firstHalfDuration + AOMstartTime1
	DAQstartTime2 = firstHalfDuration + DAQstartTime1
	# 创建通道：
	AOMchannel 		 = PBchannel(AOM,[AOMstartTime1,AOMstartTime2],[t_AOM,t_AOM])
	DAQchannel 		 = PBchannel(DAQ,[DAQstartTime1,DAQstartTime2],[t_readout,t_readout])
	uWchannel  		 = PBchannel(uW,uWstartTimes1 +uWstartTimes2,uWdurations+uWdurations)
	Ichannel   		 = PBchannel(I,IstartTimes1,Idurations)
	Qchannel   		 = PBchannel(Q,QstartTimes1+QstartTimes2,Qdurations+Qdurations[:-1])
	STARTtrigchannel = PBchannel(STARTtrig,[0],[t_startTrig])
	channels=[AOMchannel,DAQchannel, uWchannel, Ichannel, Qchannel, STARTtrigchannel]
	return channels
	
	
def makecorrelationSpectSeq(t_delay_betweenXY8seqs,t_delay, t_AOM,t_readoutDelay,t_pi,IQpadding,numberOfRepeats):
	"""创建相关光谱序列
	
	参数:
		t_delay_betweenXY8seqs: XY8 序列之间的延迟时间
		t_delay: XY8 序列中 π 脉冲之间的延迟时间
		t_AOM: AOM 脉冲持续时间
		t_readoutDelay: 读出延迟时间
		t_pi: π 脉冲持续时间
		IQpadding: IQ 调制补偿延时
		numberOfRepeats: XY8 脉冲序列的重复次数
	
	返回:
		通道列表，包括 AOM、DAQ、微波、I 和 Q 通道以及起始触发通道
	"""
	t_piby2=t_pi/2
	t_startTrig = t_min*round(300*ns/t_min)
	t_readout = t_min*round(300*ns/t_min)
	uWtoAOM_delay =t_min*round(1*us/t_min)
	start_delay = t_min*round(2*us/t_min)
	# 为序列第一半中的第一个 XY8 创建脉冲（I 仅在第二半的第二个 XY8 中脉冲，因此我们在这里获取 I 时间并在时间上偏移）：
	[uWstartTimes1a,uWdurations1a,IstartTimes,Idurations,QstartTimes1a,Qdurations1a]= makeXY8pulses(start_delay,numberOfRepeats,t_delay,t_pi, t_piby2,IQpadding)
	# 为序列第一半中的第二个 XY8 创建脉冲：
	firstXY8duration = uWstartTimes1a[-1]+t_piby2
	uWstartTimes1b = [x+firstXY8duration + t_delay_betweenXY8seqs for x in uWstartTimes1a]
	QstartTimes1b = [x +firstXY8duration + t_delay_betweenXY8seqs for x in QstartTimes1a]
	Qdurations1b = Qdurations1a
	# 为信号半部分创建 AOM 脉冲和 DAQ 脉冲
	XY8duration = uWstartTimes1b[-1]+t_pi/2-start_delay
	AOMstartTime1 = start_delay+XY8duration +uWtoAOM_delay
	DAQstartTime1 = AOMstartTime1+t_readoutDelay
	firstHalfDuration = AOMstartTime1+t_AOM 
		
	# 为序列第二半中的第一个 XY8 创建脉冲（此半部分没有 I 脉冲）：
	uWstartTimes2 = [x+firstHalfDuration for x in uWstartTimes1a+uWstartTimes1b]
	QstartTimes2 = [x+firstHalfDuration for x in QstartTimes1a+QstartTimes1b[:-1]]
	AOMstartTime2 = firstHalfDuration + AOMstartTime1
	DAQstartTime2 = firstHalfDuration + DAQstartTime1
	IstartTimes = [x +firstHalfDuration+firstXY8duration+t_delay_betweenXY8seqs for x in IstartTimes]
	
	# 连接脉冲时间：
	uWstartTimes = uWstartTimes1a+uWstartTimes1b+uWstartTimes2
	uWdurations = uWdurations1a*4
	QstartTimes = QstartTimes1a+QstartTimes1b+QstartTimes2
	Qdurations = Qdurations1a+Qdurations1b+Qdurations1a+Qdurations1b[:-1]
	
	# 创建通道：
	AOMchannel 		 = PBchannel(AOM,[AOMstartTime1,AOMstartTime2],[t_AOM,t_AOM])
	DAQchannel 		 = PBchannel(DAQ,[DAQstartTime1,DAQstartTime2],[t_readout,t_readout])
	uWchannel  		 = PBchannel(uW,uWstartTimes,uWdurations)
	Ichannel   		 = PBchannel(I,IstartTimes,Idurations)
	Qchannel   		 = PBchannel(Q,QstartTimes,Qdurations)
	STARTtrigchannel = PBchannel(STARTtrig,[0],[t_startTrig])
	channels=[AOMchannel,DAQchannel, uWchannel, Ichannel, Qchannel, STARTtrigchannel]
	return channels

def makePulsedODMRseq(scanned_param, t_pi, t_p, t_wait, t_readoutLaser, t_readoutDelay, t_integration):
	"""创建脉冲ODMR序列

	一个完整的脉冲ODMR测试周期包含四个阶段：

	1. 自旋态初始化（极化）
	   - 施加532nm激光脉冲，将电子自旋极化到基态|m_s=0⟩
	   - 参数：t_p（激光脉冲宽度，通常300µs量级）

	2. 等待与稳定
	   - 关闭激光，等待电子通过ISC通道弛豫回基态
	   - 参数：t_wait（等待时间，通常3-5µs）

	3. 自旋态操控（翻转）
	   - 施加微波π脉冲，频率f以步进值扫描
	   - 参数：t_pi（π脉冲宽度，由Rabi实验测定）

	4. 自旋态读取
	   - 施加第二个激光脉冲，激发荧光并重新极化自旋
	   - 注意：读取光脉冲必须紧接在微波脉冲之后，中间无延迟，以避免自旋在读取前发生不必要的弛豫
	   - 参数：t_readoutLaser（读取激光脉冲宽度，用于激发荧光和ISC重新极化）
	   - 荧光信号收集：仅在读取激光开始后延迟t_readoutDelay的时刻起，采集短时间窗口t_integration
	   - 参数：t_integration（积分时间，通常200-500ns）

	差分设计：每个测试周期包含两个子序列（MW_on和MW_off）用于噪声抑制。
	MW_on有微波脉冲，MW_off无微波脉冲。

	参数:
		scanned_param: 扫描参数（这里是频率）的最后一个值
		t_pi: π脉冲持续时间（由Rabi实验测定）
		t_p: 自旋极化激光脉冲宽度
		t_wait: 等待稳定时间（让电子通过ISC通道弛豫回基态）
		t_readoutLaser: 读取激光脉冲宽度（用于激发荧光和ISC重新极化）
		t_readoutDelay: 读取激光开始后延迟多久开始DAQ积分
		t_integration: DAQ积分窗口宽度（荧光信号采集时间）

	返回:
		通道列表，包括 AOM、DAQ、微波和起始触发通道
	"""
	t_pi = t_min * round(t_pi / t_min)
	t_p = t_min * round(t_p / t_min)
	t_wait = t_min * round(t_wait / t_min)
	t_readoutLaser = t_min * round(t_readoutLaser / t_min)
	t_readoutDelay = t_min * round(t_readoutDelay / t_min)
	t_integration = t_min * round(t_integration / t_min)

	t_startTrig = t_min * round(300*ns/t_min)
	uWtoAOM_delay = 0
	start_delay = t_min * round(10*us/t_min)

	# ==================== 子序列A：MW_on（带微波脉冲） ====================
	# 阶段1：自旋态初始化 - 施加激光脉冲极化到|m_s=0⟩
	AOM_polarization1 = start_delay
	# 阶段2：等待与稳定 - 关闭激光，等待ISC弛豫
	wait_end1 = AOM_polarization1 + t_p + t_wait
	# 阶段3：自旋态操控 - 施加微波π脉冲
	uW_start1 = wait_end1
	# 阶段4：自旋态读取 - 施加读取激光，激发荧光
	AOM_readout1 = uW_start1 + t_pi + uWtoAOM_delay
	# DAQ积分窗口开始：读取激光开始后延迟t_readoutDelay
	DAQ_start1 = AOM_readout1 + t_readoutDelay

	subsequenceA_duration = AOM_readout1 + t_readoutLaser

	# ==================== 子序列B：MW_off（无微波脉冲，作为参考） ====================
	# 阶段1：自旋态初始化 - 与MW_on相同
	AOM_polarization2 = subsequenceA_duration
	# 阶段2：等待与稳定 - 与MW_on相同
	wait_end2 = AOM_polarization2 + t_p + t_wait
	# 阶段3：无微波脉冲 - 仅等待t_pi时间保持结构一致
	# 阶段4：自旋态读取 - 与MW_on相同
	AOM_readout2 = wait_end2 + t_pi + uWtoAOM_delay
	DAQ_start2 = AOM_readout2 + t_readoutDelay

	# AOM通道：4个脉冲 [极化1, 读取1, 极化2, 读取2]
	AOMchannel = PBchannel(AOM,
		[AOM_polarization1, AOM_readout1, AOM_polarization2, AOM_readout2],
		[t_p, t_readoutLaser, t_p, t_readoutLaser])

	# 微波通道：仅在子序列A（MW_on）的阶段3施加π脉冲
	uWchannel = PBchannel(uW, [uW_start1], [t_pi])

	# DAQ通道：在积分窗口期间采集荧光（仅采集读取激光开始后的一小段时间）
	DAQchannel = PBchannel(DAQ,
		[DAQ_start1, DAQ_start2],
		[t_integration, t_integration])

	# 起始触发通道
	STARTtrigchannel = PBchannel(STARTtrig, [0], [t_startTrig])

	channels = [AOMchannel, uWchannel, DAQchannel, STARTtrigchannel]
	return channels		
def makeCPMGpulses(start_delay,numberOfPiPulses,t_delay,t_pi, t_piby2,IQpadding):
	"""创建 CPMG（Carr-Purcell-Meiboom-Gill）脉冲序列
	
	参数:
		start_delay: 序列开始延迟
		numberOfPiPulses: π 脉冲数量
		t_delay: π 脉冲之间的延迟时间
		t_pi: π 脉冲持续时间
		t_piby2: π/2 脉冲持续时间
		IQpadding: IQ 调制补偿延时
	
	返回:
		包含微波、I 和 Q 通道脉冲开始时间和持续时间的列表
	"""
	t_piby4 = t_piby2/2;
	if numberOfPiPulses == 1:
		uWstartTimes = [start_delay, start_delay +t_delay-t_piby4, start_delay +2*t_delay] 
		uWdurations =  [t_piby2, t_pi, t_piby2]
	else:
		half_t_delay = t_delay/2
		# 通过添加初始 π/2 和第一个 π 脉冲开始序列
		uWstartTimes =[start_delay, start_delay +half_t_delay-t_piby4] 
		uWdurations =[t_piby2, t_pi]
		# 添加剩余的 π 脉冲：
		for i in range(1,numberOfPiPulses):
			currentEdgeTime = uWstartTimes[-1]+t_delay
			uWstartTimes.append(currentEdgeTime)
			uWdurations.append(t_pi)
		# 添加最终的 π/2 脉冲：
		uWstartTimes.append(uWstartTimes[-1]+half_t_delay+t_piby4)
		uWdurations.append(t_piby2)
	# 创建 I 和 Q 通道脉冲：
	# Q 在 π(y) 脉冲和最终的 π/2(-x) 脉冲期间开启，但在第一个 π/2(x) 脉冲期间不开启
	QstartTimes = [x-IQpadding for x in uWstartTimes[1:]]
	Qdurations=[x +2*IQpadding for x in uWdurations[1:]]
	# I 仅在最终的 π/2(-x) 脉冲期间开启：
	IstartTimes =[x-IQpadding for x in [uWstartTimes[-1]]]
	Idurations =[x +2*IQpadding for x in [uWdurations[-1]]]
	return [uWstartTimes,uWdurations,IstartTimes,Idurations,QstartTimes,Qdurations]
	
def makeXY8pulses(start_delay,numberOfRepeats,t_delay,t_pi, t_piby2,IQpadding):
	"""创建 XY8 脉冲序列
	
	参数:
		start_delay: 序列开始延迟
		numberOfRepeats: XY8 脉冲序列的重复次数
		t_delay: π 脉冲之间的延迟时间
		t_pi: π 脉冲持续时间
		t_piby2: π/2 脉冲持续时间
		IQpadding: IQ 调制补偿延时
	
	返回:
		包含微波、I 和 Q 通道脉冲开始时间和持续时间的列表
	"""
	t_piby4=t_piby2/2
	# 通过添加初始 π/2 开始序列：
	half_t_delay = t_delay/2
	uWstartTimes =[start_delay] 
	uWdurations =[t_piby2]
	QstartTimes=[]
	Qdurations =[]
	# 添加剩余的 π 脉冲：
	firstPiPulseDone = False
	for i in range(0,numberOfRepeats):
		# 创建接下来的 8 个 π 脉冲：
		next8piPulseStartTimes =[]
		next8piPulseDurations=[]
		# 添加 8 个脉冲中的第一个脉冲
		currentEdgeTime=0
		if not firstPiPulseDone:
			currentEdgeTime = uWstartTimes[-1]+half_t_delay-t_piby4
			firstPiPulseDone=True
		else:
			currentEdgeTime = uWstartTimes[-1]+t_delay
		next8piPulseStartTimes.append(currentEdgeTime)
		next8piPulseDurations.append(t_pi)
		for j in range (1,8):
			newEdgeTime = next8piPulseStartTimes[-1]+t_delay
			next8piPulseStartTimes.append(newEdgeTime)
			next8piPulseDurations.append(t_pi)
		# 创建接下来的 8 个 Q 开始时间（Q 仅在 xy8 π 脉冲的第 1、3、4、6 个脉冲期间开启，对于 0 索引序列）：
		next8QstartTimes = list(next8piPulseStartTimes[i] for i in [1,3,4,6])
		next8Qdurations = list(next8piPulseDurations[i] for i in [1,3,4,6])
		# 将接下来的 8 个 π 脉冲和 Q 脉冲追加到开始时间列表：
		uWstartTimes.extend(next8piPulseStartTimes)
		uWdurations.extend(next8piPulseDurations)
		QstartTimes.extend(next8QstartTimes)
		Qdurations.extend(next8Qdurations)
		
	# 添加最终的 π/2 脉冲：
	uWstartTimes.append(uWstartTimes[-1]+half_t_delay+t_piby4)
	uWdurations.append(t_piby2)
	# 将最终的 π/2 脉冲追加到 Q 通道，因为（在信号仓中）Q 在该脉冲期间开启，因为它是一个 -x 脉冲。
	QstartTimes.append(uWstartTimes[-1])
	Qdurations.append(uWdurations[-1])
	# 为 Q 通道脉冲添加补偿延时：
	QstartTimes = [x-IQpadding for x in QstartTimes]
	Qdurations=[x +2*IQpadding for x in Qdurations]
	# 创建 I 通道脉冲。I 仅在最终的 π/2(-x) 脉冲期间开启：
	IstartTimes =[x-IQpadding for x in [uWstartTimes[-1]]]
	Idurations =[x +2*IQpadding for x in [uWdurations[-1]]]
	return [uWstartTimes,uWdurations,IstartTimes,Idurations,QstartTimes,Qdurations]
	

