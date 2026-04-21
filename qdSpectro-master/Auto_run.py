# Auto_run.py
# 自动运行ESR实验并优化参数

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

# 添加项目路径
sys.path.append(r"e:\转移\手把手教你做NV色心实验\qdSpectro-master")

# 导入相关模块
import mainControl_MyDAQ
import ESRconfig

class ESR_Auto_Optimizer:
    def __init__(self):
        self.max_iterations = 10
        self.improvement_threshold = 0.1  # 10%的改进
        self.best_contrast = 0
        self.best_params = {
            'startFreq': ESRconfig.startFreq,
            'endFreq': ESRconfig.endFreq,
            'N_scanPts': ESRconfig.N_scanPts,
            'microwavePower': ESRconfig.microwavePower,
            't_duration': ESRconfig.t_duration,
            'Nsamples': ESRconfig.Nsamples,
            'Navg': ESRconfig.Navg
        }
        self.current_iteration = 0
        self.saved_data_dir = ESRconfig.savePath
        
    def run_experiment(self):
        """运行ESR实验"""
        print(f"\n=== 运行ESR实验 {self.current_iteration+1}/{self.max_iterations} ===")
        try:
            # 运行实验
            mainControl_MyDAQ.run_experiment('ESRconfig')
            return True
        except Exception as e:
            print(f"实验运行失败: {e}")
            return False
    
    def find_latest_data_file(self):
        """查找最新的数据文件"""
        if not os.path.exists(self.saved_data_dir):
            print(f"数据目录不存在: {self.saved_data_dir}")
            return None
        
        # 获取所有ESR数据文件
        files = [f for f in os.listdir(self.saved_data_dir) if f.startswith('ESR_') and f.endswith('.txt') and '_PARAMS' not in f]
        if not files:
            print("未找到数据文件")
            return None
        
        # 按修改时间排序，返回最新的
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.saved_data_dir, x)), reverse=True)
        latest_file = os.path.join(self.saved_data_dir, files[0])
        print(f"使用最新数据文件: {latest_file}")
        return latest_file
    
    def load_data(self, file_path):
        """加载ESR数据"""
        try:
            data = np.loadtxt(file_path)
            frequencies = data[:, 0]
            signals = data[:, 1]
            backgrounds = data[:, 2]
            return frequencies, signals, backgrounds
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None, None, None
    
    def calculate_contrast(self, signals, backgrounds):
        """计算对比度"""
        # 使用ratio_SignalOverReference模式
        with np.errstate(divide='ignore'):
            contrast = np.divide(signals, backgrounds)
        # 移除异常值
        contrast = contrast[np.isfinite(contrast)]
        if len(contrast) == 0:
            return 0
        return np.mean(contrast)
    
    def analyze_spectrum(self, frequencies, signals, backgrounds):
        """分析谱线质量"""
        contrast = self.calculate_contrast(signals, backgrounds)
        
        # 计算信噪比
        signal_mean = np.mean(signals)
        signal_std = np.std(signals)
        snr = signal_mean / signal_std if signal_std > 0 else 0
        
        # 计算谱线宽度（半高全宽）
        if len(signals) > 3:
            # 找到峰值
            peak_idx = np.argmax(signals)
            peak_value = signals[peak_idx]
            half_max = peak_value / 2
            
            # 找到半最大值的左右点
            left_idx = np.argmax(signals[:peak_idx] < half_max)
            right_idx = peak_idx + np.argmax(signals[peak_idx:] < half_max)
            
            if left_idx < peak_idx and right_idx > peak_idx:
                fwhm = frequencies[right_idx] - frequencies[left_idx]
            else:
                fwhm = 0
        else:
            fwhm = 0
        
        return {
            'contrast': contrast,
            'snr': snr,
            'fwhm': fwhm,
            'signal_mean': signal_mean,
            'signal_std': signal_std
        }
    
    def optimize_parameters(self, spectrum_analysis):
        """优化实验参数"""
        current_contrast = spectrum_analysis['contrast']
        current_snr = spectrum_analysis['snr']
        
        # 检查是否有改进
        if current_contrast > self.best_contrast * (1 + self.improvement_threshold):
            print(f"✓ 对比度改进: {self.best_contrast:.4f} → {current_contrast:.4f}")
            self.best_contrast = current_contrast
            self.best_params.update({
                'startFreq': ESRconfig.startFreq,
                'endFreq': ESRconfig.endFreq,
                'N_scanPts': ESRconfig.N_scanPts,
                'microwavePower': ESRconfig.microwavePower,
                't_duration': ESRconfig.t_duration,
                'Nsamples': ESRconfig.Nsamples,
                'Navg': ESRconfig.Navg
            })
        
        # 参数优化策略
        improvements = []
        
        # 1. 优化微波功率
        if current_contrast < 1.2 and ESRconfig.microwavePower < 30:
            new_power = min(ESRconfig.microwavePower + 2, 30)
            improvements.append(f"微波功率: {ESRconfig.microwavePower} → {new_power}")
            ESRconfig.microwavePower = new_power
        
        # 2. 优化采样时间
        if current_snr < 5 and ESRconfig.t_duration < 1000*ESRconfig.us:
            new_duration = min(ESRconfig.t_duration * 1.5, 1000*ESRconfig.us)
            improvements.append(f"采样时间: {ESRconfig.t_duration/ESRconfig.us:.1f}μs → {new_duration/ESRconfig.us:.1f}μs")
            ESRconfig.t_duration = new_duration
        
        # 3. 优化样本数
        if current_snr < 10 and ESRconfig.Nsamples < 10000:
            new_samples = min(ESRconfig.Nsamples * 2, 10000)
            improvements.append(f"样本数: {ESRconfig.Nsamples} → {new_samples}")
            ESRconfig.Nsamples = new_samples
        
        # 4. 优化平均次数
        if current_contrast < 1.1 and ESRconfig.Navg < 20:
            new_avg = min(ESRconfig.Navg + 2, 20)
            improvements.append(f"平均次数: {ESRconfig.Navg} → {new_avg}")
            ESRconfig.Navg = new_avg
        
        # 5. 优化频率范围
        if spectrum_analysis['fwhm'] > 0:
            # 根据FWHM调整频率范围
            freq_range = ESRconfig.endFreq - ESRconfig.startFreq
            if freq_range > 100e6:
                # 缩小频率范围
                center_freq = (ESRconfig.startFreq + ESRconfig.endFreq) / 2
                new_range = min(freq_range * 0.8, 50e6)
                ESRconfig.startFreq = center_freq - new_range/2
                ESRconfig.endFreq = center_freq + new_range/2
                improvements.append(f"频率范围: {freq_range/1e6:.1f}MHz → {new_range/1e6:.1f}MHz")
        
        # 6. 优化扫描点数
        if ESRconfig.N_scanPts < 501:
            new_scan_pts = min(ESRconfig.N_scanPts + 50, 501)
            improvements.append(f"扫描点数: {ESRconfig.N_scanPts} → {new_scan_pts}")
            ESRconfig.N_scanPts = new_scan_pts
        
        # 更新scannedParam
        ESRconfig.scannedParam = np.linspace(
            ESRconfig.startFreq, 
            ESRconfig.endFreq, 
            ESRconfig.N_scanPts, 
            endpoint=True
        )
        
        if improvements:
            print("参数优化:")
            for improvement in improvements:
                print(f"  - {improvement}")
        else:
            print("参数已优化至最佳状态")
        
        return len(improvements) > 0
    
    def plot_results(self, frequencies, signals, backgrounds, spectrum_analysis):
        """绘制结果"""
        plt.figure(figsize=(12, 6))
        
        # 绘制信号和背景
        plt.subplot(2, 1, 1)
        plt.plot(frequencies/1e9, signals, 'b-', label='信号')
        plt.plot(frequencies/1e9, backgrounds, 'r-', label='背景')
        plt.xlabel('频率 (GHz)')
        plt.ylabel('计数')
        plt.title(f'ESR谱线 - 迭代 {self.current_iteration+1}')
        plt.legend()
        
        # 绘制对比度
        contrast = np.divide(signals, backgrounds)
        plt.subplot(2, 1, 2)
        plt.plot(frequencies/1e9, contrast, 'g-')
        plt.xlabel('频率 (GHz)')
        plt.ylabel('对比度')
        plt.title(f'对比度 - 平均值: {spectrum_analysis["contrast"]:.4f}, SNR: {spectrum_analysis["snr"]:.2f}')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.saved_data_dir, f'ESR_auto_run_{self.current_iteration+1}.png'))
        plt.close()
    
    def run(self):
        """运行自动优化循环"""
        print("=== ESR实验自动优化开始 ===")
        
        while self.current_iteration < self.max_iterations:
            # 运行实验
            if not self.run_experiment():
                print("实验失败，跳过本次迭代")
                self.current_iteration += 1
                continue
            
            # 加载数据
            data_file = self.find_latest_data_file()
            if not data_file:
                print("未找到数据文件，跳过本次迭代")
                self.current_iteration += 1
                continue
            
            frequencies, signals, backgrounds = self.load_data(data_file)
            if frequencies is None:
                print("加载数据失败，跳过本次迭代")
                self.current_iteration += 1
                continue
            
            # 分析谱线
            spectrum_analysis = self.analyze_spectrum(frequencies, signals, backgrounds)
            print(f"谱线分析结果:")
            print(f"  平均对比度: {spectrum_analysis['contrast']:.4f}")
            print(f"  信噪比: {spectrum_analysis['snr']:.2f}")
            print(f"  半高全宽: {spectrum_analysis['fwhm']/1e6:.3f} MHz")
            
            # 绘制结果
            self.plot_results(frequencies, signals, backgrounds, spectrum_analysis)
            
            # 优化参数
            improved = self.optimize_parameters(spectrum_analysis)
            
            # 检查是否达到停止条件
            if not improved and self.current_iteration > 2:
                print("\n=== 优化完成，达到最佳参数 ===")
                break
            
            self.current_iteration += 1
            
            # 等待一段时间再进行下一次实验
            if self.current_iteration < self.max_iterations:
                print(f"\n等待5秒后开始下一次实验...")
                time.sleep(5)
        
        # 输出最佳参数
        print("\n=== 最佳参数 ===")
        print(f"起始频率: {self.best_params['startFreq']/1e9:.3f} GHz")
        print(f"结束频率: {self.best_params['endFreq']/1e9:.3f} GHz")
        print(f"扫描点数: {self.best_params['N_scanPts']}")
        print(f"微波功率: {self.best_params['microwavePower']} dBm")
        print(f"采样时间: {self.best_params['t_duration']/ESRconfig.us:.1f} μs")
        print(f"样本数: {self.best_params['Nsamples']}")
        print(f"平均次数: {self.best_params['Navg']}")
        print(f"最佳对比度: {self.best_contrast:.4f}")
        
        print("\n=== ESR实验自动优化结束 ===")

if __name__ == "__main__":
    optimizer = ESR_Auto_Optimizer()
    optimizer.run()