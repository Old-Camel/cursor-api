#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

# 检查 Python 版本
if sys.version_info[0] < 3:
    print("错误: 此脚本需要 Python 3")
    sys.exit(1)

import json
import os
from pathlib import Path
import argparse
import hashlib
import uuid
import random
import string
import subprocess

def get_config_path():
    """根据不同操作系统返回配置文件路径"""
    if sys.platform == "darwin":  # macOS
        base_path = Path("~/Library/Application Support/Cursor/User/globalStorage")
    elif sys.platform == "win32":  # Windows
        base_path = Path(os.environ.get("APPDATA", "")) / "Cursor/User/globalStorage"
    else:  # Linux 和其他类Unix系统
        base_path = Path("~/.config/Cursor/User/globalStorage")
    
    return Path(os.path.expanduser(str(base_path))) / "storage.json"

CONFIG_PATH = get_config_path()

def is_cursor_running():
    """检查 Cursor 是否正在运行（不依赖第三方库）"""
    try:
        if sys.platform == "win32":
            # Windows
            output = subprocess.check_output('tasklist', shell=True).decode()
            return 'cursor' in output.lower()
        else:
            # Unix-like systems (Linux, macOS)
            output = subprocess.check_output(['ps', 'aux']).decode()
            return 'cursor' in output.lower()
    except:
        return False  # 如果出错，假设进程未运行

def check_cursor_process(func):
    """装饰器：检查 Cursor 进程"""
    def wrapper(*args, **kwargs):
        if is_cursor_running():
            print("警告: 检测到 Cursor 正在运行！")
            print("请先关闭 Cursor 再执行操作，否则修改可能会被覆盖。")
            choice = input("是否继续？(y/N): ")
            if choice.lower() != 'y':
                return
        return func(*args, **kwargs)
    return wrapper

def show_config():
    """显示当前配置文件的内容"""
    try:
        if not CONFIG_PATH.exists():
            print(f"配置文件不存在: {CONFIG_PATH}")
            return
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}")

def get_value(key):
    """获取指定键的值"""
    try:
        if not CONFIG_PATH.exists():
            print(f"配置文件不存在: {CONFIG_PATH}")
            return
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            value = data.get(key)
            if value is None:
                print(f"未找到键: {key}")
            else:
                print(json.dumps(value, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}")

def get_machine_ids():
    """获取配置信息"""
    try:
        if not CONFIG_PATH.exists():
            print(f"配置文件不存在: {CONFIG_PATH}")
            return
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            mac_id = data.get("telemetry.macMachineId", "未设置")
            machine_id = data.get("telemetry.machineId", "未设置")
            print(f"Mac配置: {mac_id}")
            print(f"Windows配置: {machine_id}")
    except Exception as e:
        print(f"读取配置文件时出错: {str(e)}")

@check_cursor_process
def set_value(key, value):
    """设置指定键的值"""
    try:
        data = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # 尝试将输入的值转换为 JSON
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            # 如果不是有效的 JSON，就按字符串处理
            pass
        
        data[key] = value
        
        # 确保目录存在
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"已设置 {key} = {value}")
    except Exception as e:
        print(f"设置值时出错: {str(e)}")

@check_cursor_process
def reset_machine_ids():
    """重置配置信息"""
    try:
        if not CONFIG_PATH.exists():
            print(f"配置文件不存在: {CONFIG_PATH}")
            return
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 删除配置ID
        data.pop("telemetry.macMachineId", None)
        data.pop("telemetry.machineId", None)
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("已成功重置配置信息")
    except Exception as e:
        print(f"重置配置信息时出错: {str(e)}")

@check_cursor_process
def generate_random_machine_ids():
    """生成随机配置"""
    try:
        if not CONFIG_PATH.exists():
            print(f"配置文件不存在: {CONFIG_PATH}")
            return
        
        # 生成随机字符串并计算其哈希值
        def generate_random_hash():
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            random_str += str(uuid.uuid4())  # 添加 UUID 增加随机性
            return hashlib.sha256(random_str.encode()).hexdigest()
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 生成新的配置
        data["telemetry.macMachineId"] = generate_random_hash()
        data["telemetry.machineId"] = generate_random_hash()
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("已生成新的配置：")
        print(f"Mac配置: {data['telemetry.macMachineId']}")
        print(f"Windows配置: {data['telemetry.machineId']}")
    except Exception as e:
        print(f"生成配置时出错: {str(e)}")

def kill_cursor_processes():
    """终止所有 Cursor 相关进程"""
    try:
        if sys.platform == "win32":
            # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'Cursor.exe'], check=False)
        else:
            # Unix-like systems (Linux, macOS)
            try:
                # 先尝试正常终止
                subprocess.run(['pkill', 'Cursor'], check=False)
                # 等待一小段时间
                time.sleep(1)
                # 如果还有进程存在，强制终止
                subprocess.run(['pkill', '-9', 'Cursor'], check=False)
            except Exception as e:
                print(f"终止进程时出错: {str(e)}")
        
        print("已尝试终止所有 Cursor 进程")
    except Exception as e:
        print(f"终止进程时出错: {str(e)}")

def show_menu():
    """显示交互菜单"""
    print("\n=== Cursor 配置管理工具 ===")
    print("1. 显示当前配置")
    print("2. 获取指定键的值")
    print("3. 设置指定键的值")
    print("4. 显示配置信息")
    print("5. 重置配置")
    print("6. 生成随机配置")
    print("7. 终止所有Cursor进程")
    print("0. 退出程序")
    print("========================")
    return input("请选择操作 (0-7): ")

def main():
    while True:
        choice = show_menu()
        
        try:
            if choice == '0':
                print("感谢使用，再见！")
                break
            elif choice == '1':
                show_config()
            elif choice == '2':
                key = input("请输入要查询的键名: ")
                get_value(key)
            elif choice == '3':
                key = input("请输入键名: ")
                value = input("请输入值: ")
                set_value(key, value)
            elif choice == '4':
                get_machine_ids()
            elif choice == '5':
                reset_machine_ids()
            elif choice == '6':
                generate_random_machine_ids()
            elif choice == '7':
                kill_cursor_processes()
            else:
                print("无效的选择，请重试")
            
            input("\n按回车键继续...")
            
        except Exception as e:
            print(f"操作出错: {str(e)}")
            input("\n按回车键继续...")

if __name__ == '__main__':
    main()