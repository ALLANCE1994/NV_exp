# NV色心实验控制系统

## 项目简介

本项目用于NV（Nitrogen-Vacancy）色心量子态调控实验的数据采集与控制系统，支持多种DAQ设备，包括myDAQ、USB-7855R FPGA等。

## 目录结构

```
src/python/
├── DAQcontrol_USB7855R.py      # USB-7855R主控制模块（自动检测模式）
├── DAQcontrol_USB7855R_preloaded.py  # USB-7855R预先下载版本
├── DAQcontrol_USB7855R_dynamic.py    # USB-7855R动态下载版本
├── DAQcontrol.py                # 通用DAQ控制模块
├── DAQcontrol_MyDAQ.py          # myDAQ控制模块
├── mainControl.py               # 主控制程序
├── connectionConfig.py          # 连接配置
├── FPGA/                        # FPGA相关文件
│   ├── DAQ_Controller.vhd       # DAQ控制器VHDL代码
│   ├── DAQ_FIFO.vhd            # FIFO模块VHDL代码
│   ├── NV_DAQ_System.vhd       # NV DAQ系统顶层设计
│   ├── NV_DAQ_System.xml       # 系统配置文件
│   └── test2.vi                # 测试VI文件
└── ...
```

## USB-7855R FPGA模块

### 硬件要求

- **设备**: NI USB-7855R FPGA板卡
- **驱动**: NI-RIO驱动
- **Python库**: nifpga

### 软件架构

本项目提供三个版本的USB-7855R控制模块：

#### 1. DAQcontrol_USB7855R.py (自动检测模式)

自动检测FPGA配置状态，优先尝试使用指定bitfile，失败后尝试使用现有配置。

**特性**:
- 自动错误检测和恢复
- 适合常规使用场景

#### 2. DAQcontrol_USB7855R_preloaded.py (预先下载版本)

适用于FPGA配置已预先下载到设备的场景。

**特性**:
- 代码简洁直接
- 需要提前使用LabVIEW或NI MAX下载FPGA配置

#### 3. DAQcontrol_USB7855R_dynamic.py (动态下载版本)

适用于需要在运行时动态下载FPGA配置的场景。

**特性**:
- 使用 `no_run=True` 参数打开会话
- 调用 `download()` 下载bitfile到FPGA
- 调用 `run()` 启动FPGA
- 需要特定版本NI-RIO驱动支持

### 使用方法

#### 选择设备类型

在 `mainControl.py` 中根据设备类型选择导入：

```python
# DAQ_DEVICE_TYPE = 0: myDAQ (使用 nidaqmx)
# DAQ_DEVICE_TYPE = 1: USB-7855R FPGA (使用 nifpga)
# DAQ_DEVICE_TYPE = 2: USB-6363 (使用 nidaqmx)

if conCfg.DAQ_DEVICE_TYPE == 1:
    import DAQcontrol_USB7855R as DAQctl
else:
    import DAQcontrol as DAQctl
```

#### 基本使用示例

```python
import DAQcontrol_USB7855R_dynamic as DAQctl

# 初始化控制器
controller = DAQctl.USB7855RController()

# 检测设备
device_name = controller.find_device()
print(f"使用设备: {device_name}")

# 加载FPGA配置
if controller.load_bitfile():
    print("FPGA配置加载成功")

# 配置采集参数
controller.configure_daq(1000)

# 读取数据
data = controller.read_data(100)
print(f"读取到 {len(data)} 个样本")

# 关闭会话
controller.close()
```

### FPGA配置要求

#### 预先下载模式

1. 使用LabVIEW打开FPGA项目
2. 右键FPGA目标 → 'Run' 下载配置
3. 配置保存在设备非易失性存储中

#### 动态下载模式

1. 确保安装支持动态下载的NI-RIO驱动版本
2. 程序运行时自动下载bitfile到FPGA
3. 调用 `download()` 和 `run()` 方法

### 寄存器定义

| 寄存器名称 | 地址 | 说明 |
|-----------|------|------|
| SAMPLE_COUNT | 0x00 | 采样数量 |
| SAMPLING_DIV | 0x01 | 采样分频系数 |
| TRIGGER_EDGE | 0x02 | 触发边沿 |
| CONTROL | 0x03 | 控制寄存器 |
| STATUS | 0x04 | 状态寄存器 |

### 注意事项

1. **设备兼容性**: USB-7855R不是DAQ卡，必须使用nifpga库，不能使用nidaqmx
2. **驱动版本**: 动态下载功能需要特定版本的NI-RIO驱动支持
3. **bitfile匹配**: bitfile必须与FPGA硬件型号匹配
4. **预先下载**: 建议在支持的电脑上预先下载FPGA配置，以避免驱动兼容性问题

## FPGA文件说明

### VHDL源文件

- `DAQ_Controller.vhd`: DAQ控制器核心逻辑
- `DAQ_FIFO.vhd`: 数据FIFO缓冲模块
- `NV_DAQ_System.vhd`: 顶层系统设计，整合所有模块

### 配置文件

- `NV_DAQ_System.xml`: 系统配置参数
- `test2.vi`: LabVIEW测试程序

### Bitfile文件

- 位于 `D:\FROM_C\USB7855\FPGA Bitfiles\`
- `.lvbitx` 格式为NI FPGA配置文件

## 依赖项

```
nifpga>=<version>
numpy
```

## 故障排除

### 错误码 -52023 (NiFpga_Status_BitfileNotDownloaded)

**原因**: FPGA上没有匹配的bitfile配置

**解决方案**:
1. 使用LabVIEW预先下载FPGA配置
2. 在NI MAX中右键设备 → 'Download FPGA'
3. 或使用动态下载版本（需要驱动支持）

### AttributeError: 'Session' object has no attribute 'write'

**原因**: 使用了错误的nifpga API

**解决方案**:
```python
# 错误
session.write(reg_addr, data)

# 正确
session.registers[reg_name].write(data)
```

## 版本历史

- **2026-05-05**: 添加USB-7855R FPGA控制模块，支持预先下载和动态下载两种模式
- **2026-05-05**: 修复nifpga Session API调用问题
- **2026-05-05**: 添加FPGA VHDL源文件和配置文件

## 联系方式

如有问题，请提交Issue或联系项目维护者。