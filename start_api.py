#!/usr/bin/env python3
"""
Chorus API 启动脚本
简化API服务的启动过程
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import fastapi
        import uvicorn
        import pychorus
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_api():
    """启动API服务"""
    print("🚀 启动 Chorus API 服务...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 检查必要目录
    required_dirs = ['uploads', 'outputs', 'temp']
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 确保目录存在: {dir_name}")
    
    print("\n🌐 API服务将在以下地址运行:")
    print("   - 主页: http://localhost:8000")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc文档: http://localhost:8000/redoc")
    print("\n💡 提示: 按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        # 启动服务
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

def open_browser():
    """打开浏览器"""
    try:
        time.sleep(2)  # 等待服务启动
        webbrowser.open("http://localhost:8000")
        print("🌐 已自动打开浏览器")
    except:
        print("💡 请手动打开浏览器访问: http://localhost:8000")

if __name__ == "__main__":
    print("🎵 Chorus API 启动器")
    print("=" * 50)
    
    # 检查是否在正确的目录
    if not Path("main.py").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        print("   确保 main.py 文件存在")
        sys.exit(1)
    
    # 启动API服务
    if start_api():
        print("✅ 服务启动成功!")
    else:
        print("❌ 服务启动失败")
        sys.exit(1)


