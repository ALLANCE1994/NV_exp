"""
NV色心参数优化脚本
本脚本用于优化Rabi实验中的关键参数：
1. t_AOM - 极化时间（确保完全极化）
2. t_readoutDelay - 读出延迟（最大化荧光对比度）
3. t_wait - 等待时间（确保ISC弛豫完成）
4. Nsamples - 采样数（信噪比平衡）

优化策略：依次优化每个参数，保持其他参数为当前最佳值
"""

from spinapi import ns, us, ms
import os
import numpy as np
from time import localtime, strftime
from connectionConfig import *
import SRScontrol as SRSctl
import DAQcontrol_MyDAQ as DAQctl
import PBcontrol as PBctl
import sequenceControl as seqCtl
import matplotlib.pyplot as plt
import sys
import time

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

t_min = 1e3/PBclk

# ==================== 用户优化参数设置 ====================

# 1. t_AOM 优化设置
t_AOM_start = 10*us
t_AOM_end = 500*us
t_AOM_pts = 15

# 2. t_readoutDelay 优化设置
t_readoutDelay_start = 50*ns
t_readoutDelay_end = 1000*ns
t_readoutDelay_pts = 20

# 3. t_wait 优化设置
t_wait_start = 1*us
t_wait_end = 10*us
t_wait_pts = 10

# 4. Nsamples 优化设置
Nsamples_options = [100, 500, 1000, 2000, 5000]

# 固定参数
microwaveFrequency = 2.8660e9
B210_gain = 65
endPulseDuration = 500
DAQtimeout = 10

# 保存路径
savePath = os.getcwd() + "\\Saved_Data\\"
saveFileName = "parameter_optimization_"

# ==================== 主程序 ====================

def save_optimization_data(x_data, y_data, x_label, y_label, filename_prefix):
    if not os.path.isdir(savePath):
        os.makedirs(savePath)
    dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
    dataFileName = savePath + filename_prefix + dateTimeStr + ".txt"

    data = np.array([x_data, y_data]).T
    dataFile = open(dataFileName, 'w')
    dataFile.write("# {}\t{}\n".format(x_label, y_label))
    for item in data:
        dataFile.write("{:.2f}\t{:.6f}\n".format(item[0], item[1]))
    dataFile.close()
    return dataFileName


def read_fluorescence(Nsamples=200):
    """读取荧光信号，每次读取都创建和关闭DAQ任务"""
    DAQtask = None
    try:
        DAQtask = DAQctl.configureDAQ(Nsamples)
        sig = DAQctl.readDAQ(DAQtask, 2*Nsamples, DAQtimeout)
        return np.mean(sig), np.std(sig)
    except Exception as e:
        print("    读取错误: {}".format(e))
        return 0.0, 0.0
    finally:
        if DAQtask is not None:
            try:
                DAQctl.closeDAQTask(DAQtask)
            except:
                pass


def optimize_t_AOM():
    print("\n" + "="*60)
    print("步骤1: 优化 t_AOM (极化时间)")
    print("="*60)

    t_readoutDelay_fixed = 300*ns
    t_wait_fixed = 3*us

    t_AOM_range = np.linspace(t_AOM_start, t_AOM_end, t_AOM_pts)

    signal_list = []
    noise_list = []

    print("扫描范围: {:.1f} us - {:.1f} us".format(t_AOM_start/1e3, t_AOM_end/1e3))

    for i, t_AOM in enumerate(t_AOM_range):
        instructionArray = PBctl.programPB('RabiSeq',
            [endPulseDuration, t_AOM, t_readoutDelay_fixed, t_wait_fixed])

        mean_signal, std_signal = read_fluorescence(200)

        signal_list.append(mean_signal)
        noise_list.append(std_signal)

        print("  [{}/{}] t_AOM = {:.1f} us, signal = {:.4f}, noise = {:.6f}".format(
            i+1, t_AOM_pts, t_AOM/1e3, mean_signal, std_signal))

    snr = np.array(signal_list) / (np.array(noise_list) + 1e-10)
    best_idx = np.argmax(snr)
    best_t_AOM = t_AOM_range[best_idx]

    print("\n最优 t_AOM = {:.1f} us (SNR = {:.2f})".format(best_t_AOM/1e3, snr[best_idx]))

    save_optimization_data(t_AOM_range/1e3, signal_list, "t_AOM (us)", "Signal", "t_AOM_opt_")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    ax1.plot(t_AOM_range/1e3, signal_list, 'b-o')
    ax1.set_xlabel('t_AOM (us)')
    ax1.set_ylabel('Fluorescence Signal (V)')
    ax1.set_title('t_AOM Optimization - Signal')
    ax1.grid(True)

    ax2.plot(t_AOM_range/1e3, snr, 'r-o')
    ax2.set_xlabel('t_AOM (us)')
    ax2.set_ylabel('SNR')
    ax2.set_title('t_AOM Optimization - SNR')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(savePath + "t_AOM_optimization.png", dpi=150)
    plt.show()

    return best_t_AOM


def optimize_t_readoutDelay(t_AOM_best, t_wait_fixed):
    print("\n" + "="*60)
    print("步骤2: 优化 t_readoutDelay (读出延迟)")
    print("="*60)

    t_readoutDelay_range = np.linspace(t_readoutDelay_start, t_readoutDelay_end, t_readoutDelay_pts)

    signal_list = []

    print("扫描范围: {:.0f} ns - {:.0f} ns".format(t_readoutDelay_start, t_readoutDelay_end))

    for i, t_readoutDelay in enumerate(t_readoutDelay_range):
        instructionArray = PBctl.programPB('RabiSeq',
            [endPulseDuration, t_AOM_best, t_readoutDelay, t_wait_fixed])

        mean_signal, _ = read_fluorescence(200)

        signal_list.append(mean_signal)

        print("  [{}/{}] t_readoutDelay = {:.0f} ns, signal = {:.4f}".format(
            i+1, t_readoutDelay_pts, t_readoutDelay, mean_signal))

    best_idx = np.argmax(signal_list)
    best_t_readoutDelay = t_readoutDelay_range[best_idx]

    print("\n最优 t_readoutDelay = {:.0f} ns".format(best_t_readoutDelay))

    save_optimization_data(t_readoutDelay_range, signal_list, "t_readoutDelay (ns)", "Signal", "t_readoutDelay_opt_")

    plt.figure(figsize=(10, 6))
    plt.plot(t_readoutDelay_range, signal_list, 'g-o')
    plt.xlabel('t_readoutDelay (ns)')
    plt.ylabel('Fluorescence Signal (V)')
    plt.title('t_readoutDelay Optimization')
    plt.grid(True)
    plt.savefig(savePath + "t_readoutDelay_optimization.png", dpi=150)
    plt.show()

    return best_t_readoutDelay


def optimize_t_wait(t_AOM_best, t_readoutDelay_best):
    print("\n" + "="*60)
    print("步骤3: 优化 t_wait (等待稳定时间)")
    print("="*60)

    t_wait_range = np.linspace(t_wait_start, t_wait_end, t_wait_pts)

    signal_list = []

    print("扫描范围: {:.1f} us - {:.1f} us".format(t_wait_start/1e3, t_wait_end/1e3))

    for i, t_wait in enumerate(t_wait_range):
        instructionArray = PBctl.programPB('RabiSeq',
            [endPulseDuration, t_AOM_best, t_readoutDelay_best, t_wait])

        mean_signal, _ = read_fluorescence(200)

        signal_list.append(mean_signal)

        print("  [{}/{}] t_wait = {:.1f} us, signal = {:.4f}".format(
            i+1, t_wait_pts, t_wait/1e3, mean_signal))

    best_idx = np.argmax(signal_list)
    best_t_wait = t_wait_range[best_idx]

    print("\n最优 t_wait = {:.1f} us".format(best_t_wait/1e3))

    save_optimization_data(t_wait_range/1e3, signal_list, "t_wait (us)", "Signal", "t_wait_opt_")

    plt.figure(figsize=(10, 6))
    plt.plot(t_wait_range/1e3, signal_list, 'm-o')
    plt.xlabel('t_wait (us)')
    plt.ylabel('Fluorescence Signal (V)')
    plt.title('t_wait Optimization - ISC Relaxation Time')
    plt.grid(True)
    plt.savefig(savePath + "t_wait_optimization.png", dpi=150)
    plt.show()

    return best_t_wait


def optimize_Nsamples(t_AOM_best, t_readoutDelay_best, t_wait_best):
    print("\n" + "="*60)
    print("步骤4: 优化 Nsamples (采样数)")
    print("="*60)

    snr_results = []
    time_results = []

    print("候选采样数: {}".format(Nsamples_options))

    for i, Nsamples in enumerate(Nsamples_options):
        instructionArray = PBctl.programPB('RabiSeq',
            [endPulseDuration, t_AOM_best, t_readoutDelay_best, t_wait_best])

        start_time = time.time()
        mean_signal, std_signal = read_fluorescence(Nsamples)
        elapsed_time = time.time() - start_time

        snr = mean_signal / (std_signal + 1e-10) if std_signal > 0 else 0

        snr_results.append(snr)
        time_results.append(elapsed_time)

        print("  [{}/{}] Nsamples = {:5d}, SNR = {:.2f}, time = {:.2f}s".format(
            i+1, len(Nsamples_options), Nsamples, snr, elapsed_time))

    efficiency = np.array(snr_results) / (np.array(time_results) + 1e-10)
    best_idx = np.argmax(efficiency)
    best_Nsamples = Nsamples_options[best_idx]

    print("\n最优 Nsamples = {} (效率 = {:.4f})".format(best_Nsamples, efficiency[best_idx]))

    save_optimization_data(Nsamples_options, snr_results, "Nsamples", "SNR", "Nsamples_opt_")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(Nsamples_options, snr_results, 'b-o')
    ax1.set_xlabel('Nsamples')
    ax1.set_ylabel('SNR')
    ax1.set_title('Nsamples Optimization - SNR')
    ax1.grid(True)

    ax2.plot(Nsamples_options, efficiency, 'r-o')
    ax2.set_xlabel('Nsamples')
    ax2.set_ylabel('Efficiency (SNR/time)')
    ax2.set_title('Nsamples Optimization - Efficiency')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(savePath + "Nsamples_optimization.png", dpi=150)
    plt.show()

    return best_Nsamples


def main():
    print("\n" + "="*60)
    print("NV色心参数优化程序")
    print("="*60)
    print("优化参数: t_AOM, t_readoutDelay, t_wait, Nsamples")
    print("微波频率: {:.4f} GHz".format(microwaveFrequency/1e9))
    print("B210增益: {} dB".format(B210_gain))
    print("="*60)

    print("\n正在配置设备...")

    # 配置SRS/B210
    B210 = SRSctl.initSRS(GPIBaddr, modelName)
    SRSctl.setSRS_Freq(B210, microwaveFrequency)
    SRSctl.setSRS_RFAmplitude(B210, B210_gain)
    SRSctl.setupSRSmodulation(B210, 'RabiSeq')
    SRSctl.enableSRS_RFOutput(B210)

    print("B210 配置完成")

    # 依次优化参数
    t_AOM_best = optimize_t_AOM()
    t_readoutDelay_best = optimize_t_readoutDelay(t_AOM_best, t_wait_fixed=3*us)
    t_wait_best = optimize_t_wait(t_AOM_best, t_readoutDelay_best)
    Nsamples_best = optimize_Nsamples(t_AOM_best, t_readoutDelay_best, t_wait_best)

    # 关闭设备
    SRSctl.disableSRS_RFOutput(B210)

    # 输出最终结果
    print("\n" + "="*60)
    print("优化完成！最优参数如下：")
    print("="*60)
    print("  t_AOM           = {:.1f} us".format(t_AOM_best/1e3))
    print("  t_readoutDelay  = {:.0f} ns".format(t_readoutDelay_best))
    print("  t_wait          = {:.1f} us".format(t_wait_best/1e3))
    print("  Nsamples        = {}".format(Nsamples_best))
    print("="*60)

    # 保存最终结果
    dateTimeStr = strftime("%Y-%m-%d_%Hh%Mm%Ss", localtime())
    resultFile = savePath + "optimization_results_" + dateTimeStr + ".txt"
    with open(resultFile, 'w') as f:
        f.write("NV色心参数优化结果\n")
        f.write("="*40 + "\n")
        f.write("t_AOM           = {:.1f} us\n".format(t_AOM_best/1e3))
        f.write("t_readoutDelay  = {:.0f} ns\n".format(t_readoutDelay_best))
        f.write("t_wait          = {:.1f} us\n".format(t_wait_best/1e3))
        f.write("Nsamples        = {}\n".format(Nsamples_best))
        f.write("="*40 + "\n")

    print("\n结果已保存至: {}".format(resultFile))

    return {
        't_AOM': t_AOM_best,
        't_readoutDelay': t_readoutDelay_best,
        't_wait': t_wait_best,
        'Nsamples': Nsamples_best
    }


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n用户中断，程序退出...")
        sys.exit()
    except Exception as e:
        print("\n错误: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit()
