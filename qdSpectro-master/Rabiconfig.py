# Rabi配置.py
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
拉比实验配置

本脚本可用于配置mainControl.py以运行拉比实验。程序会记录氮空位金刚石样品发射的荧光信号，该信号随微波驱动脉冲的持续时间变化，最终数据将保存为制表符分隔的文本文件（保存选项详见下文）。微波脉冲持续时间从startPulseDuration到endPulseDuration以N_scanPts个步长进行扫描。在每个扫描点，脚本会采集2*Nsamples次荧光读数，依次交替开启和关闭微波，以此确定荧光本底水平。
由此可得到Nsamples组微波开启时的信号计数，以及Nsamples组微波关闭时的本底（参考）计数。首次完成脉冲持续时间扫描后，脚本将重复扫描Navg次，并对所有运行结果中每个扫描点的对比度取平均值（对比度定义及平均选项详见下文）。

——对比度设置——
脚本会根据contrastMode变量指定的两种公式之一，由信号计数与本底计数计算对比度。若contrastMode设为'ratio_SignalOverReference'，对比度定义为信号与本底的比值；若设为'ratio_DifferenceOverSum'，对比度定义为信号与本底的差值同二者之和的比值。用户也可选择'signalOnly'对比度模式，该模式下仅绘制信号计数，忽略本底计数。

——平均选项——
默认情况下，针对每个扫描点，脚本会基于平均后的信号计数（对该扫描点的Nsamples次信号读数取平均）与平均后的本底计数计算对比度。例如，若对比度模式为ratio_SignalOverReference，默认会将Nsamples次信号的平均值除以Nsamples次本底的平均值得到对比度。若希望先逐次计算信号与对应本底的对比度，再对所有样本取平均，可将shotByShotNormalization设为True。
例如，当contrastMode为ratio_SignalOverReference且shotByShotNormalization为True时，对比度将通过每次信号计数与紧随其后的本底计数相除，再对这些比值取平均得到。

脚本首次扫描微波脉冲持续时间时，会按脉冲时长从短到长的顺序进行。若Navg>1，程序将重复扫描Navg次并对结果取平均。默认情况下，除首次扫描外，后续所有扫描的扫描点顺序均会随机打乱。若希望关闭随机化，可将下方的randomize选项设为False。

——绘图选项——
将livePlotUpdate设为True，可在数据采集过程中实时绘制图像。注意，首次扫描完成后，绘图仅在每次后续扫描结束时更新。若livePlotUpdate设为False，则仅在实验全部结束后绘制数据图像。

将plotPulseSequence设为True，可绘制已写入PulseBlaster的脉冲序列。注意，程序会等待用户关闭该绘图窗口后再继续运行。

——保存选项——
用户可选择数据的保存频率。首次扫描时，可设置按saveSpacing_inScanPts个扫描点为间隔保存数据（例如该变量设为2时，脚本会每隔一个扫描点重新保存一次数据）。后续扫描中，程序会在每次扫描结束后，按saveSpacing_inAverages次平均运行轮次为间隔重新保存数据（例如设为3时，每完成3次平均后重新保存）。无论上述选项如何设置，数据总会在首次扫描结束以及实验全部结束（即最后一轮平均完成）时自动保存。

运行本脚本的步骤：
1）编辑connectionConfig.py，定义实验装置中PulseBlaster、斯坦福研究源（SRS）与数据采集卡（DAQ）的通道连接。
2）编辑下方的用户输入参数部分。
3）运行脚本。在Windows命令提示符中，可通过输入python mainControl.py Rabiconfig执行该脚本。

用户输入参数：
*startPulseDuration：扫描的最短脉冲持续时间，单位为纳秒。注意：该值必须为PulseBlaster卡时间分辨率t_min的整数倍（t_min = 1/时钟频率）。
*endPulseDuration：扫描的最长脉冲持续时间，单位为纳秒。注意：该值必须为PulseBlaster卡时间分辨率t_min的整数倍（t_min = 1/时钟频率）。
*N_scanPts：扫描点数量。
*microwavePower：SRS信号源输出功率，单位为分贝毫瓦（dBm）。注意：该值不得超过与SRS输出端相连的任意放大器的输入功率上限。
*microwaveFrequency：SRS信号源输出的微波频率，单位为赫兹（Hz）。
*t_AOM：声光调制器（AOM）脉冲持续时间，单位为纳秒（ns）。
*t_readoutDelay：AOM脉冲起始至DAQ采集脉冲的延迟时间，单位为纳秒（ns）。最佳延迟可通过optimReadoutDelay.py脚本确定（详见实验方案论文第54步）。
*Nsamples：每个扫描点采集的荧光测量样本数。
*Navg：平均运行轮次（即脉冲长度扫描的重复次数）。
*DAQtimeout：数据采集卡等待指定数量样本就绪（即完成采集）的最长时间，单位为秒。
*contrastMode：根据所需对比度模式，设为'ratio_SignalOverReference'、'ratio_DifferenceOverSum'或'signalOnly'之一（详见上文“对比度设置”说明）。
*livePlotUpdate：设为True可在数据采集时实时更新绘图（详见上文“绘图选项”）。
*plotPulseSequence：设为True可在实验开始时绘制脉冲序列（详见上文“绘图选项”）。
*plotXaxisUnits：设置数据图横轴单位，可选纳秒（ns）、微秒（us）或毫秒（ms）。
*xAxisLabel：设置数据图横轴标签。
*saveSpacing_inScanPts：首次扫描期间，以扫描点数为间隔的数据保存周期。
*saveSpacing_inAverages：首次完整扫描后，以平均运行轮次为间隔的数据保存周期。
*savePath：数据保存文件夹路径。默认情况下，数据保存在本脚本所在目录下名为Saved_Data的文件夹中。
*saveFileName：数据保存文件名。该名称后会自动附加脚本运行的日期和时间。
*shotByShotNormalization：设为True可启用逐次对比度归一化（详见上文“平均选项”）。
*randomize：设为True可对首次扫描之后的所有扫描打乱扫描点顺序。
"""
#导入模块
from spinapi import ns,us,ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
# 定义 t_min，即PulseBlaster的时间分辨率，其计算公式为1/(时钟频率)：
t_min = 1e3/PBclk #in ns
#-------------------------  USER 输入  ---------------------------------------#

# 微波 扫描 参数s:----------------------------------------------------
# 启动 pulse 持续时间 (单位为纳秒):
startPulseDuration = 0
# End pulse 持续时间 (单位为纳秒):
endPulseDuration = 600
# 数量 pulse length steps:
N_scanPts =101
# 来自SRS的微波功率输出（dBm）- 请勿超过放大器的最大输入功率:
microwavePower = -5
# 微波 频率 (Hz):
microwaveFrequency = 2.87e9 
# Pulse 序列 参数s:----------------------------------------------------
# AOM pulse 持续时间 (ns)
t_AOM = 5*us
# 读取out 延迟 (ns)
t_readoutDelay = 2.3*us
# 各脉冲长度点需采集的荧光测量样本数量：
Nsamples = 1000
# 平均运行轮次：
Navg = 1
#DAQ 超时, 单位为秒:
DAQtimeout = 10
# 绘图 options--------------------------------------------------------------
# 对比度 mode
contrastMode ='ratio_SignalOverReference'
# Live 绘图 update option
livePlotUpdate = True
# 绘制 脉冲序列 option  - set to true to 绘图 the 脉冲序列
plotPulseSequence = False
# 绘制X轴单位乘数（纳秒、微秒或毫秒）
plotXaxisUnits = ns
# 绘制X轴标签
xAxisLabel = 'Microwave pulse length (ns)'
# 保存 options------------------------------------------------------------------
# 首次扫描期间，以扫描点数为间隔的数据保存周期：
saveSpacing_inScanPts = 2
# 首次完整扫描后，以平均运行轮次为间隔的数据保存周期：
saveSpacing_inAverages = 3
# 数据保存文件夹路径：
savePath = os.getcwd()+"\\Saved_Data\\"
# 数据保存文件名：
saveFileName = "Rabi_"
# 平均化选项：------------------------------------------------------------
# 逐帧对比度归一化选项：
shotByShotNormalization = False
# 随机打乱扫描点顺序选项：
randomize = True
#------------------------- END OF USER 输入 ----------------------------------#

scannedParam = np.linspace(startPulseDuration,endPulseDuration, N_scanPts, endpoint=True) 
#序列字符串:
sequence = 'RabiSeq'
#扫描 start Name
scanStartName = 'startPulseDuration'
#扫描 end Name
scanEndName = 'endPulseDuration'
#PB 通道s
PBchannels = {'AOM':AOM,'uW':uW,'DAQ':DAQ,'STARTtrig':STARTtrig}
#序列参数：
sequenceArgs = [t_AOM,t_readoutDelay]
#Make 保存文件路径：
dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
dataFileName = savePath + saveFileName+ dateTimeStr +".txt"
#Make param file path
paramFileName = savePath + saveFileName+dateTimeStr+'_PARAMS'+".txt"
# 参数文件保存设置：
formattingSaveString = "%s\t%d\n%s\t%d\n%s\t%d\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%f\n%s\t%r\n%s\t%r\n%s\t%r\n%s\t%d\n%s\t%d\n%s\t%s\n"
expParamList = ['N_timePts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startPulseDuration:',scannedParam[0],'endPulseDuration:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]

def updateSequenceArgs():
	sequenceArgs = [t_AOM,t_readoutDelay]
	return sequenceArgs
	
def updateExpParamList():
	expParamList = ['N_timePts:',N_scanPts,'Navg:',Navg,'Nsamples:',Nsamples,'startPulseDuration:',scannedParam[0],'endPulseDuration:',scannedParam[-1],'microwavePower:',microwavePower,'microwaveFrequency',microwaveFrequency,'t_AOM:',t_AOM, 't_readoutDelay:',t_readoutDelay,'shotByShotNormalization:',shotByShotNormalization,'randomize:',randomize,'plotPulseSequence:',plotPulseSequence,'saveSpacing_inScanPts:',saveSpacing_inScanPts,'saveSpacing_inAverages:',saveSpacing_inAverages,'dataFileName:',dataFileName]
	return expParamList