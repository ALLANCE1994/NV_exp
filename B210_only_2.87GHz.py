# B210mini 最终救命版 —— 解决 FX3 state 5
# 输出通道：TX1
import os
os.add_dll_directory(r"C:\Program Files\UHD\bin")
import uhd
import numpy as np
import time

print("==================================")
print(" B210mini 2.87GHz 微波输出")
print("==================================")
usrp = uhd.usrp.MultiUSRP("type=b200,fpga=usrp_b210_fpga.bin")

# 配置参数
freq = 2870000000
gain = 50
rate = 16000000  # 降低采样率以提高稳定性

usrp.set_tx_rate(rate, 0)
usrp.set_tx_gain(gain, 0)

# ======================
# 只改这一行！！！
# ======================
usrp.set_tx_freq(uhd.types.TuneRequest(freq), 0)  # 修复了！

# 发射连续波
buffer_size = 32768  # 优化缓冲区大小，平衡稳定性和响应速度
samps = np.ones(buffer_size, dtype=np.complex64)
stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
streamer = usrp.get_tx_stream(stream_args)
meta = uhd.types.TXMetadata()

print("✅ 正在输出 2.87GHz 微波（TX1 通道）")
print("正在稳定运行...")
print("按 Ctrl + C 停止")

try:
    # 持续发送数据，确保连续输出
    while True:
        # 持续发送数据，不使用突发标记，确保信号连续
        streamer.send(samps, meta)
        # 不添加延迟，确保数据连续发送

except KeyboardInterrupt:
    print("❌ 已停止")