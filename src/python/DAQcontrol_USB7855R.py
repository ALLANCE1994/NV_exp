# DAQ控制 - NI USB-7855R专用
# 用于NV色心实验的FPGA数据采集控制
# 使用 NI-FPGA Python API (nifpga)

import nifpga
import sys
import os
import numpy as np
import connectionConfig

# FPGA寄存器地址定义
FPGA_REG = {
    'SAMPLE_COUNT': 0x00,
    'SAMPLING_DIV': 0x01,
    'TRIGGER_EDGE': 0x02,
    'CONTROL': 0x03,
    'STATUS': 0x04
}

# 控制寄存器位定义
FPGA_CTRL = {
    'START': 0x01,
    'RESET': 0x02,
    'ENABLE': 0x04
}

# 状态寄存器位定义
FPGA_STAT = {
    'BUSY': 0x01,
    'DONE': 0x02,
    'FIFO_EMPTY': 0x04,
    'ERROR': 0x08
}

# FPGA配置文件路径
FPGA_BITFILE_DIR = r"D:\FROM_C\USB7855\FPGA Bitfiles"
FPGA_BITFILE_NAME = "usb7855_test_tset_dQx7o23LGbY.lvbitx"
FPGA_BITFILE_PATH = os.path.join(FPGA_BITFILE_DIR, FPGA_BITFILE_NAME)

# 常见设备名称列表（统一管理）
COMMON_DEVICE_NAMES = [
    "RIO0", "RIO1", "RIO2",          # CompactRIO/R Series
    "Dev1", "Dev2", "Dev3", "Dev4", "Dev5",  # 通用设备名称
    "cDAQ1Mod1", "cDAQ1Mod2",        # CompactDAQ模块
    "USB7855R", "7855R"              # 设备型号名称
]


class USB7855RController:
    """NI USB-7855R FPGA控制器类"""
    
    def __init__(self):
        self.session = None
        self.device_name = "RIO0"
    
    def check_bitfile(self):
        """检查FPGA配置文件是否存在"""
        if os.path.exists(FPGA_BITFILE_PATH):
            print(f"✅ FPGA配置文件: {FPGA_BITFILE_PATH}")
            return True
        else:
            print(f"❌ FPGA配置文件不存在: {FPGA_BITFILE_PATH}")
            files = [f for f in os.listdir(FPGA_BITFILE_DIR) 
                     if f.endswith('.lvbitx')] if os.path.exists(FPGA_BITFILE_DIR) else []
            if files:
                print(f"📋 可用的FPGA配置文件:")
                for i, f in enumerate(files):
                    print(f"   {i+1}. {f}")
            return False
    
    def _test_device(self, dev_name):
        """内部方法：测试单个设备连接"""
        test_bitfile = FPGA_BITFILE_PATH if os.path.exists(FPGA_BITFILE_PATH) else None
        if not test_bitfile:
            return None  # 无法测试
        
        try:
            with nifpga.Session(test_bitfile, dev_name, no_run=True):
                return 'success'
        except nifpga.ResourceNotFoundError:
            return None
        except nifpga.ErrorStatus as e:
            if "bitfile" in str(e).lower() or "Bitfile" in str(e):
                return 'bitfile_mismatch'
            return None
        except Exception:
            return None
    
    def find_device(self):
        """查找第一个可用的FPGA设备"""
        print("🔍 正在检测FPGA设备...")
        
        for dev_name in COMMON_DEVICE_NAMES:
            result = self._test_device(dev_name)
            if result == 'success':
                print(f"   ✅ 成功访问设备: {dev_name}")
                self.device_name = dev_name
                return dev_name
            elif result == 'bitfile_mismatch':
                print(f"   ✅ 发现设备: {dev_name} (FPGA配置不匹配)")
                self.device_name = dev_name
                return dev_name
        
        print("   ❌ 所有常见设备名称都无法访问")
        print("   请在NI MAX中确认设备名称")
        return self.device_name
    
    def list_devices(self):
        """列出所有可用的FPGA设备"""
        print("📋 正在扫描可用的FPGA设备...")
        available = []
        
        for dev_name in COMMON_DEVICE_NAMES:
            result = self._test_device(dev_name)
            if result in ('success', 'bitfile_mismatch'):
                available.append(dev_name)
        
        if not available:
            print("❌ 未找到任何FPGA设备")
            return []
        
        print("📋 可用的FPGA设备:")
        for i, device in enumerate(available):
            print(f"   {i+1}. {device}")
        return available
    
    def update_config(self):
        """更新connectionConfig中的设备配置"""
        connectionConfig.DAQ_APDInput = f"{self.device_name}/ai0"
        connectionConfig.DAQ_SampleClk = "PFI0"
        connectionConfig.DAQ_StartTrig = "PFI1"
        print(f"✅ 设备配置已更新为: {self.device_name}")
    
    def load_bitfile(self, use_existing_config=True):
        """加载FPGA配置文件
        
        参数:
            use_existing_config: 如果FPGA已有配置，是否尝试使用现有配置打开会话
                               True: 先尝试使用指定bitfile，失败则尝试使用现有配置
                               False: 只使用指定的bitfile，失败则报错
        """
        if self.session is not None:
            self.close()
        
        # 尝试1: 使用指定的bitfile打开会话
        try:
            print(f"   正在打开FPGA会话: {self.device_name}")
            print(f"   使用配置文件: {FPGA_BITFILE_PATH}")
            self.session = nifpga.Session(FPGA_BITFILE_PATH, self.device_name)
            print(f"✅ FPGA配置文件已成功加载: {FPGA_BITFILE_PATH}")
            return True
        except nifpga.ErrorStatus as excpt:
            error_code = excpt.code if hasattr(excpt, 'code') else -1
            error_msg = str(excpt)
            print(f"⚠️ NI-FPGA错误 (代码: {error_code}): {excpt}")
            
            # 错误码 -52023: NiFpga_Status_BitfileNotDownloaded
            # 注意：错误码可能在消息中，需要检查两种情况
            is_bitfile_not_downloaded = (error_code == -52023) or ("52023" in error_msg)
            
            if is_bitfile_not_downloaded and use_existing_config:
                print("\n   尝试使用FPGA中已有的配置...")
                return self._try_existing_config()
            
            if error_code == -52023:
                print("\n" + "="*60)
                print("错误分析: FPGA配置文件未下载到设备")
                print("="*60)
                print("解决方案:")
                print("  1. 使用LabVIEW打开项目，右键FPGA目标 -> 'Run'")
                print("  2. 在NI MAX中右键设备 -> 'Download FPGA'")
                print("  3. 使用NI CompactRIO Configuration Utility")
                print("="*60 + "\n")
            return False
        except Exception as excpt:
            print(f"⚠️ 加载FPGA配置文件失败: {type(excpt).__name__}. {excpt}")
            return False
    
    def _try_existing_config(self):
        """尝试使用FPGA中已有的配置打开会话"""
        try:
            # 方法1: 使用no_run=True参数，不立即运行
            print(f"   尝试连接到FPGA已有配置 (no_run模式)...")
            self.session = nifpga.Session(FPGA_BITFILE_PATH, self.device_name, no_run=True)
            print(f"   会话已打开，尝试启动FPGA...")
            self.session.run()
            print(f"✅ 成功使用FPGA中已有的配置")
            print("   ⚠️ 注意: 当前使用的是FPGA中已有的配置")
            return True
        except nifpga.ErrorStatus as excpt:
            print(f"   ❌ no_run模式失败: {type(excpt).__name__}. {excpt}")
            
        try:
            # 方法2: 尝试不指定bitfile，只连接到设备
            print(f"   尝试直接连接到设备...")
            import inspect
            # 检查Session类的签名，看看是否有其他参数
            sig = inspect.signature(nifpga.Session.__init__)
            print(f"   Session构造函数参数: {list(sig.parameters.keys())}")
            
            # 尝试使用resource参数直接连接
            self.session = nifpga.Session(resource=self.device_name)
            print(f"✅ 成功直接连接到设备")
            return True
        except Exception as excpt2:
            print(f"   ❌ 直接连接失败: {type(excpt2).__name__}. {excpt2}")
        
        print("\n" + "="*60)
        print("请确保FPGA配置已预先下载:")
        print("  1. 在另一台电脑上使用LabVIEW下载FPGA配置")
        print("  2. 确保下载的配置与当前指定的bitfile匹配")
        print("  3. 在NI MAX中验证设备状态")
        print("="*60 + "\n")
        return False
    
    def calculate_divider(self, target_rate_hz=None):
        """计算采样分频系数"""
        if target_rate_hz is None:
            target_rate_hz = connectionConfig.DAQ_MaxSamplingRate
        divider = int(connectionConfig.FPGA_CLK_FREQ / target_rate_hz / 2) - 1
        return max(0, min(65535, divider))
    
    def write_register(self, reg_addr, data):
        """向FPGA寄存器写入数据"""
        if self.session is None:
            raise RuntimeError("FPGA会话未初始化")
        
        # 获取寄存器名称映射
        reg_name = None
        for name, addr in FPGA_REG.items():
            if addr == reg_addr:
                reg_name = name
                break
        
        if reg_name is None:
            raise ValueError(f"未知的寄存器地址: 0x{reg_addr:02X}")
        
        # 检查寄存器是否存在
        if reg_name not in self.session.registers:
            print(f"⚠️ 寄存器 '{reg_name}' 不存在于bitfile中")
            print(f"   可用的寄存器: {list(self.session.registers.keys())}")
            raise KeyError(f"寄存器 '{reg_name}' 不存在")
        
        self.session.registers[reg_name].write(data)
        print(f"   写入寄存器 {reg_name} (0x{reg_addr:02X}): {data}")
    
    def read_register(self, reg_addr):
        """从FPGA寄存器读取数据"""
        if self.session is None:
            raise RuntimeError("FPGA会话未初始化")
        
        # 获取寄存器名称映射
        reg_name = None
        for name, addr in FPGA_REG.items():
            if addr == reg_addr:
                reg_name = name
                break
        
        if reg_name is None:
            raise ValueError(f"未知的寄存器地址: 0x{reg_addr:02X}")
        
        # 检查寄存器是否存在
        if reg_name not in self.session.registers:
            print(f"⚠️ 寄存器 '{reg_name}' 不存在于bitfile中")
            print(f"   可用的寄存器: {list(self.session.registers.keys())}")
            raise KeyError(f"寄存器 '{reg_name}' 不存在")
        
        return self.session.registers[reg_name].read()
    
    def configure_fpga(self, Nsamples, sampling_rate_hz=None):
        """配置FPGA采集参数"""
        divider = self.calculate_divider(sampling_rate_hz)
        self.write_register(FPGA_REG['SAMPLE_COUNT'], Nsamples)
        self.write_register(FPGA_REG['SAMPLING_DIV'], divider)
        self.write_register(FPGA_REG['TRIGGER_EDGE'], 0)
        print(f"FPGA配置完成: 采样点数={Nsamples}, 分频系数={divider}")
    
    def configure_daq(self, Nsamples, load_fpga=True):
        """配置USB-7855R进行数据采集"""
        try:
            if load_fpga and not self.load_bitfile():
                raise RuntimeError("无法加载FPGA配置")
            
            if self.session is None:
                raise RuntimeError("无法初始化FPGA会话")
            
            NsampsPerDAQread = 2 * Nsamples
            self.configure_fpga(NsampsPerDAQread)
            print(f"USB-7855R DAQ配置完成: {Nsamples} samples/scan")
            return self.session
        except Exception as excpt:
            print(f'配置DAQ时出错: {type(excpt).__name__}. {excpt}')
            self.close()
            sys.exit()
    
    def read_data(self, N, timeout=10.0):
        """从FPGA读取采集数据"""
        if self.session is None:
            raise RuntimeError("FPGA会话未初始化")
        
        try:
            counts = self.session.fifos['AI_FIFO'].read(N, timeout)
            return [counts] if not isinstance(counts, list) else counts
        except nifpga.ErrorStatus as excpt:
            print(f'FPGA读取错误: {excpt}')
            raise
    
    def read_averaged(self, N, N_avg=1, timeout=10.0):
        """读取数据并进行平均"""
        all_data = [self.read_data(N, timeout) for _ in range(N_avg)]
        return np.mean(np.array(all_data), axis=0).tolist()
    
    def get_status(self):
        """获取FPGA状态"""
        status_raw = self.read_register(FPGA_REG['STATUS'])
        return {
            'busy': bool(status_raw & FPGA_STAT['BUSY']),
            'done': bool(status_raw & FPGA_STAT['DONE']),
            'fifo_empty': bool(status_raw & FPGA_STAT['FIFO_EMPTY']),
            'error': bool(status_raw & FPGA_STAT['ERROR'])
        }
    
    def reset(self):
        """重置FPGA采集逻辑"""
        self.write_register(FPGA_REG['CONTROL'], FPGA_CTRL['RESET'])
        self.write_register(FPGA_REG['CONTROL'], 0x00)
        print("FPGA已重置")
    
    def start(self):
        """启动FPGA采集"""
        self.write_register(FPGA_REG['CONTROL'], FPGA_CTRL['ENABLE'] | FPGA_CTRL['START'])
        print("FPGA采集已启动")
    
    def stop(self):
        """停止FPGA采集"""
        self.write_register(FPGA_REG['CONTROL'], 0x00)
        print("FPGA采集已停止")
    
    def close(self):
        """关闭FPGA会话"""
        if self.session is not None:
            self.session.close()
            self.session = None
            print("FPGA会话已关闭")


# 全局控制器实例（兼容原有API）
_controller = USB7855RController()
fpga_session = None  # 保持向后兼容


# 兼容原有API的函数
def checkFPGAbitfile():
    return _controller.check_bitfile()

def getFirstDAQDevice():
    return _controller.find_device()

def updateDeviceConfig(device_name):
    _controller.device_name = device_name
    _controller.update_config()

def listDAQDevices():
    return _controller.list_devices()

def loadFPGAbitfile(device_name=FPGA_BITFILE_PATH, bitfile_path=FPGA_BITFILE_PATH):
    if device_name != FPGA_BITFILE_PATH:  # 检查是否传入了设备名
        _controller.device_name = device_name
    global fpga_session
    result = _controller.load_bitfile()
    fpga_session = _controller.session
    return result

def writeFPGAregister(reg_addr, data):
    _controller.write_register(reg_addr, data)

def readFPGAregister(reg_addr):
    return _controller.read_register(reg_addr)

def configureFPGA(Nsamples, sampling_rate_hz=None):
    _controller.configure_fpga(Nsamples, sampling_rate_hz)

def configureDAQ(Nsamples, load_fpga=True):
    global fpga_session
    session = _controller.configure_daq(Nsamples, load_fpga)
    fpga_session = _controller.session
    return session

def readDAQ(N, timeout=10.0):
    return _controller.read_data(N, timeout)

def readDAQ_Averaged(N, N_avg=1, timeout=10.0):
    return _controller.read_averaged(N, N_avg, timeout)

def closeDAQTask():
    _controller.close()

def getFPGAStatus():
    return _controller.get_status()

def resetFPGA():
    _controller.reset()

def startFPGA():
    _controller.start()

def stopFPGA():
    _controller.stop()

def configureDAQ_USB7855R(Nsamples):
    return configureDAQ(Nsamples)

def testDAQConnection(device_name):
    print(f"\n🔍 测试设备连接: {device_name}")
    result = _controller._test_device(device_name)
    if result == 'success':
        print(f"   ✅ 成功连接到设备: {device_name}")
        return True
    elif result == 'bitfile_mismatch':
        print(f"   ⚠️ 设备存在但FPGA配置不匹配: {device_name}")
        return True
    elif result is None:
        print(f"   ⚠️ 没有找到FPGA配置文件，无法测试设备连接")
        return False
    else:
        print(f"   ❌ 无法连接到设备")
        return False


# 初始化检查
checkFPGAbitfile()


if __name__ == "__main__":
    print("="*60)
    print("NI USB-7855R FPGA控制模块测试 (NI-FPGA API)")
    print("="*60)
    
    try:
        print("\n0. 检测FPGA设备...")
        device_name = _controller.find_device()
        
        if not device_name:
            print("❌ 未找到FPGA设备")
            sys.exit(1)
        
        _controller.update_config()
        print(f"   使用设备: {device_name}")
        
        if not testDAQConnection(device_name):
            print("\n⚠️ 设备连接失败，请检查设备连接")
            sys.exit(1)
        
        print("\n1. 加载FPGA配置文件...")
        if not _controller.load_bitfile():
            print("\n⚠️ 警告：无法加载FPGA配置")
            print("   如果FPGA配置已预先加载，可以继续测试...")
        
        if _controller.session is None:
            print("\n❌ FPGA会话未初始化，跳过后续测试步骤")
            print("✅ 设备检测测试完成！")
            sys.exit(0)
        
        print("\n2. 配置DAQ...")
        _controller.configure_daq(1000, load_fpga=False)
        
        print("\n3. 获取FPGA状态...")
        status = _controller.get_status()
        print(f"   FPGA状态: {status}")
        
        print("\n4. 启动FPGA采集...")
        _controller.start()
        
        print("\n5. 读取数据...")
        try:
            data = _controller.read_data(100)
            print(f"   读取到 {len(data)} 个样本")
            print(f"   数据范围: {min(data):.4f} ~ {max(data):.4f}")
            print(f"   数据平均值: {sum(data)/len(data):.4f}")
        except Exception as e:
            print(f"   ⚠️ 数据读取演示失败: {e}")
        
        print("\n6. 停止FPGA采集...")
        _controller.stop()
        
        print("\n7. 关闭FPGA会话...")
        _controller.close()
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()