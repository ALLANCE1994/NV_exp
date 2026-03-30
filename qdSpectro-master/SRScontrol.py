# SRS 控制
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

#后续要更换为罗德施瓦格信号发生器的控制代码SMA100B，用于控制罗德施瓦格信号发生器的频率、功率、相位等参数。
import numpy as np
import pyvisa as visa
import sys
# 频率单位乘数定义
Hz =1
kHz =1e3
MHz=1e6
GHz=1e9


unicode = lambda s: str(s)

##-------------------- Function definitions--------------------
def initSRS(GPIBaddr,modelName):
	#initSRS: 打开与 SRS 的 GPIB 通信通道。
	# 参数: - GPIBaddr: 描述 SRS 的 GPIB 地址的整数。对于 SG384 型号，出厂默认值为 27。
	#        - modelName: 描述 SRS 型号的字符串。例如 'SG384'
	
	# 检查型号名称是否被识别：
	if modelName not in ('SG382','SG384','SG386','SG392','SG394','SG396'):
		print('错误： SRS 型号名称 ',modelName,' 未被识别。此代码仅在 SRS 型号 SG384 和 SG386 上测试过，但也识别型号 SG382、SG392、SG394、SG396。如果您使用的是不同的 SRS 型号，并且认为它与 SRScontrol.py 中的函数兼容，请编辑 SRScontrol.py 中的 initSRS 函数以包含您的型号。\n')
		sys.exit()
	elif modelName not in ['SG384', 'SG386']:
		print('警告： 此代码仅在 SRS 型号 SG384 和 SG386 上测试过，但可能也支持其他 SG 型号。请参考您的 SRS 手册并检查 SRScontrol.py 中使用的函数是否与您型号的 GPIB 接口兼容。') 
	# 从 GPIB 地址构造仪器标识符：
	SRSaddr = unicode('GPIB0::'+str(GPIBaddr)+'::INSTR')
	# 实例化资源管理器
	rm = visa.ResourceManager()
	# 尝试查询 SRS 标识：
	SRS = rm.open_resource(SRSaddr)
	try:
		deviceID = SRS.query('*IDN?')
	except Exception as excpt:
		print('错误： 无法查询 SRS。请检查 GPIB 地址是否正确且 SRS GPIB 通信已启用。异常详情：', type(excpt).__name__,'.',excpt)
		sys.exit()
	if 'Stanford Research Systems,'+modelName not in deviceID:
		print('错误： 此 GPIB 地址（',GPIBaddr,') 处的仪器不是 SRS '+modelName+'。当发送身份查询 \'*IDN?\' 时，它返回 ',deviceID,'。请检查您的 SRS 信号发生器的 GPIB 地址和/或型号名称。\n') 
		sys.exit() 
	# 清除 ESR（标准事件状态寄存器）、INSR（仪器状态寄存器）和 LERR（最后错误缓冲区）：
	SRS.write('*CLS')
	return SRS

def SRSerrCheck(SRS):
	err = SRS.query('LERR?')
	if int(err) is not 0:
		print('SRS 错误：错误代码', int(err),'. 请参考 SRS 手册了解错误代码的描述。')
		sys.exit()
		

def enableSRS_RFOutput(SRS):
	# 启用 SRS 的射频输出
	SRS.write('ENBR 1')
	SRSerrCheck(SRS)


def disableSRS_RFOutput(SRS):
	# 禁用 SRS 的射频输出
	SRS.write('ENBR 0')
	SRSerrCheck(SRS)
	

def setSRS_RFAmplitude(SRS,RFamplitude, units='dBm'):
	# 设置 SRS 的射频幅度
	SRS.write('AMPR '+str(RFamplitude)+' '+units)
	SRSerrCheck(SRS)
	

def setSRS_Freq(SRS,freq, units='Hz'):
	# setSRSFreq: 设置 SRS 输出的频率。您可以只使用一个参数（第一个参数，freq）调用此函数，
	# 在这种情况下，参数 freq 必须以赫兹为单位。您也可以使用两个参数调用此函数，
	# 第一个参数指定频率，第二个参数指定单位，详情如下。
	# 参数: - freq: 设置 SRS 频率的浮点数。如果未传递 units 参数，则必须以 Hz 为单位。
	#        - units: 描述单位的字符串（例如 'MHz'）。对于 SRS384，最小单位是 'Hz'，最大是 'GHz'
	SRS.write('FREQ '+str(freq)+' '+units)
	SRSerrCheck(SRS)


def setupSRSmodulation(SRS,sequence):
	# 为 T2、XY8 和相关光谱序列启用外部源的 IQ 调制
	# 并为 ESR、Rabi 和 T1 序列禁用调制。
	if sequence in ['ESRseq', 'RabiSeq', 'T1seq']:
		disableModulation(SRS)
	elif sequence in ['T2seq','XY8seq','correlSpecSeq']:
		enableIQmodulation(SRS)
	else:
		print('SRScontrol.py 中的错误：传递给 setupSRSmodulation 的序列名称未被识别。')
		sys.exit()
	

def enableIQmodulation(SRS):
	SRSerrCheck(SRS)
	# 启用调制
	SRS.write('MODL 1')
	SRSerrCheck(SRS)
	# 设置调制类型为 IQ
	SRS.write('TYPE 6')
	SRSerrCheck(SRS)
	# 设置 IQ 调制功能为外部
	SRS.write('QFNC 5')	


def disableModulation(SRS):
	# 禁用调制
	SRS.write('MODL 0')
	SRSerrCheck(SRS)
	

def queryModulationStatus(SRS):
	# 查询调制状态
	status = SRS.query('MODL?')
	SRSerrCheck(SRS)
	if status=='1\r\n':
		print('SRS 调制已开启...')
		IQstatus = SRS.query('TYPE?')
		SRSerrCheck(SRS)
		if IQstatus=='6\r\n':
			print('...并且设置为 IQ')
		else:
			print('...但未设置为 IQ。')
	else:
		print('SRS 调制已关闭。')
	return status