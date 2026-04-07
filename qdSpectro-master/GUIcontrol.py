#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUIcontrol.py

GUI控制程序，用于配置和运行NV色心实验
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import importlib
import numpy as np
from time import localtime, strftime

class NVExperimentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NV色心实验控制")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 设置字体
        self.style = ttk.Style()
        self.style.configure("TLabel", font=('SimHei', 10))
        self.style.configure("TButton", font=('SimHei', 10))
        self.style.configure("TCombobox", font=('SimHei', 10))
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 实验类型选择
        self.create_experiment_selector()
        
        # 参数设置区域
        self.params_frame = ttk.LabelFrame(self.main_frame, text="实验参数", padding="10")
        self.params_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 保存设置区域
        self.save_frame = ttk.LabelFrame(self.main_frame, text="保存设置", padding="10")
        self.save_frame.pack(fill=tk.X, pady=10)
        
        # 运行控制区域
        self.run_frame = ttk.LabelFrame(self.main_frame, text="运行控制", padding="10")
        self.run_frame.pack(fill=tk.X, pady=10)
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(self.main_frame, text="运行结果", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 初始化变量
        self.exp_config = None
        self.exp_params = {}
        self.save_path = os.getcwd() + "\\Saved_Data\\"
        
        # 创建保存设置控件
        self.create_save_settings()
        
        # 创建运行控制控件
        self.create_run_controls()
        
        # 创建结果显示控件
        self.create_result_display()
        
        # 默认选择ESR实验
        self.experiment_var.set("ESRconfig")
        self.load_experiment_config()
    
    def create_experiment_selector(self):
        """创建实验类型选择器"""
        selector_frame = ttk.LabelFrame(self.main_frame, text="实验类型", padding="10")
        selector_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(selector_frame, text="选择实验类型：").pack(side=tk.LEFT, padx=5)
        
        self.experiment_var = tk.StringVar()
        experiment_options = ["ESRconfig", "Rabiconfig", "T1config", "T2config", "XY8config", "correlSpecconfig"]
        
        self.experiment_combo = ttk.Combobox(selector_frame, textvariable=self.experiment_var, values=experiment_options, state="readonly")
        self.experiment_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(selector_frame, text="加载配置", command=self.load_experiment_config).pack(side=tk.LEFT, padx=5)
    
    def load_experiment_config(self):
        """加载所选实验的配置"""
        try:
            # 清除参数框架
            for widget in self.params_frame.winfo_children():
                widget.destroy()
            
            # 导入配置文件
            config_name = self.experiment_var.get()
            if config_name:
                # 动态导入配置模块
                self.exp_config = importlib.import_module(config_name)
                
                # 创建参数输入控件
                self.create_param_controls()
                
                messagebox.showinfo("成功", f"已加载{config_name}配置")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def create_param_controls(self):
        """创建参数输入控件"""
        if not self.exp_config:
            return
        
        # 创建参数网格
        param_grid = ttk.Frame(self.params_frame)
        param_grid.pack(fill=tk.BOTH, expand=True)
        
        # 获取配置文件中的参数
        param_vars = {}
        row = 0
        
        # 遍历配置文件中的变量
        for attr in dir(self.exp_config):
            if not attr.startswith('_') and attr not in ['os', 'np', 'localtime', 'strftime', 'ns', 'us', 'ms', 'Hz', 'kHz', 'MHz', 'GHz', 'AOM', 'uW', 'DAQ', 'STARTtrig', 'updateSequenceArgs', 'updateExpParamList']:
                try:
                    value = getattr(self.exp_config, attr)
                    # 只处理数值、字符串和布尔值
                    if isinstance(value, (int, float, str, bool)):
                        # 创建标签
                        ttk.Label(param_grid, text=f"{attr}:", width=20).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                        
                        # 创建输入控件
                        if isinstance(value, bool):
                            var = tk.BooleanVar(value=value)
                            ttk.Checkbutton(param_grid, variable=var).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                        elif isinstance(value, (int, float)):
                            var = tk.StringVar(value=str(value))
                            ttk.Entry(param_grid, textvariable=var, width=20).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                        else:
                            var = tk.StringVar(value=str(value))
                            ttk.Entry(param_grid, textvariable=var, width=50).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                        
                        param_vars[attr] = var
                        row += 1
                except:
                    pass
        
        # 保存参数变量
        self.exp_params = param_vars
        
        # 添加滚动条
        canvas = tk.Canvas(param_grid)
        scrollbar = ttk.Scrollbar(param_grid, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=row, column=0, columnspan=2, sticky="nsew")
        scrollbar.grid(row=row, column=2, sticky="ns")
        
        param_grid.grid_rowconfigure(row, weight=1)
        param_grid.grid_columnconfigure(1, weight=1)
    
    def create_save_settings(self):
        """创建保存设置控件"""
        ttk.Label(self.save_frame, text="保存路径：").pack(side=tk.LEFT, padx=5)
        
        self.save_path_var = tk.StringVar(value=self.save_path)
        ttk.Entry(self.save_frame, textvariable=self.save_path_var, width=50).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.save_frame, text="浏览", command=self.browse_save_path).pack(side=tk.LEFT, padx=5)
    
    def browse_save_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory(initialdir=self.save_path, title="选择保存路径")
        if path:
            self.save_path_var.set(path)
            self.save_path = path
    
    def create_run_controls(self):
        """创建运行控制控件"""
        ttk.Button(self.run_frame, text="运行实验", command=self.run_experiment, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(self.run_frame, text="停止实验", command=self.stop_experiment, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(self.run_frame, text="重置参数", command=self.reset_parameters, width=15).pack(side=tk.LEFT, padx=10)
    
    def create_result_display(self):
        """创建结果显示控件"""
        self.result_text = tk.Text(self.result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.result_text, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    def run_experiment(self):
        """运行实验"""
        try:
            if not self.exp_config:
                messagebox.showerror("错误", "请先加载实验配置")
                return
            
            # 更新配置参数
            self.update_config_parameters()
            
            # 确保保存路径存在
            os.makedirs(self.save_path, exist_ok=True)
            
            # 更新保存路径
            setattr(self.exp_config, 'savePath', self.save_path)
            
            # 运行实验
            self.result_text.insert(tk.END, "正在运行实验...\n")
            self.root.update()
            
            # 运行实验
            config_name = self.experiment_var.get()
            
            # 导入mainControl_MyDAQ模块
            import mainControl_MyDAQ
            
            # 重定向标准输出到GUI
            import io
            import contextlib
            
            # 创建一个字符串IO对象来捕获输出
            output = io.StringIO()
            
            # 重定向标准输出
            with contextlib.redirect_stdout(output):
                try:
                    success = mainControl_MyDAQ.run_experiment(config_name)
                    if success:
                        self.result_text.insert(tk.END, "实验运行成功！\n")
                    else:
                        self.result_text.insert(tk.END, "实验运行失败！\n")
                except Exception as e:
                    self.result_text.insert(tk.END, f"实验运行出错: {str(e)}\n")
            
            # 显示捕获的输出
            output_str = output.getvalue()
            if output_str:
                self.result_text.insert(tk.END, output_str)
            
            self.result_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("错误", f"运行实验失败: {str(e)}")
            self.result_text.insert(tk.END, f"错误: {str(e)}\n")
    
    def stop_experiment(self):
        """停止实验"""
        # 这里需要实现停止实验的逻辑
        # 暂时只是显示一个消息
        self.result_text.insert(tk.END, "实验已停止\n")
        self.result_text.see(tk.END)
    
    def reset_parameters(self):
        """重置参数"""
        self.load_experiment_config()
        self.result_text.insert(tk.END, "参数已重置\n")
        self.result_text.see(tk.END)
    
    def update_config_parameters(self):
        """更新配置参数"""
        if not self.exp_config or not self.exp_params:
            return
        
        for attr, var in self.exp_params.items():
            try:
                value = var.get()
                # 尝试转换类型
                if hasattr(self.exp_config, attr):
                    original_value = getattr(self.exp_config, attr)
                    if isinstance(original_value, bool):
                        new_value = value == '1' or value.lower() == 'true'
                    elif isinstance(original_value, int):
                        new_value = int(value)
                    elif isinstance(original_value, float):
                        new_value = float(value)
                    else:
                        new_value = value
                    
                    setattr(self.exp_config, attr, new_value)
            except Exception as e:
                print(f"更新参数 {attr} 失败: {str(e)}")

if __name__ == "__main__":
    # 设置中文字体
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    root = tk.Tk()
    app = NVExperimentGUI(root)
    root.mainloop()
