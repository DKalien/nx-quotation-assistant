"""
NX 报价助手 - 示例脚本

此模块包含用于从 NX 中提取模型参数的示例脚本。
"""

# 示例 1: 提取质量属性
# 在 NX Developer 选项卡中运行此脚本

import NXOpen

def extract_mass_properties():
    """从当前零件中提取质量属性"""
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work
    lw = session.ListingWindow

    if work_part is None:
        print("没有加载零件！")
        return None

    bodies = work_part.Bodies.ToArray()

    if len(bodies) == 0:
        print("零件中没有找到实体！")
        return None

    measure_mgr = work_part.MeasureManager()
    mass_props = measure_mgr.NewMassProperties(bodies)

    # 获取属性
    result = {
        'part_name': work_part.Leaf,
        'body_count': len(bodies),
        'mass': mass_props.Mass,
        'volume': mass_props.Volume,
        'surface_area': mass_props.SurfaceArea,
        'center_of_mass': mass_props.CenterOfMass
    }

    # 打印结果
    lw.Open()
    lw.WriteFullline(f"零件: {result['part_name']}")
    lw.WriteFullline(f"实体数: {result['body_count']}")
    lw.WriteFullline(f"质量: {result['mass']:.4f} kg")
    lw.WriteFullline(f"体积: {result['volume']:.4f} mm^3")
    lw.WriteFullline(f"表面积: {result['surface_area']:.4f} mm^2")
    lw.Close()

    return result


# 示例 2: 提取边界框

def extract_bounding_box():
    """提取边界框尺寸"""
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    if work_part is None:
        return None

    bodies = work_part.Bodies.ToArray()

    if len(bodies) == 0:
        return None

    # 获取组合边界框
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

    for body in bodies:
        bbox = body.GetBoundingBox()
        min_pt = bbox[0]
        max_pt = bbox[1]

        min_x = min(min_x, min_pt[0])
        min_y = min(min_y, min_pt[1])
        min_z = min(min_z, min_pt[2])
        max_x = max(max_x, max_pt[0])
        max_y = max(max_y, max_pt[1])
        max_z = max(max_z, max_pt[2])

    return {
        'length': max_x - min_x,
        'width': max_y - min_y,
        'height': max_z - min_z,
        'min_point': (min_x, min_y, min_z),
        'max_point': (max_x, max_y, max_z)
    }


# 示例 3: 提取零件属性

def extract_attributes():
    """提取所有零件属性"""
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    if work_part is None:
        return {}

    attributes = {}

    # 获取用户属性
    user_attrs = work_part.GetUserAttributes()
    for attr in user_attrs:
        attributes[attr.Title] = attr.StringValue

    # 获取系统属性
    try:
        attributes['PART_NAME'] = work_part.Leaf
        attributes['PART_NUMBER'] = work_part.PartNumber if hasattr(work_part, 'PartNumber') else ''
        attributes['DESCRIPTION'] = work_part.Description if hasattr(work_part, 'Description') else ''
    except:
        pass

    return attributes


# 示例 4: 导出到 CSV（独立运行 - 不在 NX 中运行）

import csv

def export_to_csv(data, filepath):
    """将提取的数据导出到 CSV 文件"""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # 写入表头
        writer.writerow(['零件名称', '质量 (kg)', '体积 (mm^3)',
                        '长度 (mm)', '宽度 (mm)', '高度 (mm)'])

        # 写入数据
        for item in data:
            writer.writerow([
                item.get('part_name', ''),
                item.get('mass', 0),
                item.get('volume', 0),
                item.get('length', 0),
                item.get('width', 0),
                item.get('height', 0)
            ])

    print(f"数据已导出到 {filepath}")


# 用于 NX 执行的主函数

def main():
    """NX 日志的主入口点"""
    mass_data = extract_mass_properties()
    bbox_data = extract_bounding_box()
    attr_data = extract_attributes()

    if mass_data and bbox_data:
        print("\n=== 报价数据摘要 ===")
        print(f"零件: {mass_data['part_name']}")
        print(f"质量: {mass_data['mass']:.4f} kg")
        print(f"体积: {mass_data['volume']:.4f} mm^3")
        print(f"尺寸: {bbox_data['length']:.2f} x {bbox_data['width']:.2f} x {bbox_data['height']:.2f} mm")
        print("=" * 30)


if __name__ == '__main__':
    main()
