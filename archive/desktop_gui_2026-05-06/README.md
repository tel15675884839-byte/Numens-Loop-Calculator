# Loop Calculator (现代工业回路计算器)

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![Framework](https://img.shields.io/badge/framework-PySide6-green.svg)

Loop Calculator 是一款专为工业系统（如消防报警、安防控制）设计的专业回路负载计算工具。它能够精确模拟回路中的电压降、电流消耗，并根据电气标准推荐最优的电缆方案。

## 🚀 核心功能

- **精密电气计算**：实时计算回路的总静态电流 (Standby) 和报警电流 (Alarm)。
- **电压降模拟**：根据电缆长度、阻抗和设备负载，模拟回路末端电压，确保设备在安全电压范围内工作。
- **智能电缆推荐**：根据计算结果自动匹配最佳电缆截面积（1.0mm², 1.5mm², 2.5mm² 等）。
- **产品库管理**：内置可扩展的 JSON 设备数据库，支持从 Excel 一键导入和去重处理。
- **现代工业 UI**：基于现代工业审美设计的用户界面，支持实时诊断反馈。
- **自动化测试**：完善的测试用例确保计算结果的工业级精度。

## 🛠️ 技术栈

- **语言**: Python 3.9+
- **GUI 框架**: PySide6 (Qt for Python)
- **数据格式**: JSON, XLSX
- **测试工具**: Pytest

## 📦 快速开始

### 1. 安装依赖
确保已安装 Python，然后在项目根目录运行：
```bash
pip install -r requirements.txt
```

### 2. 运行程序
执行主程序脚本：
```bash
python LoopCalculatorApp.py
```
或者直接运行编译好的批处理文件：
- `启动程序.bat`

## 📂 项目结构

- `loop_calculator/`: 核心源代码
  - `calculator.py`: 纯逻辑计算引擎（Qt-free）
  - `main_window.py`: 主界面交互逻辑
  - `database.py`: 数据库访问层
- `assets/`: 界面图标及 LOGO 资源
- `tests/`: 自动化测试脚本
- `products_db.json`: 核心产品设备数据库
- `convert_xlsx.py`: 数据转换工具

## 🧪 运行测试

```bash
pytest tests/
```

## 📝 许可证

本项目遵循内部开发协议，仅限专业工程人员使用。
