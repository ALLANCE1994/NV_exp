# README  qdSpectro v1.0.1
Copyright 2018 Diana Prado Lopes Aude Craik (MIT许可证)

本软件包旨在与题为"Quantum diamond spectrometer for nanoscale NMR and ESR spectroscopy"的论文中描述的协议一起使用（目前正在Nature Protocols 2019年发表审核中）。该论文介绍了基于金刚石中氮空位（NV）色心的光谱仪构建协议，并描述了此软件包和相关硬件的安装和运行过程。本README文件提供了qdSpectro的系统要求和安装/运行指南的摘要，但用户还应阅读论文中的完整协议说明（以下简称协议论文）。

本文件结构如下：
1. 系统要求
    * 与qdSpectro直接通信的非标准外围硬件列表（如协议论文中所述，完成NV金刚石光谱仪组装还需要其他未在此列出的设备）
    * qdSpectro的软件依赖项列表，也必须安装
2. 安装指南
3. 使用说明
    * 使用qdSpectro运行实验
    * 使用togglePBchan.py
4. 当前版本补丁和更新

## 1. 系统要求：

### 非标准硬件
* National Instruments数据采集卡（DAQ），采样率至少为250 kSa/s（例如，National Instruments NI USB-6229或NI USB-6211）。qdSpectro已使用NI USB-6229和NI USB-6211进行测试。该代码设计为与National Instruments DAQ配合使用，如果使用其他数据采集系统，需要用户进行修改。
* 500MHz PulseBlaster卡（Spincore PulseBlasterESR PRO 500 MHz）。qdSpectro仅使用Spincore PulseBlasterESR PRO 500MHz卡进行了测试，但应与其他SpinCore PulseBlaster卡兼容。可以使用其他信号发生器，但需要用户修改qdSpectro代码。
* SRS SG384信号发生器。qdSpectro设计为与SRS SG384信号发生器配合使用，仅使用此型号和SG 386型号进行了测试。它应该与其他SRS SG3800或SG3900型号兼容，但尚未使用这些型号进行测试。可以使用其他脉冲发生器，但需要用户修改qdSpectro代码。
* National Instruments USB/GPIB转换器（qdSpectro使用National Instruments GPIB-USB-HS进行测试）。用于将SRS信号发生器连接到PC。

### 软件依赖项
操作系统：
* 此处和协议论文中描述的软件安装说明适用于Windows PC（qdSpectro已在Windows 10上测试）。虽然该软件包应该可以移植到Linux或Mac操作系统，但尚未在这些平台上测试，可能需要用户进行一些修改。

软件包：
* Python 3版本3.6.3或更高版本（使用版本3.6.3测试），并且位数与计算机的位数匹配（即，如果在64位计算机上运行，则安装64位Python）。 https://www.python.org/
* Notepad++或任何其他您选择的文本编辑器，用于查看和编辑Python脚本。 https://notepad-plus-plus.org/

驱动程序：
* National Instruments NI-DAQmx驱动程序（使用NI DAQ卡NI USB-6229的17.1.1版本测试）- 用户应下载与所选DAQ卡兼容的NI-DAQmx驱动程序。 https://www.ni.com/dataacquisition/nidaqmx.htm
* SpinAPI：PulseBlaster卡的SpinCore API和驱动程序套件（使用20171214版本测试）。 http://www.spincore.com/support/spinapi/SpinAPI_Main.shtml
* 用于USB/GPIB转换器的National Instrument驱动程序（列在上面的硬件要求下），用于PC和SRS信号发生器之间的GPIB通信。qdSpectro已使用National Instruments GPIB-USB-HS转换器进行测试，该转换器需要安装NI-VISA和NI-488.2驱动程序（qdSpectro已使用两者的16.0版本进行测试，尽管较新版本也应该可以工作）。

外围仪器控制库：
* SpinAPI Python3包装器 - SpinCore的Python包装器，用于SpinAPI中的C函数，可用于与PulseBlaster卡通信和控制。qdSpectro已使用Spincore在以下链接上提供的spinapi.py版本进行测试（截至2018年2月8日）。
http://www.spincore.com/support/SpinAPI_Python_Wrapper/Python_Wrapper_Main.shtml
如果上述链接不再有效，仍可以从此处检索所需版本的spinapi.py：https://web.archive.org/web/20190208140542/http://www.spincore.com/support/SpinAPI_Python_Wrapper/spinapi.py
* NI-VISA库（使用16.0版本测试）- 此库应随NI GPIB/USB转换器的驱动程序一起安装，但如果没有，可以从National Instruments网站下载：http://www.ni.com/download/ni-visa-16.0/6184/en/（16.0版本的链接）。必须安装此库才能使qdSpectro通过GPIB与SRS信号发生器通信。 ***重要：此库的位数必须与Python位数匹配。***
* PyVISA 1.8或更高版本（使用1.8版本测试）- NI-VISA库的Python包装器，允许从Python脚本调用该库 https://pypi.python.org/pypi/PyVISA

用于数据处理和图形显示的Python库：
* Matplotlib（使用2.1.2版本测试）- 用于绘图的Python库 https://matplotlib.org/index.html
* NumPy（使用1.14.0版本测试）- 用于科学计算的Python库 http://www.numpy.org/

## 2. 安装指南
注意：完成完整安装过程的时间通常为1-3小时，主要是由于外围驱动程序依赖项和所需的硬件设置。
* 从https://www.python.org/下载并安装Python 3版本3.6.3或更高版本。Python位数必须与NI-VISA库的位数和计算机的位数匹配。qdSpectro随附的协议论文描述了如何从Windows命令提示符运行Python脚本以及如何使用文本编辑器Notepad++编辑脚本。用户可以选择从集成开发环境（IDE）运行和编辑脚本，或使用不同的编辑器。
要检查Python安装是否成功，请在Windows命令提示符中键入python并按Enter键运行Python。这应该返回Python版本号和位数。要退出Python，请键入exit()（或按住Ctrl键并按Z键），然后按Enter键。
* 从https://notepad-plus-plus.org/下载并安装Notepad++。
* 选择一个安装qdSpectro的文件夹。此后将此文件夹称为工作目录。从https://gitlab.com/dplaudecraik/qdSpectro下载qdSpectro并将其保存在工作目录中。建议用户下载最新版本并查看软件包的README文件，了解有关安装说明的任何版本特定更改。
* 从http://www.spincore.com/support/SpinAPI_Python_Wrapper/Python_Wrapper_Main.shtml下载SpinAPI Python3包装器
（如果此链接不再有效，仍可以从此处检索所需版本的spinapi.py：https://web.archive.org/web/20190208140542/http://www.spincore.com/support/SpinAPI_Python_Wrapper/spinapi.py）
***重要：将文件保存为工作目录中的spinapi.py。***
* 下载并安装NI USB/GPIB转换器所需的驱动程序（对于用于测试qdSpectro的NI GPIB-USB-HS转换器，驱动程序是NI-VISA和NI-488.2）。如果这些驱动程序不包含NI-VISA库，请从National Instruments网站下载并安装该库：例如http://www.ni.com/download/ni-visa-16.0/6184/en/（16.0版本的链接）。
***重要：确保NI-VISA库的位数与Python位数匹配（即，如果在64位计算机上运行，则安装64位NI-VISA）。***
* 在Windows命令提示符中，通过运行```python -m pip install -U pyvisa```安装pyVISA
* 通过启动Python（在命令提示符中键入python并按Enter键）并运行```import visa```来检查库是否成功安装。如果没有出现错误，则安装成功。
* 在Windows命令提示符中，通过运行```python -m pip install -U matplotlib```安装matplotlib。通过启动Python并运行```import matplotlib```来检查库是否成功安装。如果没有出现错误，则安装成功。
* 在Windows命令提示符中，通过运行```python -m pip install -U numpy```安装numpy。通过启动Python并运行```import numpy```来检查库是否成功安装。如果没有出现错误，则安装成功。
* 按照PulseBlaster手册的“安装”部分中的说明进行操作（例如，2017年9月4日版本的PulseBlasterESR-PRO手册的第9页）。这包括下载SpinAPI软件包，将PulseBlaster卡插入计算机中可用的外围组件互连（PCI）插槽，并使用SpinCore提供的测试程序之一测试PulseBlaster。
* 按照National Instruments DAQ的安装说明进行操作（例如，2009年4月版本的NI USB-621x手册的第1章）。这包括下载NI-DAQmx驱动程序并通过USB将DAQ卡连接到计算机。
* 使用GPIB/USB转换器将SRS信号发生器的GPIB端口连接到PC上的USB端口。按照SRS手册中的GPIB设置说明在SRS信号发生器上启用GPIB接口并选择其GPIB地址（例如，对于SG 380系列中的型号，请参见SG380系列手册修订版2.04的第46页）。打开qdSpectro的connectionConfig.py，并在此脚本的“SRS connections”部分下，编辑变量GPIBaddr和modelName，使其成为SRS信号发生器的GPIB地址和型号名称（例如，GPIBaddr=27，modelName=‘SG384’）。
* 按照协议论文中的说明完成硬件设置，包括从DAQ、PulseBlaster和SRS信号发生器到金刚石光谱仪设备的必要连接，并按照论文中的指示编辑connectionConfig.py以相应配置qdSpectro。

## 3. 使用说明：

### 使用qdSpectro运行实验：
下载qdSpectro软件包后，工作目录应包含以下文件。
用户输入配置文件：
* connectionConfig.py – PulseBlaster、DAQ和SRS与PC连接的配置文件。在运行任何软件包脚本之前，用户应按照协议中的指示编辑此文件。
* __config.py – 实验配置文件。每个实验都有自己的配置文件（例如，ESR实验的配置文件是ESRconfig.py），主要由“用户输入”部分组成，用户可以在其中编辑实验参数并配置与数据处理、绘图和保存方式相关的选项。

主控制和辅助库：
* mainControl.py – 本协议中描述的所有实验都从mainControl.py脚本运行，该脚本将实验特定的配置文件作为参数。根据配置文件中定义的输入参数，mainControl.py运行实验、生成图表并保存结果。
* DAQcontrol.py – 包含配置DAQ的函数
* SRScontrol.py – 包含控制SRS信号发生器的函数
* PBcontrol.py – 包含配置和编程PulseBlaster卡的函数
* sequenceControl.py – 包含创建运行本协议中实验所需的脉冲序列的函数

在使用qdSpectro运行任何实验之前，用户应阅读随下载的软件包版本提供的README文件，其中将描述任何升级和补丁，并按照协议论文中的指示编辑connectionConfig.py。

使用qdSpectro运行实验：
1. 在notepad++中打开相关的___config.py文件。阅读此脚本中定义的实验参数和数据处理选项的描述。
2. 根据需要编辑此脚本的“用户输入”部分中的实验参数并配置数据处理选项。
3. 要运行实验，请打开Windows命令提示符，从工作目录运行：
```python mainControl.py __config```
4. 要在实验完成前退出，请按Ctrl+C。

关于单位的说明：用户输入参数的单位（在上面的步骤ii中输入）在___config.py文件的用户输入部分的注释中指定。为了更加清晰，我们还在此处注意到，qdSpectro软件包1.0版本（撰写本文时的当前版本）中时间变量的默认单位是纳秒。用户可以以纳秒为单位输入时间变量，或使用以下单位乘数之一：ns = 1，us = 1e3，ms = 1e6。例如，如果将变量endTau设置为10微秒，用户可以在相关___config.py文件的用户输入部分中输入endTau = 10000或endTau = 10*us。本文中的说明始终使用后一种格式。为了完整性，我们还注意到，在qdSpectro 1.0版本中，微波频率以赫兹为单位输入（例如，如果将变量startFreq设置为2.7GHz，用户应输入startFreq=2.7e9），微波功率以dBm为单位输入（例如，如果将变量microwavePower设置为0 dBm，用户应输入microwavePower=0）。运行不同版本qdSpectro的用户应参考该版本的README文件，了解任何版本特定的用户输入说明。

### 使用togglePBchan.py：
在协议论文中描述的NV金刚石光谱仪设备设置的几个点上，必须打开和关闭PulseBlaster（PB）通道。使用qdSpectro软件包中的togglePBchan.py脚本来切换任何PulseBlaster通道。在Windows命令提示符中，从工作目录启动Python并运行togglePBchan.py。将显示一个键，将字母与PulseBlaster通道相关联，如下所示：
* A = 连接到驱动AOM的RF源上的开关的PB通道
* M = 连接到SRS信号发生器的MW输出上的开关的PB通道
* I = 连接到SRS信号发生器的I输入上的开关的PB通道
* Q = 连接到SRS信号发生器的Q输入上的开关的PB通道
* D = 连接到DAQ的采样时钟输入的PB通道
* S = 连接到DAQ的启动触发输入的PB通道
要打开给定的PB通道，请键入相应的字母并按Enter键。要关闭通道，请再次键入相同的键。通过在示波器上测量PB输出电压来检查功能。

## 4. 当前版本补丁和更新
v1.0.1：T1config.py用户输入部分的文档小修复。