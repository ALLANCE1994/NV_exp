# USB-7855R FPGA模块说明

## 概述

本目录包含NV色心实验控制系统中使用的NI USB-7855R FPGA相关文件，包括VHDL源代码、配置文件和测试程序。

## 硬件平台

- **设备**: NI USB-7855R
- **类型**: FPGA板卡（不是传统DAQ卡）
- **接口**: USB 3.0
- **编程方式**: LabVIEW FPGA / nifpga Python API

## 文件说明

### VHDL源代码

#### DAQ_Controller.vhd
DAQ控制器核心逻辑，负责：
- 数据采集时序控制
- 触发信号处理
- 采样分频控制

#### DAQ_FIFO.vhd
数据FIFO缓冲模块，负责：
- 数据缓存
- 流式数据传输
- 跨时钟域处理

#### NV_DAQ_System.vhd
NV DAQ系统顶层设计，整合所有子模块：
- 集成DAQ_Controller
- 集成DAQ_FIFO
- 定义系统接口

### 配置文件

#### NV_DAQ_System.xml
系统配置文件，包含：
- 模块参数配置
- 时钟设置
- 接口定义

#### test2.vi
LabVIEW测试程序，用于：
- FPGA功能验证
- 硬件调试
- bitfile下载测试

### 仿真文件

位于 `IP_BlockSimFiles/xsim.dir/` 目录：
- xsim.dbg: 调试信息
- xsim.mem: 内存映射
- xsim.rtti: 运行时类型信息

## FPGA寄存器映射

| 寄存器名称 | 地址 | 数据宽度 | 说明 |
|----------|------|---------|------|
| CLK_40MHZ | - | 1-bit | 40MHz时钟指示（只读） |
| FIFO | - | 32-bit | 数据FIFO接口 |
| SAMPLE_COUNT | 0x00 | 16-bit | 采样数量设置 |
| SAMPLING_DIV | 0x01 | 16-bit | 采样分频系数 |
| TRIGGER_EDGE | 0x02 | 1-bit | 触发边沿选择 |
| CONTROL | 0x03 | 8-bit | 控制寄存器 |
| STATUS | 0x04 | 8-bit | 状态寄存器 |

### 控制寄存器位定义

| 位 | 名称 | 说明 |
|----|------|------|
| 0 | START | 启动采集 |
| 1 | RESET | 重置逻辑 |
| 2 | ENABLE | 使能控制 |

### 状态寄存器位定义

| 位 | 名称 | 说明 |
|----|------|------|
| 0 | BUSY | 采集忙标志 |
| 1 | DONE | 采集完成标志 |
| 2 | FIFO_EMPTY | FIFO空标志 |
| 3 | ERROR | 错误标志 |

## 使用方法

### 1. 创建FPGA项目

1. 打开LabVIEW
2. 创建FPGA项目
3. 添加现有VHDL文件或创建新的FPGA VI
4. 配置为目标设备 (NI USB-7855R)

### 2. 编译FPGA程序

1. 在项目中打开FPGA VI
2. 点击"Run"或编译
3. 等待编译完成（可能需要几分钟）
4. bitfile (.lvbitx) 将生成在指定目录

### 3. 下载bitfile到设备

#### 方法1: LabVIEW下载
- 打开编译后的bitfile
- 右键FPGA目标 → 'Run'

#### 方法2: NI MAX下载
- 打开NI MAX
- 找到USB-7855R设备
- 右键 → 'Download FPGA'

#### 方法3: 动态下载（需要特定驱动）
- 使用Python nifpga库
- 调用 `session.download()` 方法

### 4. Python控制示例

```python
import nifpga

# 打开会话
session = nifpga.Session("path/to/bitfile.lvbitx", "RIO0")

# 下载并运行（动态模式）
session.download()
session.run()

# 读取数据
fifo_data = session.fifos['FIFO'].read(1000, timeout_ms=1000)

# 写入寄存器
session.registers['SAMPLE_COUNT'].write(1000)

# 关闭会话
session.close()
```

## 注意事项

### 驱动要求

- 动态下载功能需要NI-RIO驱动支持
- 建议使用与LabVIEW版本兼容的驱动
- 部分驱动版本可能不支持动态下载

### 预先下载

推荐预先下载FPGA配置：
1. 在装有正确版本LabVIEW的电脑上编译bitfile
2. 使用LabVIEW或NI MAX下载到设备
3. 设备重启后配置会自动加载

### 位文件兼容性

- bitfile必须针对正确的设备型号编译
- 不同型号设备的bitfile不通用
- USB-7855R的bitfile不能用于其他RIO设备

### 时钟要求

- 系统时钟: 40MHz
- 采样时钟由分频系数控制
- 确保时钟源稳定

## 故障诊断

### 错误码 -52023

**错误**: NiFpga_Status_BitfileNotDownloaded

**原因**: FPGA上没有匹配的bitfile配置

**解决方案**:
1. 使用LabVIEW下载bitfile
2. 在NI MAX中执行 'Download FPGA'
3. 或确保使用支持动态下载的驱动版本

### 连接失败

**可能原因**:
1. 设备未正确连接
2. 驱动未安装
3. 设备被其他程序占用

**解决方案**:
1. 检查USB连接
2. 重启NI MAX验证设备
3. 关闭其他可能使用设备的程序

### FIFO读取无数据

**可能原因**:
1. 采集未启动
2. 触发条件未满足
3. FIFO未使能

**解决方案**:
1. 检查控制寄存器设置
2. 验证触发信号
3. 确认FPGA逻辑正确

## 更新日志

### 2026-05-05
- 添加完整的VHDL源文件
- 添加系统配置文件
- 添加测试程序
- 验证动态下载功能正常

## 相关文档

- [主README](../README.md)
- [USB-7855R Python控制模块说明](../README.md#usb-7855r-fpga模块)