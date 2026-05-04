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
from nidaqmx.constants import *
from connectionConfig import *
import sys

def configureDAQ(Nsamples):
    try:
        # 创建并配置模拟输入电压任务
        NsampsPerDAQread = 2 * Nsamples
        readTask = nidaqmx.Task()

        # 根据设备类型配置终端
        if DAQ_DEVICE_TYPE == 1:
            # USB-7855R 配置 - 使用差分输入
            channel = readTask.ai_channels.add_ai_voltage_chan(
                DAQ_APDInput, "",
                DAQ_TerminalConfig,
                minVoltage, maxVoltage,
                VoltageUnits.VOLTS
            )
        else:
            # 其他设备 (myDAQ, USB-6363) 配置
            channel = readTask.ai_channels.add_ai_voltage_chan(
                DAQ_APDInput, "",
                DAQ_TerminalConfig,
                minVoltage, maxVoltage,
                VoltageUnits.VOLTS
            )

        # 配置采样时钟
        readTask.timing.cfg_samp_clk_timing(
            DAQ_MaxSamplingRate,
            DAQ_SampleClk,
            Edge.RISING,
            AcquisitionType.FINITE,
            NsampsPerDAQread
        )

        # 配置转换时钟
        readTask.timing.ai_conv_src = DAQ_SampleClk
        readTask.timing.ai_conv_active_edge = Edge.RISING

        # 配置开始触发
        readStartTrig = readTask.triggers.start_trigger
        readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)

    except Exception as excpt:
        print('配置 DAQ 时出错。请检查您的 DAQ 是否已连接并通电。异常详情：',
              type(excpt).__name__, '.', excpt)
        if 'readTask' in locals():
            closeDAQTask(readTask)
        sys.exit()
    return readTask


def readDAQ(task, N, timeout):
    try:
        counts = task.read(N, timeout)
    except Exception as excpt:
        print('错误：无法读取 DAQ。请检查您的 DAQ 连接。异常详情：',
              type(excpt).__name__, '.', excpt)
        sys.exit()
    return counts


def closeDAQTask(task):
    task.close()


def configureDAQ_USB7855R(Nsamples):
    """针对 NI USB-7855R 的专用配置函数

    此函数用于 USB-7855R 作为独立采集卡使用的情况，
    不依赖外部脉冲卡触发，而是使用内部时钟或 FPGA 触发。
    """
    try:
        NsampsPerDAQread = 2 * Nsamples
        readTask = nidaqmx.Task()

        # 添加模拟输入通道 - USB-7855R 模拟输入
        channel = readTask.ai_channels.add_ai_voltage_chan(
            DAQ_APDInput, "",
            DAQ_TerminalConfig,
            minVoltage, maxVoltage,
            VoltageUnits.VOLTS
        )

        # 配置内部采样时钟 (USB-7855R 可以使用内部时钟)
        readTask.timing.cfg_samp_clk_timing(
            DAQ_MaxSamplingRate,
            "",  # 使用内部默认时钟
            Edge.RISING,
            AcquisitionType.FINITE,
            NsampsPerDAQread
        )

        # 配置开始触发 - 数字边沿触发
        readStartTrig = readTask.triggers.start_trigger
        readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)

    except Exception as excpt:
        print('配置 USB-7855R 时出错。异常详情：',
              type(excpt).__name__, '.', excpt)
        if 'readTask' in locals():
            closeDAQTask(readTask)
        sys.exit()
    return readTask


def configureDAQ_Continuous(Nsamples):
    """配置连续采集模式（用于实时监测）"""
    try:
        readTask = nidaqmx.Task()

        # 添加模拟输入通道
        channel = readTask.ai_channels.add_ai_voltage_chan(
            DAQ_APDInput, "",
            DAQ_TerminalConfig,
            minVoltage, maxVoltage,
            VoltageUnits.VOLTS
        )

        # 配置连续采集
        readTask.timing.cfg_samp_clk_timing(
            DAQ_MaxSamplingRate,
            DAQ_SampleClk,
            Edge.RISING,
            AcquisitionType.CONTINUOUS,
            Nsamples
        )

        # 配置开始触发
        readStartTrig = readTask.triggers.start_trigger
        readStartTrig.cfg_dig_edge_start_trig(DAQ_StartTrig, Edge.RISING)

    except Exception as excpt:
        print('配置连续采集模式时出错。异常详情：',
              type(excpt).__name__, '.', excpt)
        if 'readTask' in locals():
            closeDAQTask(readTask)
        sys.exit()
    return readTask