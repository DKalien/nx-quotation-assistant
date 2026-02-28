# NXOpen 资源收集

Siemens NX/UG 自动化和模型参数提取的精选资源列表。

## GitHub 仓库

### 1. NXOpen Python 教程
- **URL**: https://github.com/Foadsf/NXOpen_Python_tutorials
- **描述**: 用于自动化 Siemens NX CAD/CAM/CAE 软件的 NXOpen Python 教程集合
- **特性**:
  - 基础 NX Python 设置指南
  - 消息框和列表窗口示例
  - 圆柱体特征创建示例
- **语言**: Python

### 2. NXOpen-CAE
- **URL**: https://github.com/theScriptingEngineer/NXOpen-CAE
- **描述**: 用于 Siemens SimCenter 3D (NX CAE) 的 NXOpen C# 代码
- **特性**:
  - 结构分析自动化
  - 后处理脚本
- **语言**: C#

### 3. NXOpen-CAE-python
- **URL**: https://github.com/theScriptingEngineer/NXOpen-CAE-python
- **描述**: NXOpen-CAE 脚本的 Python 版本
- **特性**:
  - 打印装配结构
  - 后处理自动化
- **语言**: Python

### 4. nxopentse Python 包
- **URL**: https://github.com/theScriptingEngineer/nxopentse
- **安装**: `pip install nxopentse`
- **特性**:
  - 可复用的 NXOpen 函数
  - CAD 和 CAE 功能
  - 代码补全支持

### 5. NX 批处理
- **URL**: https://github.com/MohanDulam/NX-Batch-Processing
- **描述**: 无需打开 NX 即可导出中性 CAD 文件
- **特性**:
  - 批量文件导出
  - 支持多种格式
- **语言**: C# WinForms

### 6. NX 技巧与窍门
- **URL**: https://github.com/Foadsf/NXtips
- **描述**: NX 使用技巧和 NXOpen Python 教程

## GitHub 主题

- [NXOpen](https://github.com/topics/nxopen) - 所有 NXOpen 相关项目
- [Siemens NX](https://github.com/topics/siemens-nx) - 所有 Siemens NX 相关项目

## NX 日志网站

网站: https://www.nxjournaling.com

### 参数提取的有用脚本

| 脚本 | URL | 描述 |
|------|-----|------|
| 获取所有惯性属性 | /content/get-all-inerita-properties-part-file | 获取所有实体的质量属性 |
| 读取属性 | /content/reading-attributes | 读取所有零件属性 |
| 提取对象属性 | /content/extracting-object-attributes | 将属性提取到表格 |
| 简易材料重量管理 | /content/easy-material-weight-management-part-1 | 材料重量计算 |
| 从图纸提取对象属性 | /content/extract-object-attributes-drawing-notes | 从图纸提取属性 |

## 官方文档

- NXOpen Python 参考指南 (NX 10+)
- NXOpen 入门指南
- NXOpen 程序员指南
- Siemens 社区论坛

## 支持的编程语言

| 语言 | 用途 |
|------|------|
| Python | 快速开发、脚本编写 |
| C# | Windows 桌面应用程序 |
| C++ | 高性能需求 |
| VB.NET | 传统选择 |
| Java | 跨平台需求 |

## 关键 NXOpen API 类

- `NXOpen.Session` - 主会话对象
- `NXOpen.Part` - 零件文件操作
- `NXOpen.Body` - 实体操作
- `NXOpen.MeasureManager` - 测量功能
- `NXOpen.UF.UFSession` - 底层 UF 函数

## 可用参数类型

| 类别 | 参数 | API 方法 |
|------|------|----------|
| 质量属性 | 质量、体积、质心、转动惯量 | `MeasureManager.NewMassProperties()` |
| 几何属性 | 边界框、表面积、边数 | `Body.GetBoundingBox()` |
| 零件属性 | 用户定义属性 | `GetUserAttributes()` |
| 材料 | 密度、材料名称 | `Material` 对象 |
| 特征 | 特征类型、参数 | `Feature` 对象 |
| 装配 | 组件层次结构 | `Part.Assembly()` |

## 社区资源

- [NX Journaling 论坛](https://nxjournaling.com) - 社区问答
- [Siemens 社区](https://community.sw.siemens.com) - 官方支持
