# NX 报价助手

一个基于 Python 的工具，用于从 Siemens NX/UG 提取 3D 模型参数，辅助报价准备工作。

## 功能特性

- 提取质量属性（质量、体积、质心、转动惯量）
- 提取几何属性（边界框、表面积）
- 提取零件属性和材料信息
- 导出数据到 Excel/CSV 用于报价文档
- 支持多零件批量处理

## 项目结构

```
nx-quotation-assistant/
├── archive/                        # 归档代码（C++ 项目等）
├── docs/                           # 文档和资源
├── scripts/                        # 可运行脚本
├── src/                            # 核心源代码
├── tests/                          # 测试文件
├── .gitignore
├── README.md
└── requirements.txt
```

## 环境要求

- Siemens NX（版本 10+）
- Python 3.8+
- NXOpen Python API

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 提取零件质量和表面积

在 NX 环境中运行：

```bash
# 在 NX 的 Developer 选项卡中运行
python scripts/extract_mass_properties.py
```

程序会自动提取指定零件的：
- 体积和表面积
- 质量（基于固定密度 7.85 g/cm³）
- 边界框尺寸
- 单位信息

**注意**: 需要在 Siemens NX 环境中运行，因为使用 NXOpen API 获取精确数据。

## 目录说明

- **src/** - 核心源代码模块
  - `extractor.py` - 模型参数提取器
  - `exporter.py` - 数据导出器（支持 CSV、Excel、JSON）
  
- **scripts/** - 可直接运行的脚本
  - `extract_mass_properties.py` - 主脚本，提取质量和表面积
  - `examples.py` - 示例代码集合
  
- **docs/** - 项目文档
  - `nxopen-api-guide.md` - NXOpen API 快速参考
  - `resources.md` - 学习资源列表
  
- **tests/** - 测试文件
  - 包含测试用的 .prt 零件文件
  
- **archive/** - 归档代码
  - `Dll1/` - C++ 版本项目（Visual Studio）
  - `extract_mass_properties_cpp.cpp` - C++ 源代码

### 详细文档

- **完整使用指南**: [EXTRACTION_TOOL_GUIDE.md](EXTRACTION_TOOL_GUIDE.md)

## 资源

详见 [docs/resources.md](docs/resources.md) 获取收集的资源和参考资料。

## 最近更新

### 2026-02-28 - 项目结构整理

- **改进**: 重新组织项目结构，提高可维护性
  - ✅ 删除备份文件和临时文件
  - ✅ 移动主脚本到 `scripts/` 目录
  - ✅ 归档 C++ 项目到 `archive/` 目录
  - ✅ 创建 `tests/` 目录存放测试文件
  - ✅ 更新文档说明新的目录结构
- **详情**: 查看 [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

### 2026-02-28 - v1.4 正式版 - 修复关键 API 错误

- **问题**: 3 个关键 API 使用错误导致数据提取失败
  - `MeasureManager()` 调用错误 - 应该是属性而不是方法
  - `Body.GetBoundingBox()` 方法不存在
  - `CloseModified.No` 枚举值不兼容
- **修复**: 
  - ✅ 修正 MeasureManager 为属性访问
  - ✅ 使用 UF API 获取边界框
  - ✅ 使用枚举数值提高兼容性
- **状态**: ✅ 所有错误已修复，请在 NX 中验证
- **详情**: 查看 [FINAL_FIX_REPORT.md](FINAL_FIX_REPORT.md)

### 2026-02-28 - 修复 NXOpen API 兼容性问题

- **问题**: 多个 NXOpen API 调用在不同版本中不兼容
- **修复**: 使用 Python 原生迭代方式，修复枚举值和常量
- **详情**: 查看 [API_COMPATIBILITY_FIX.md](API_COMPATIBILITY_FIX.md)

### 2026-02-28 - 修复质量属性提取问题

- **问题**: 提取到的体积和表面积均为 0
- **原因**: `NewMassProperties` API 调用参数错误
- **修复**: 更正 API 调用方式
- **详情**: 查看 [BUGFIX_REPORT.md](BUGFIX_REPORT.md)

## 许可证

MIT License
