# NXOpen API 快速参考

## 入门

### 基础设置
```python
import NXOpen

def main():
    # 获取当前会话
    session = NXOpen.Session.GetSession()

    # 获取工作零件
    work_part = session.Parts.Work

    # 你的代码在这里

if __name__ == '__main__':
    main()
```

### 显示消息
```python
import NXOpen

def show_message():
    session = NXOpen.Session.GetSession()
    lw = session.ListingWindow

    lw.Open()
    lw.WriteFullline("你好 NX!")
    lw.Close()
```

## 质量属性提取

### 获取实体的质量属性
```python
import NXOpen

def get_mass_properties():
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work
    measure_manager = work_part.MeasureManager()

    # 获取零件中的所有实体
    bodies = work_part.Bodies.ToArray()

    if len(bodies) > 0:
        # 创建质量属性对象
        mass_props = measure_manager.NewMassProperties(bodies)

        # 提取属性
        mass = mass_props.Mass
        volume = mass_props.Volume
        center = mass_props.CenterOfMass

        print(f"质量: {mass}")
        print(f"体积: {volume}")
        print(f"质心: {center}")

        return {
            'mass': mass,
            'volume': volume,
            'center_of_mass': center
        }

    return None
```

## 零件属性

### 读取所有零件属性
```python
import NXOpen

def get_part_attributes():
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    attributes = {}

    # 获取所有用户属性
    user_attrs = work_part.GetUserAttributes()

    for attr in user_attrs:
        attributes[attr.Title] = attr.StringValue

    return attributes
```

### 设置零件属性
```python
import NXOpen

def set_attribute(name, value):
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    work_part.SetAttribute(name, value)
```

## 几何信息

### 获取边界框
```python
import NXOpen

def get_bounding_box():
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    bodies = work_part.Bodies.ToArray()

    if len(bodies) > 0:
        # 获取第一个实体的边界框
        bbox = bodies[0].GetBoundingBox()

        # bbox 包含: 最小角点, 最大角点
        min_point = bbox[0]  # (x_min, y_min, z_min)
        max_point = bbox[1]  # (x_max, y_max, z_max)

        # 计算尺寸
        length = max_point[0] - min_point[0]
        width = max_point[1] - min_point[1]
        height = max_point[2] - min_point[2]

        return {
            'length': length,
            'width': width,
            'height': height,
            'volume_bbox': length * width * height
        }

    return None
```

## 装配结构

### 打印装配树
```python
import NXOpen

def print_assembly_structure(part=None, level=0):
    session = NXOpen.Session.GetSession()

    if part is None:
        part = session.Parts.Work

    indent = "  " * level
    print(f"{indent}{part.Leaf}")

    # 检查是否为装配
    if part.ComponentAssembly is not None:
        root_component = part.ComponentAssembly.RootComponent

        if root_component is not None:
            for child in root_component.GetChildren():
                # 获取子零件
                child_part = child.Prototype.OwningPart
                print_assembly_structure(child_part, level + 1)
```

## 导出到 Excel

### 使用 openpyxl
```python
import NXOpen
from openpyxl import Workbook

def export_to_excel(output_path):
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    # 获取质量属性
    bodies = work_part.Bodies.ToArray()
    mass_props = work_part.MeasureManager().NewMassProperties(bodies)

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "模型参数"

    # 表头
    ws['A1'] = '零件名称'
    ws['B1'] = '质量 (kg)'
    ws['C1'] = '体积 (mm^3)'
    ws['D1'] = '材料'

    # 数据
    ws['A2'] = work_part.Leaf
    ws['B2'] = mass_props.Mass
    ws['C2'] = mass_props.Volume

    # 保存
    wb.save(output_path)
```

## 有用的 NXOpen 类参考

| 类 | 用途 |
|-------|------|
| `NXOpen.Session` | 主会话，访问所有 NX 功能 |
| `NXOpen.Part` | 零件文件操作 |
| `NXOpen.Body` | 实体对象 |
| `NXOpen.Face` | 面对象 |
| `NXOpen.Edge` | 边对象 |
| `NXOpen.Feature` | 特征对象 |
| `NXOpen.MeasureManager` | 测量功能 |
| `NXOpen.Component` | 装配组件 |
| `NXOpen.UF.UFSession` | 底层 UF API 访问 |

## 常用操作

### 遍历所有实体
```python
for body in work_part.Bodies.ToArray():
    print(f"实体: {body.Tag}")
    # 处理每个实体
```

### 遍历所有特征
```python
for feature in work_part.Features.GetFeatures():
    print(f"特征: {feature.FeatureType}")
    # 处理每个特征
```

### 获取材料信息
```python
material = work_part.Material
if material:
    print(f"材料: {material.Name}")
    print(f"密度: {material.Density}")
```

## 技巧

1. 访问对象前始终检查对象是否存在
2. 使用 try-except 进行错误处理
3. 从 NX Developer 选项卡运行脚本
4. 录制宏以学习 API 用法
5. 使用 NXOpen 参考文档获取详细 API 信息
