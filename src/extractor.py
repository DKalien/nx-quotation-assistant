"""
模型参数提取器

用于从 NX 模型中提取报价所需的参数。
"""

class ModelExtractor:
    """
    从 Siemens NX 中提取模型参数。

    此类提供了从 NX 模型中提取各种参数的方法，
    包括质量属性、尺寸和自定义属性。
    """

    def __init__(self, session=None):
        """
        初始化提取器。

        参数:
            session: NXOpen 会话对象。如果为 None，将自动获取。
        """
        self.session = session
        self.work_part = None

    def connect(self):
        """连接到 NX 会话"""
        try:
            import NXOpen
            if self.session is None:
                self.session = NXOpen.Session.GetSession()
            self.work_part = self.session.Parts.Work
            return True
        except Exception as e:
            print(f"连接 NX 时出错: {e}")
            return False

    def get_mass_properties(self):
        """
        获取零件中所有实体的质量属性。

        返回:
            dict: 包含质量、体积、表面积等的字典。
        """
        if self.work_part is None:
            return None

        bodies = self.work_part.Bodies.ToArray()
        if len(bodies) == 0:
            return None

        measure_mgr = self.work_part.MeasureManager()
        mass_props = measure_mgr.NewMassProperties(bodies)

        return {
            'mass': mass_props.Mass,
            'volume': mass_props.Volume,
            'surface_area': mass_props.SurfaceArea,
            'center_of_mass': mass_props.CenterOfMass,
            'body_count': len(bodies)
        }

    def get_bounding_box(self):
        """
        获取所有实体的边界框尺寸。

        返回:
            dict: 包含长度、宽度、高度的字典
        """
        if self.work_part is None:
            return None

        bodies = self.work_part.Bodies.ToArray()
        if len(bodies) == 0:
            return None

        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        for body in bodies:
            bbox = body.GetBoundingBox()
            min_pt, max_pt = bbox[0], bbox[1]

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

    def get_attributes(self):
        """
        获取所有零件属性。

        返回:
            dict: 属性名称和值的字典
        """
        if self.work_part is None:
            return {}

        attributes = {}

        # 用户属性
        user_attrs = self.work_part.GetUserAttributes()
        for attr in user_attrs:
            attributes[attr.Title] = attr.StringValue

        # 系统属性
        attributes['_part_name'] = self.work_part.Leaf

        return attributes

    def extract_all(self):
        """
        提取所有可用参数。

        返回:
            dict: 所有参数的组合字典
        """
        mass = self.get_mass_properties() or {}
        bbox = self.get_bounding_box() or {}
        attrs = self.get_attributes() or {}

        return {
            'part_name': self.work_part.Leaf if self.work_part else '',
            **mass,
            **bbox,
            **attrs
        }
