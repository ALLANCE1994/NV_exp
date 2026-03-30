# optimizeReadout延迟.py
# 版权所有 2018 Diana Prado Lopes Aude Craik

# 特此免费授予任何获得本软件及相关文档文件（"软件"）副本的人
# 许可，允许其不受限制地处理本软件，包括但不限于使用、复制、
# 修改、合并、发布、分发、再许可和/或销售软件副本的权利，
# 并允许向其提供软件的人这样做，但须符合以下条件：

# 上述版权声明 and this permission notice shall be
# included in all copies or substantial portions of the Software.

# 本软件按"原样"提供 "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
# 读取延迟优化脚本
本脚本用于查找声光调制器（AOM）脉冲起始与数据采集卡（DAQ）脉冲起始之间的最佳延迟（详见实验流程第54步）。脚本会绘制NV金刚石样品发射的荧光强度随扫描延迟变化的曲线，并将数据保存为制表符分隔的文本文件（保存选项详见下文）。

## 脚本运行步骤
1. 编辑`connectionConfig.py`文件，定义实验装置中脉冲发生器（PulseBlaster）与数据采集卡的通道连接配置。
2. 编辑下方的用户输入参数区域。
3. 运行脚本。在Windows命令提示符中，可通过执行`python optimizeReadoutDelay.py`命令运行该脚本。

## 用户输入参数说明
--> 注：`t_min`为脉冲发生器（PulseBlaster）板卡的时间分辨率（即`t_min = 1/时钟频率`）。例如，500MHz的板卡，`t_min = 2纳秒`。
* `startDelay`：扫描的最短延迟，单位为纳秒（必须≥5*t_min）。
* `endDelay`：扫描的最长延迟，单位为纳秒。
* `N_scanPts`：扫描数据点数量。
* `t_AOM`：声光调制器（AOM）脉冲持续时长，单位为纳秒。
* `Nsamples`：每个延迟点需采集的荧光测量样本数。
* `DAQtimeout`：数据采集卡等待获取指定数量样本（即完成采集）的最长等待时间，单位为秒。
* `plotPulseSequence`：若设为`True`，脚本将生成脉冲发生器输出的脉冲序列图像。
* `savePath`：数据保存文件夹路径。默认情况下，数据将保存在本脚本所在目录下名为`Saved_Data`的文件夹中。
* `saveFileName`：数据保存文件名。脚本运行时的日期和时间会自动追加至该文件名后。

"""
#导入模块
from spinapi import ns,us,ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
import SRScontrol as SRSctl
import DAQcontrol as DAQctl
import PBcontrol as PBctl
import sequenceControl as seqCtl
import random
import matplotlib.pyplot as plt
import numpy as np
import sys

# 定义 t_min, 时间分辨率 of the PulseBlaster, given by 1/(时钟频率):
t_min = 1e3/PBclk #in ns
#-------------------------  USER 输入  ---------------------------------------#

# 扫描 参数s:----------------------------------------------------
# 启动 pulse 持续时间 (单位为纳秒), must be >=5*t_min:
startDelay = 5*t_min
# End pulse 持续时间 (单位为纳秒):
endDelay = 10000
# 数量 延迟 steps:
N_scanPts = 100
# Pulse 序列 参数s:----------------------------------------------------
# AOM pulse 持续时间 (单位为ns)
t_AOM= 5*us
# 数量 fluorescence measurement 样本 to take at each 延迟 点:
Nsamples = 1000
#DAQ 超时, 单位为秒:
DAQtimeout = 10
# 绘图 options--------------------------------------------------------------
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = True
# 保存 options------------------------------------------------------------------
# Path to folder where 数据 will be 保存d:
savePath = os.getcwd()+"\\Saved_Data\\"
# File name for 数据 file
saveFileName = "optimizeReadoutDelay_"
#------------------------- END OF USER 输入 ----------------------------------#
try:
	t_readoutDelay = np.linspace(startDelay,endDelay, N_scanPts, endpoint=True) 
	#PB 通道s
	PBchannels = {'AOM':AOM,'DAQ':DAQ,'STARTtrig':STARTtrig}
	#Make 保存 file path
	dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
	dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
	#Make param file path
	paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
	#Param file 保存 settings
	formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%s\n"
	expParamList = ['N_scanPts:',N_scanPts,'Nsamples:',Nsamples,'startDelay:',startDelay,'endDelay:',endDelay,'t_AOM:',t_AOM,'plotPulseSequence:',plotPulseSequence,'dataFileName:',dataFileName]


	#Validate user 输入:
	if startDelay<(5*t_min):
		print('错误： startDelay is too sh或t. 请 set startDelay>',5*t_min,'ns.')
		sys.exit()
	if startDelay%(t_min):
		startDelay = t_min*round(startDelay/t_min)
		print('警告： startDelay is 不 a 的倍数',t_min,'ns. Rounding...\nstartDelay now set to:',startDelay,'ns.')
		t_readoutDelay = np.linspace(startDelay,endDelay, N_scanPts, endpoint=True) 
	stepSize = t_readoutDelay[1]-t_readoutDelay[0]
	if (stepSize%t_min):
				roundedStepSize = t_min*round(stepSize/t_min)
				endDelay  = (N_scanPts-1)*roundedStepSize + startDelay 
				print('警告： requested time step is ',stepSize,'ns, which is 不 an 整数 的倍数 ',t_min,'ns. Rounding step size to the nearest 的倍数 ',t_min,':\nStep size is now',roundedStepSize,'.\nstartDelay=',startDelay,' 和 \nendDelay=',endDelay)
				t_readoutDelay = np.linspace(startDelay,endDelay, N_scanPts, endpoint=True)

	#配置 DAQ
	DAQclosed = False
	DAQtask = DAQctl.configureDAQ(Nsamples)

	fluorescence = np.zeros(N_scanPts)
	if plotPulseSequence:
		instructionArray= PBctl.programPB('optimReadoutSeq', [t_readoutDelay[-1],t_AOM])
		[t_us,channelPulses,yTicks]=seqCtl.plotSequence(instructionArray,PBchannels)
		plt.figure(0)
		for channel in channelPulses:
			plt.plot(t_us, list(channel))
		plt.yticks(yTicks)
		plt.xlabel('time (us)')
		plt.ylabel('channel')
		plt.title('Pulse Sequence plot (at last scan point)')

	#运行 readout 延迟 扫描:
	for i in range (0, N_scanPts):
		#编程 PB
		instructionArray= PBctl.programPB('optimReadoutSeq', [t_readoutDelay[i],t_AOM])
		print('Scan point ', i+1, ' of ', N_scanPts)
		#read DAQ
		sig=DAQctl.readDAQ(DAQtask,2*Nsamples,DAQtimeout)
		#Take 平均 of counts
		fluorescence[i] = np.mean(sig)

	#Close DAQ 任务:
	DAQctl.closeDAQTask(DAQtask)
	DAQclosed = True

	#保存 数据:
	#Check if 保存 directory exists, and, if not, creates a "保存d 数据" folder in the 电流 directory, where all 数据 will be 保存d.
	if not (os.path.isdir(savePath)):
		os.makedirs(savePath)
		print('警告： Save direct或y did 不 exist, creating folder named Saved_Data in the w或king direct或y. Data will be saved to this direct或y.')

	data = np.array([t_readoutDelay,fluorescence])
	data = data.T
	dataFile = open(dataFileName, 'w')
	for item in data:
		dataFile.write("%.0f\t%f\n" % tuple(item))
	paramFile = open(paramFileName, 'w')
	paramFile.write(formattingSaveString % tuple(expParamList))
	dataFile.close()
	paramFile.close()

	#绘图 results
	plt.figure(1)
	plt.plot(t_readoutDelay, fluorescence)
	plt.xlabel('Delay (ns)')
	plt.ylabel('APD Voltage (V)')
	plt.show()
except KeyboardInterrupt:
		print('User keyboard interrupt. Quitting...')
		sys.exit()
finally:
		if 'SRS' in vars():	
			#Turn off SRS 输出
			SRSctl.disableSRS_RFOutput(SRS)
		if ('DAQtask' in vars()) and  (not DAQclosed):
			#Close DAQ 任务:
			DAQctl.closeDAQTask(DAQtask)
			DAQclosed=True