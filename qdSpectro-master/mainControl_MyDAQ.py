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
import os
import sys
# 确保工作目录是脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

import connectionConfig as conCfg
import sequenceControl as seqCtl
import SRScontrol as SRSctl
# 使用针对MyDAQ优化的DAQ控制模块
import DAQcontrol_MyDAQ as DAQctl
import PBcontrol as PBctl
import matplotlib.pyplot as plt
# 设置中文字体，解决字体警告问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
import numpy as np
from spinapi import ms,us,ns
from random import shuffle
from os.path import isdir 
from os import makedirs
import math
from importlib import import_module
from time import localtime, strftime, sleep as time_sleep
import time


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

	# 检查 PulsedODMRseq 的特定参数：
	if expCfg.sequence == 'PulsedODMRseq':
		if expCfg.t_readoutDelay%t_min:
			print('错误：t_readoutDelay 设置为', expCfg.t_readoutDelay,'纳秒，它不是',t_min,'纳秒的倍数。请将 t_readoutDelay 设置为',t_min,'纳秒的整数倍。')
			sys.exit()
		if expCfg.t_readoutLaser<t_min or expCfg.t_readoutLaser%t_min:
			print('错误：t_readoutLaser 设置为', expCfg.t_readoutLaser,'纳秒，它必须大于',t_min,'纳秒且是',t_min,'纳秒的整数倍。')
			sys.exit()
		if expCfg.t_integration<t_min or expCfg.t_integration%t_min:
			print('错误：t_integration 设置为', expCfg.t_integration,'纳秒，它必须大于',t_min,'纳秒且是',t_min,'纳秒的整数倍。')
			sys.exit()
		if expCfg.t_integration > expCfg.t_readoutLaser:
			print('错误：t_integration（', expCfg.t_integration,'纳秒）不能大于 t_readoutLaser（', expCfg.t_readoutLaser,'纳秒）！')
			sys.exit()
	
	# 检查 PulsedODMRseq 中的 t_pi 是否是 t_min 的倍数且大于 t_min：
	if expCfg.sequence == 'PulsedODMRseq':
		if expCfg.t_pi<t_min or expCfg.t_pi%t_min:
			print('错误：请求的 pi 脉冲长度',expCfg.t_pi,'纳秒要么小于',t_min,'纳秒，要么不是',t_min,'纳秒的整数倍。')
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


def save_differential_data_and_plot(expCfg, x_data, signal, background, contrast, dateTimeStr):
	"""保存差分数据和生成图片"""
	# 检查是否启用了差分数据保存
	save_diff_data = getattr(expCfg, 'saveDifferentialData', True)
	save_plots_flag = getattr(expCfg, 'savePlots', True)
	
	if not save_diff_data and not save_plots_flag:
		return
	
	# 对比度归一化（0-1范围）
	print("\n对比度归一化:")
	print(f"原始对比度范围: {np.min(contrast):.4f} ~ {np.max(contrast):.4f}")
	
	# 计算归一化对比度
	contrast_min = np.min(abs(contrast))
	contrast_max = np.max(abs(contrast))
	
	if contrast_max > contrast_min:
		normalized_contrast = 1-(abs(contrast_max) - abs(contrast)) / contrast_max
	else:
		normalized_contrast = np.zeros_like(contrast)
	
	print(f"归一化对比度范围: {np.min(normalized_contrast):.4f} ~ {np.max(normalized_contrast):.4f}")
	
	if save_diff_data:
		# 创建差分数据文件名
		diff_data_file = expCfg.savePath + "differential_data_" + dateTimeStr + ".txt"
		
		# 计算差分数据
		differential_data = np.zeros([len(x_data), 6])
		differential_data[:, 0] = x_data
		differential_data[:, 1] = signal
		differential_data[:, 2] = background
		differential_data[:, 3] = contrast
		differential_data[:, 4] = signal - background  # 差分信号
		differential_data[:, 5] = normalized_contrast  # 归一化对比度
		
		# 保存差分数据
		with open(diff_data_file, 'w') as f:
			f.write("# 扫描参数\t信号\t背景\t对比度\t差分信号\t归一化对比度\n")
			for item in differential_data:
				f.write("%.6f\t%.8f\t%.8f\t%.8f\t%.8f\t%.8f\n" % tuple(item))
		
		print(f"✅ 差分数据已保存到: {diff_data_file}")
	
	# 生成并保存图片
	if save_plots_flag:
		save_plots(expCfg, x_data, signal, background, contrast, normalized_contrast, dateTimeStr)


def save_plots(expCfg, x_data, signal, background, contrast, normalized_contrast, dateTimeStr):
	"""生成并保存实验图片"""
	# 创建图片文件名
	plot_file_prefix = expCfg.savePath + expCfg.saveFileName + dateTimeStr
	
	# 创建综合对比度图
	plt.figure(figsize=(12, 8))
	
	# 子图1：原始对比度曲线
	plt.subplot(2, 2, 1)
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], contrast, 'b-', linewidth=2)
	plt.ylabel('原始对比度')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('原始对比度曲线')
	plt.grid(True)
	
	# 子图2：归一化对比度曲线
	plt.subplot(2, 2, 2)
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], normalized_contrast, 'g-', linewidth=2)
	plt.ylabel('归一化对比度 (0-1)')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('归一化对比度曲线')
	plt.grid(True)
	
	# 子图3：信号和背景曲线
	plt.subplot(2, 2, 3)
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], signal, 'r-', label='信号', linewidth=2)
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], background, 'm-', label='背景', linewidth=2)
	plt.ylabel('荧光强度')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('信号和背景曲线')
	plt.legend()
	plt.grid(True)
	
	# 子图4：差分信号曲线
	plt.subplot(2, 2, 4)
	differential_signal = signal - background
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], differential_signal, 'c-', linewidth=2)
	plt.ylabel('差分信号')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('差分信号曲线')
	plt.grid(True)
	
	plt.tight_layout()
	plt.savefig(plot_file_prefix + '_summary.png', dpi=300, bbox_inches='tight')
	plt.close()
	
	# 创建单独的原始对比度图
	plt.figure(figsize=(10, 6))
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], contrast, 'b-', linewidth=2)
	plt.ylabel('原始对比度')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('实验原始对比度曲线')
	plt.grid(True)
	plt.savefig(plot_file_prefix + '_contrast.png', dpi=300, bbox_inches='tight')
	plt.close()
	
	# 创建单独的归一化对比度图
	plt.figure(figsize=(10, 6))
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], normalized_contrast, 'g-', linewidth=2)
	plt.ylabel('归一化对比度 (0-1)')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('实验归一化对比度曲线')
	plt.grid(True)
	plt.savefig(plot_file_prefix + '_normalized_contrast.png', dpi=300, bbox_inches='tight')
	plt.close()
	
	# 创建差分信号图
	plt.figure(figsize=(10, 6))
	differential_signal = signal - background
	plt.plot([x/expCfg.plotXaxisUnits for x in x_data], differential_signal, 'c-', linewidth=2)
	plt.ylabel('差分信号 (信号 - 背景)')
	plt.xlabel(expCfg.xAxisLabel)
	plt.title('差分信号曲线')
	plt.grid(True)
	plt.savefig(plot_file_prefix + '_differential.png', dpi=300, bbox_inches='tight')
	plt.close()
	
	print(f"✅ 实验图片已保存到: {plot_file_prefix}_*.png")
	
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
		
		# 初始化B210相关变量
		B210_available = False
		B210 = None
		
		# 初始化 B210 并对 PulseBlaster 进行编程
		try:
			B210 = SRSctl.initSRS(conCfg.GPIBaddr,conCfg.modelName)
			B210_available = True
			print("✅ B210信号发生器初始化成功")
		except Exception as e:
			print(f"警告：无法初始化B210信号发生器: {e}")
			print("将跳过B210相关操作，继续执行其他功能")
			B210_available = False
			B210 = None
		
		# 确保必要的配置参数存在
		if not hasattr(expCfg, 'plotXaxisUnits'):
			expCfg.plotXaxisUnits = 1.0
		if not hasattr(expCfg, 'xAxisLabel'):
			expCfg.xAxisLabel = "Frequency (Hz)"
		if not hasattr(expCfg, 'formattingSaveString'):
			expCfg.formattingSaveString = "json"
		if not hasattr(expCfg, 'PBchannels'):
			expCfg.PBchannels = {"I": 0x01, "Q": 0x02, "STARTtrig": 0x04, "DAQ": 0x08, "AOM": 0x10, "MW": 0x20}

		# 继续执行其他操作
		sequenceArgs = expCfg.updateSequenceArgs()
		# 调用updateExpParamList函数获取参数列表和文件名
		expParamList, dataFileName, paramFileName = expCfg.updateExpParamList()
		expCfg.dataFileName = dataFileName
		expCfg.paramFileName = paramFileName

		# 对 PB 进行编程
		if expCfg.sequence != 'ESRseq':
			if B210_available:
				SRSctl.setSRS_Freq(B210, expCfg.microwaveFrequency)
			seqArgList = [expCfg.scannedParam[-1]]
			seqArgList.extend(sequenceArgs)
			instructionArray=PBctl.programPB(expCfg.sequence,seqArgList)
		else:
			if B210_available:
				SRSctl.setSRS_Freq(B210, expCfg.scannedParam[0])
			# 对 PB 进行编程
			instructionArray=PBctl.programPB(expCfg.sequence,sequenceArgs)

		# 启用 B210 输出（如果可用）
		if B210_available:
			# B210使用增益单位（dB），而不是功率单位（dBm）
			# 从配置文件中获取B210增益值
			if hasattr(expCfg, 'B210_gain'):
				gain_value = expCfg.B210_gain
			else:
				gain_value = 60  # 默认值
			print(f"使用B210增益值: {gain_value} dB")
			SRSctl.setSRS_RFAmplitude(B210, gain_value)
			SRSctl.setupSRSmodulation(B210,expCfg.sequence)
			SRSctl.enableSRS_RFOutput(B210)
			
		# 配置 DAQ
		DAQclosed = False
		software_delay = 0  # 软件延迟时间（秒）
		# 根据序列类型配置DAQ
		if expCfg.sequence == 'ESRseq':
			# 对于ESRseq，使用基于时间和样本数的配置
			# 每个样本组的时间是2*t_duration（信号+参考）
			acquisitionTimePerSample_ns = 2 * expCfg.t_duration
			print(f"ESRseq模式：每个样本组时间 = {acquisitionTimePerSample_ns} ns, 样本组数 = {expCfg.Nsamples}")
			result = DAQctl.configureDAQbyTime(acquisitionTimePerSample_ns, expCfg.Nsamples)
			if result is None:
				print("错误：DAQ配置失败，无法继续实验")
				sys.exit(1)
			DAQtask, actualTotalSamples, software_delay = result
		elif expCfg.sequence == 'RabiSeq':
			# 对于RabiSeq，使用专门的Rabi配置函数
			# 获取Rabi实验所需的参数
			t_AOM = expCfg.t_AOM
			t_readoutDelay = expCfg.t_readoutDelay
			t_wait = expCfg.t_wait
			# 使用最大的微波脉冲持续时间来配置DAQ，确保覆盖所有扫描点
			max_t_uW = max(expCfg.scannedParam)
			print(f"RabiSeq模式：使用最大微波脉冲持续时间 = {max_t_uW} ns")
			result = DAQctl.configureDAQforRabi(expCfg.Nsamples, t_AOM, t_readoutDelay, t_wait, max_t_uW)
			if result is None:
				print("错误：DAQ配置失败，无法继续实验")
				sys.exit(1)
			DAQtask, software_delay = result
		else:
			# 其他序列使用传统的样本数配置
			# 将t_duration转换为微秒单位
			t_duration_us = expCfg.t_duration / 1e3
			DAQtask = DAQctl.configureDAQ(expCfg.Nsamples, t_duration_us)
			if DAQtask is None:
				print("错误：DAQ配置失败，无法继续实验")
				sys.exit(1)
			
		if expCfg.plotPulseSequence:
			# 绘制序列
			plt.figure(0)
			[t_us,channelPulses,yTicks]=seqCtl.plotSequence(instructionArray,expCfg.PBchannels)
			for channel in channelPulses:
				plt.plot(t_us, list(channel))
				plt.yticks(yTicks)
				plt.xlabel('时间 (微秒)')
				plt.ylabel('通道')
				# 如果我们正在绘制脉冲长度 <5*t_min 的 Rabi 序列，在序列绘图标题中警告用户
				if expCfg.sequence == 'RabiSeq' and (seqArgList[0]<(5*t_min)):
					plt.title('脉冲序列图（在最后一个扫描点）。关闭以继续实验...\n（注意：对于微波脉冲<5*t_min纳秒，微波通道被指令脉冲5*t_min纳秒，但PB的短脉冲标志同时被脉冲以产生所需的脉冲长度。）', fontsize=7)
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
				# 设置下一次扫描迭代
				if expCfg.sequence == 'ESRseq' or expCfg.sequence == 'PulsedODMRseq':
					if B210_available:
						SRSctl.setSRS_Freq(B210, expCfg.scannedParam[i_scanPoint])
				else:
					seqArgList[0] = expCfg.scannedParam[i_scanPoint]
					instructionArray= PBctl.programPB(expCfg.sequence,seqArgList)
				print('扫描点 ',i_scanPoint+1,' 共 ',expCfg.N_scanPts)
				
				# 添加软件延迟，确保采样点与PB脉冲窗口对齐
				if software_delay > 0:
					print(f"应用软件延迟: {software_delay:.6f} 秒")
					time.sleep(software_delay)
				
				# 读取 DAQ
				if expCfg.sequence == 'ESRseq':
					# ESRseq使用基于时间和样本数的配置
					cts=DAQctl.readDAQ(DAQtask,actualTotalSamples,expCfg.DAQtimeout)
				else:
					# 其他序列使用传统的样本数配置
					cts=DAQctl.readDAQ(DAQtask,2*expCfg.Nsamples,expCfg.DAQtimeout)
			
				# 提取信号和背景计数
				# 每个样本组包含2个样本（1个信号 + 1个背景）
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
			
			# 根据 saveSpacing_inAverages 的间隔和最终扫描后保存参数文件
			if (i_run%expCfg.saveSpacing_inAverages == 0) or (i_run==expCfg.Navg-1):
				paramFile = open(expCfg.paramFileName, 'w')
				expParamList[3] = i_run+1
				# 使用JSON格式保存参数
				import json
				# 将expParamList转换为字典
				param_dict = {}
				for i in range(0, len(expParamList), 2):
					if i+1 < len(expParamList):
						key = expParamList[i].rstrip(':')
						value = expParamList[i+1]
						param_dict[key] = value
				# 写入JSON文件（时间戳已在文件名中）
				json.dump(param_dict, paramFile, indent=2)
				paramFile.close()
				print(f"✅ 参数已保存到: {expCfg.paramFileName}")
		
		# 关闭 B210 输出（如果可用）
		if B210_available:
			SRSctl.disableSRS_RFOutput(B210)

		# 从paramFileName中提取dateTimeStr
		# paramFileName格式: savePath + saveFileName + dateTimeStr + '_PARAMS.txt'
		# 需要提取中间的时间戳部分
		paramFileName = expCfg.paramFileName
		baseName = expCfg.savePath + expCfg.saveFileName
		dateTimeStr = paramFileName.replace(baseName, '').replace('_PARAMS.txt', '')
		
		# 保存差分数据和图片（使用与参数文件相同的时间戳）
		save_differential_data_and_plot(expCfg, sortedScanParam, updatedSignal, updatedBackground, updatedContrast, dateTimeStr)
		
		# 关闭 DAQ 任务：
		DAQctl.closeDAQTask(DAQtask)
		DAQclosed=True
		plt.show()
	except KeyboardInterrupt:
		print('用户键盘中断。正在退出...')
		sys.exit()
	finally:
		if B210_available: 
			# 关闭 B210 输出
			SRSctl.disableSRS_RFOutput(B210)
		if ('DAQtask' in vars()) and DAQtask is not None and (not DAQclosed):
			# 关闭 DAQ 任务：
			DAQctl.closeDAQTask(DAQtask)
			DAQclosed=True
		# 停止脉冲卡输出
		try:
			import spinapi
			# 尝试初始化脉冲卡（如果尚未初始化）
			try:
				spinapi.pb_init()
			except Exception as init_err:
				# 忽略初始化错误，可能已经初始化
				pass
			# 停止脉冲卡输出
			spinapi.pb_stop()
			# 重新初始化并关闭，确保完全停止
			try:
				spinapi.pb_init()
				spinapi.pb_close()
			except Exception as close_err:
				# 忽略关闭错误
				pass
			print("✅ 脉冲卡输出已停止")
		except Exception as e:
			print(f"警告：无法停止脉冲卡输出: {e}")
			# 尝试使用另一种方法停止脉冲卡
			try:
				# 直接调用底层函数停止脉冲
				import ctypes
				# 加载spinapi库
				spinapi_lib = ctypes.CDLL("spinapi.dll")
				# 停止脉冲
				spinapi_lib.pb_stop()
				# 关闭设备
				spinapi_lib.pb_close()
				print("✅ 使用备用方法停止脉冲卡输出")
			except Exception as alt_err:
				print(f"警告：备用方法也无法停止脉冲卡输出: {alt_err}")
	
def run_experiment(config_name):
	"""运行实验"""
	if config_name in ['ESRconfig','Rabiconfig','T1config','T2config','XY8config','correlSpecconfig','PulsedODMRconfig']:
		expConfigFile=config_name
	else:
		print('请指定一个有效的配置文件，例如：ESRconfig, Rabiconfig, T1config, T2config, XY8config, correlSpecconfig, PulsedODMRconfig')
		return False
	runExperiment(expConfigFile)
	return True

if __name__ == "__main__":
	# 检查是否有命令行参数
	if len(sys.argv)>1 and (sys.argv[1] in ['ESRconfig','Rabiconfig','T1config','T2config','XY8config','correlSpecconfig','PulsedODMRconfig']):
		expConfigFile=sys.argv[1]
		runExperiment(expConfigFile)
	else:
		# 显示菜单
		print('====================================')
		print('NV色心实验控制程序')
		print('====================================')
		print('请选择要运行的实验：')
		print('1. ESR实验 (ESRconfig)')
		print('2. Rabi振荡实验 (Rabiconfig)')
		print('3. T1弛豫实验 (T1config)')
		print('4. T2弛豫实验 (T2config)')
		print('5. XY8序列实验 (XY8config)')
		print('6. 相关光谱实验 (correlSpecconfig)')
		print('7. 脉冲ODMR实验 (PulsedODMRconfig)')
		print('====================================')
		
		# 获取用户输入
		while True:
			try:
				choice = int(input('请输入选项编号 (1-7): '))
				if 1 <= choice <= 7:
					break
				else:
					print('请输入有效的选项编号 (1-7)')
			except ValueError:
				print('请输入有效的数字')
		
		# 根据选择设置实验配置文件
		experiments = {
			1: 'ESRconfig',
			2: 'Rabiconfig',
			3: 'T1config',
			4: 'T2config',
			5: 'XY8config',
			6: 'correlSpecconfig',
			7: 'PulsedODMRconfig'
		}
		
		expConfigFile = experiments[choice]
		print(f'您选择了：{experiments[choice]}')
		runExperiment(expConfigFile)