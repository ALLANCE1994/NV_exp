# 检测脉冲卡输出和MyDAQ采样时钟/触发信号
import sys
sys.path.insert(0, '.')

import PBcontrol as PB
import time
import nidaqmx
from nidaqmx.constants import *
from connectionConfig import *

# ===================== 参数 =====================
t_duration = 1000000    # 1ms 脉冲 (1,000,000 ns)
interval = 1000000000   # 每1秒测试一次 (1,000,000,000 ns)

# 配置MyDAQ输出采样时钟和触发信号
def configureMyDAQ():
    try:
        # 创建采样时钟输出任务
        clock_task = nidaqmx.Task()
        # 使用myDAQ1设备名称，与connectionConfig.py一致
        clock_task.co_channels.add_co_pulse_chan_freq("myDAQ1/ctr0", freq=DAQ_MaxSamplingRate, duty_cycle=50000000)
        clock_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS)
        
        # 创建触发信号输出任务
        trigger_task = nidaqmx.Task()
        # 使用myDAQ1设备名称，与connectionConfig.py一致6
        trigger_task.co_channels.add_co_pulse_chan_width("myDAQ1/ctr1", width=100000)  # 100μs 触发脉冲
        trigger_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=1)
        
        return clock_task, trigger_task
    except Exception as e:
        print(f"配置MyDAQ时出错: {e}")
        return None, None

# 检测PulseBlaster输出
def testPulseBlasterOutput():
    print("\n测试PulseBlaster输出...")
    try:
        # 生成ESR序列
        PB.programPB("ESRseq", [t_duration])
        print("✅ PulseBlaster输出测试完成，请到示波器查看各通道波形")
    except Exception as e:
        print(f"❌ PulseBlaster输出测试失败: {e}")

# 检测MyDAQ采样时钟和触发信号
def testMyDAQSignals(clock_task, trigger_task):
    print("\n测试MyDAQ采样时钟和触发信号...")
    try:
        # 启动采样时钟
        clock_task.start()
        print("✅ 采样时钟已启动 (频率: {} Hz)".format(DAQ_MaxSamplingRate))
        
        # 生成触发信号
        trigger_task.start()
        print("✅ 触发信号已发送")
        
        # 等待一段时间让信号稳定
        time.sleep(0.5)
        
        return True
    except Exception as e:
        print(f"❌ MyDAQ信号测试失败: {e}")
        return False

print("开始检测脉冲卡输出和MyDAQ信号...")
print("=====================================")
print("硬件连接说明:")
print("1. MyDAQ PFI0 (采样时钟) → PulseBlaster PB_DAQ通道")
print("2. MyDAQ PFI1 (触发信号) → PulseBlaster PB_STARTtrig通道")
print("3. PulseBlaster各通道 → 示波器")
print("=====================================")

# 配置MyDAQ
clock_task, trigger_task = configureMyDAQ()

if clock_task and trigger_task:
    try:
        while True:
            # 测试MyDAQ信号
            testMyDAQSignals(clock_task, trigger_task)
            
            # 测试PulseBlaster输出
            testPulseBlasterOutput()
            
            # 转换纳秒为秒
            interval_sec = interval / 1e9
            print(f"\n等待 {interval_sec} 秒后再次测试...")
            time.sleep(interval_sec)
            
    except KeyboardInterrupt:
        print("\n已停止测试")
        # 清理任务
        if clock_task:
            clock_task.stop()
            clock_task.close()
        if trigger_task:
            trigger_task.stop()
            trigger_task.close()
else:
    print("❌ 无法配置MyDAQ，测试无法进行")