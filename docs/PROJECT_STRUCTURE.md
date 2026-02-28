# 项目结构说明

本文档详细描述了 NX 报价助手项目的文件组织结构。

## 目录结构

```
nx-quotation-assistant/
├── archive/                        # 归档代码（历史版本、参考实现）
├── docs/                           # 项目文档
├── scripts/                        # 可直接运行的脚本
├── src/                            # 核心源代码模块
├── tests/                          # 测试文件
├── .gitignore                      # Git 忽略配置
├── README.md                       # 项目主文档
└── requirements.txt                # Python 依赖项
```

## 详细说明

### 📁 archive/ - 归档代码

存放历史版本、参考实现或暂时不使用的代码。

**内容：**
- `Dll1/` - C++ 版本的 NX Open 项目
  - 包含完整的 Visual Studio 项目文件
  - 可用于学习 C++ 版本的 NX Open API 用法
  - 编译说明见 `Dll1/README_编译说明.txt`
- `extract_mass_properties_cpp.cpp` - C++ 版主程序源代码

**用途：**
- 保留历史代码实现
- 作为 C++ 开发的参考
- 不主动维护，仅供参考

### 📁 docs/ - 项目文档

存放项目相关文档和学习资源。

**文件：**
- `nxopen-api-guide.md` - NXOpen API 快速参考指南
  - 常用 API 示例代码
  - 质量属性提取方法
  - 零件属性操作
  - 数据导出示例
- `resources.md` - 学习资源收集
  - GitHub 仓库推荐
  - 官方文档链接
  - 社区资源
  - 教程网站

### 📁 scripts/ - 可运行脚本

包含可直接在 NX 环境中运行的 Python 脚本。

**文件：**
- `extract_mass_properties.py` - **主脚本**
  - 提取零件质量和表面积
  - 自动检测单位系统
  - 批量处理多个零件
  - 输出结果到文件
  - 密度设置：7.85 g/cm³
  
- `examples.py` - 示例代码集合
  - 基础 API 使用示例
  - 质量属性提取示例
  - 边界框提取示例
  - 属性读取示例
  - 数据导出示例

**使用方法：**
```python
# 在 NX Developer 选项卡中运行
python scripts/extract_mass_properties.py
```

### 📁 src/ - 核心源代码

包含可复用的 Python 模块，提供核心功能。

**文件：**
- `__init__.py` - 包初始化文件
- `extractor.py` - 模型参数提取器
  - `ModelExtractor` 类
  - 质量属性提取
  - 边界框计算
  - 零件属性读取
  - 统一提取接口
  
- `exporter.py` - 数据导出器
  - `DataExporter` 类
  - 支持 CSV 格式导出
  - 支持 Excel 格式导出（需要 openpyxl）
  - 支持 JSON 格式导出
  - 格式化报价报告生成

**使用示例：**
```python
from src.extractor import ModelExtractor
from src.exporter import DataExporter

# 创建提取器
extractor = ModelExtractor()
extractor.connect()

# 提取数据
data = extractor.extract_all()

# 导出数据
exporter = DataExporter(output_dir='./output')
exporter.to_excel(data, 'report.xlsx')
```

### 📁 tests/ - 测试文件

存放测试用的零件文件。

**内容：**
- `m.prt` - 测试零件（米制单位）
- `mm.prt` - 测试零件（毫米制单位）

**用途：**
- 脚本功能验证
- 单位检测测试
- 回归测试

### 📄 根目录文件

- `.gitignore` - Git 忽略配置
  - Python 缓存文件
  - 虚拟环境目录
  - 输出文件目录
  - IDE 配置文件
  
- `README.md` - 项目主文档
  - 项目介绍
  - 安装说明
  - 使用指南
  - 目录结构
  - 更新日志
  
- `requirements.txt` - Python 依赖项
  - pandas - 数据处理
  - numpy - 数值计算
  - openpyxl - Excel 文件操作
  - click - 命令行界面
  - pyyaml - 配置文件解析

## 文件组织原则

### ✅ 当前结构优点

1. **清晰的职责分离**
   - `src/` - 可复用模块
   - `scripts/` - 直接运行的脚本
   - `tests/` - 测试资源
   - `docs/` - 文档

2. **易于导航**
   - 按功能分类
   - 命名清晰
   - 层次简单

3. **便于维护**
   - 相关代码组织在一起
   - 归档代码不干扰主项目
   - 测试资源独立

### 📋 开发建议

**添加新功能时：**
1. 核心功能 → `src/`
2. 独立脚本 → `scripts/`
3. 测试文件 → `tests/`
4. 相关文档 → `docs/`

**代码组织：**
- 模块化设计
- 单一职责原则
- 清晰的文档字符串
- 遵循现有代码风格

## 版本历史

### v2.0 - 项目结构重构 (2026-02-28)

**变更：**
- 删除备份文件 `extract_mass_properties_backup.py`
- 删除临时输出文件 `mass_properties_output.txt`
- 移动主脚本到 `scripts/` 目录
- 归档 C++ 项目到 `archive/` 目录
- 创建 `tests/` 目录
- 更新文档结构

**理由：**
- 提高项目可维护性
- 清晰的目录结构
- 分离核心代码和可运行脚本
- 保留历史代码作为参考

### v1.0 - 初始版本

- 基础 Python 脚本
- 简单的质量属性提取
- 基础文档

## 相关资源

- [NXOpen API 指南](docs/nxopen-api-guide.md)
- [学习资源](docs/resources.md)
- [C++ 版本编译说明](archive/Dll1/README_编译说明.txt)
