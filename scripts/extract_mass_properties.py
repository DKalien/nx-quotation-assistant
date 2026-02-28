# NXOpen Python Script - 提取零件质量和表面积
# 在 NX 中通过 Developer -> Play 运行此脚本
# 密度设置: 7.85 g/cm³ = 7850 kg/m³
# 版本 v4.11：精简版 + 基于Convert方法的最终单位检测 + 优化输出 + 删除冗余信息

import NXOpen
import NXOpen.UF
import os

def get_all_bodies(part, uf_session):
    """使用 UF API 获取所有实体"""
    bodies = []
    tag = 0
    while True:
        tag = uf_session.Obj.CycleObjsInPart(part.Tag, NXOpen.UF.UFConstants.UF_solid_type, tag)
        if tag == 0:
            break
        obj_type, obj_subtype = uf_session.Obj.AskTypeAndSubtype(tag)
        if obj_subtype == NXOpen.UF.UFConstants.UF_solid_body_subtype:
            body = NXOpen.TaggedObjectManager.GetTaggedObject(tag)
            bodies.append(body)
    return bodies

def get_display_unit_info(work_part):
    """
    获取显示单位信息
    返回: (单位名称, 体积转换系数, 面积转换系数)
    """
    lw = NXOpen.Session.GetSession().ListingWindow
    uc = work_part.UnitCollection
    
    # 获取基础单位对象
    length_unit = uc.GetBase("长度")
    area_unit = uc.GetBase("面积")
    volume_unit = uc.GetBase("体积")
    
    # 获取单位标识符
    length_journal_id = length_unit.JournalIdentifier
    area_journal_id = area_unit.JournalIdentifier
    volume_journal_id = volume_unit.JournalIdentifier
    
    lw.WriteLine(f"      长度单位标识: {length_journal_id}")
    lw.WriteLine(f"      面积单位标识: {area_journal_id}")
    lw.WriteLine(f"      体积单位标识: {volume_journal_id}")
    
    # 根据标识符判断单位和转换系数
    if "MilliMeter" in length_journal_id:
        unit_name = "毫米"
        length_factor = 0.001      # mm -> m
        area_factor = 1e-6         # mm² -> m²
        volume_factor = 1e-9       # mm³ -> m³
    elif "Meter" in length_journal_id:
        unit_name = "米"
        length_factor = 1.0        # m -> m
        area_factor = 1.0          # m² -> m²
        volume_factor = 1.0        # m³ -> m³
    elif "Inch" in length_journal_id:
        unit_name = "英寸"
        length_factor = 0.0254     # inch -> m
        area_factor = 6.4516e-4    # inch² -> m²
        volume_factor = 1.6387e-5  # inch³ -> m³
    else:
        unit_name = "未知"
        length_factor = 0.001      # 默认假设毫米
        area_factor = 1e-6
        volume_factor = 1e-9
    
    lw.WriteLine(f"      检测到的显示单位: {unit_name}")
    return unit_name, volume_factor, area_factor

def detect_display_unit_with_convert(work_part):
    """
    使用Convert方法检测显示单位
    返回: (单位名称, 转换系数, 检测方法)
    """
    try:
        uc = work_part.UnitCollection
        
        # 获取单位对象
        mm_unit = uc.FindObject("MilliMeter")
        m_unit = uc.FindObject("Meter")
        inch_unit = uc.FindObject("Inch")
        
        # 测试毫米转米
        result_mm_to_m = uc.Convert(mm_unit, m_unit, 1.0)
        
        # 根据转换系数判断显示单位
        if abs(result_mm_to_m - 0.001) < 0.0001:  # 1毫米 = 0.001米
            return "毫米", result_mm_to_m, "Convert方法"
        elif abs(result_mm_to_m - 1000.0) < 1.0:  # 1米 = 1000毫米
            return "米", result_mm_to_m, "Convert方法"
        else:
            # 测试英寸转毫米
            result_inch_to_mm = uc.Convert(inch_unit, mm_unit, 1.0)
            if 25.0 < result_inch_to_mm < 26.0:  # 1英寸 ≈ 25.4毫米
                return "英寸", result_inch_to_mm, "Convert方法"
            else:
                return "未知", result_mm_to_m, "Convert方法"
    except Exception as e:
        return "错误", str(e), "Convert方法"

def collect_detailed_unit_info(work_part):
    """
    收集详细的单位信息用于对比分析
    返回: 包含单位详细信息的字典
    """
    lw = NXOpen.Session.GetSession().ListingWindow
    uc = work_part.UnitCollection
    
    unit_info = {
        "part_name": work_part.FullPath,
        "part_units_info": {},
        "display_units_info": {},
        "unit_objects_info": {}
    }
    
    # 1. 获取 PartUnits 信息
    try:
        # PartUnits 是一个枚举类型
        part_units_value = work_part.PartUnits
        unit_info["part_units_info"]["value"] = str(part_units_value)
        unit_info["part_units_info"]["enum_name"] = str(part_units_value)
        
        # 尝试获取枚举成员
        try:
            if hasattr(part_units_value, 'name'):
                unit_info["part_units_info"]["name"] = part_units_value.name
        except:
            pass
            
    except Exception as e:
        unit_info["part_units_info"]["error"] = str(e)
    
    # 2. 获取显示单位信息 (GetBase)
    try:
        # 获取各种度量类型的基础单位
        measure_types = ["长度", "面积", "体积", "质量", "角度", "时间"]
        for measure_type in measure_types:
            try:
                unit_obj = uc.GetBase(measure_type)
                unit_info["display_units_info"][measure_type] = {
                    "journal_identifier": unit_obj.JournalIdentifier,
                    "name": unit_obj.Name if hasattr(unit_obj, 'Name') else "N/A",
                    "abbreviation": unit_obj.Abbreviation if hasattr(unit_obj, 'Abbreviation') else "N/A",
                    "symbol": unit_obj.Symbol if hasattr(unit_obj, 'Symbol') else "N/A",
                    "tag": str(unit_obj.Tag),
                    "is_base_unit": unit_obj.IsBaseUnit if hasattr(unit_obj, 'IsBaseUnit') else "N/A",
                    "is_default_unit": unit_obj.IsDefaultUnit if hasattr(unit_obj, 'IsDefaultUnit') else "N/A"
                }
            except Exception as e:
                unit_info["display_units_info"][measure_type] = {"error": str(e)}
    except Exception as e:
        unit_info["display_units_info"]["error"] = str(e)
    
    # 3. 获取所有可用的度量类型
    try:
        available_measures = []
        # 尝试获取可用的度量类型
        # 注意：UnitCollection 可能没有直接的方法获取所有度量类型
        # 我们可以尝试一些常见的度量类型
        common_measures = ["长度", "面积", "体积", "质量", "质量密度", "时间", "角度", 
                          "速度", "加速度", "力", "压力", "力矩", "温度"]
        for measure in common_measures:
            try:
                uc.GetBase(measure)
                available_measures.append(measure)
            except:
                pass
        unit_info["available_measures"] = available_measures
    except Exception as e:
        unit_info["available_measures_error"] = str(e)
    
    # 4. 获取单位对象的属性列表
    try:
        # 以长度单位为例，获取其所有属性
        length_unit = uc.GetBase("长度")
        attributes = []
        for attr in dir(length_unit):
            if not attr.startswith("_"):
                try:
                    # 尝试获取属性值
                    value = getattr(length_unit, attr)
                    if callable(value):
                        attributes.append(f"{attr}: callable")
                    else:
                        attributes.append(f"{attr}: {type(value).__name__}")
                except:
                    attributes.append(f"{attr}: inaccessible")
        unit_info["unit_objects_info"]["length_unit_attributes"] = attributes[:20]  # 只取前20个
    except Exception as e:
        unit_info["unit_objects_info"]["error"] = str(e)
    
    # 5. 探索 UnitCollection 的属性和方法
    try:
        uc_attributes = []
        for attr in dir(uc):
            if not attr.startswith("_"):
                try:
                    value = getattr(uc, attr)
                    if callable(value):
                        uc_attributes.append(f"{attr}: callable")
                    else:
                        uc_attributes.append(f"{attr}: {type(value).__name__}")
                except:
                    uc_attributes.append(f"{attr}: inaccessible")
        unit_info["unit_collection_info"] = {
            "attributes": uc_attributes[:30],  # 只取前30个
            "type": str(type(uc))
        }
    except Exception as e:
        unit_info["unit_collection_info"] = {"error": str(e)}
    
    # 6. 尝试通过 UF API 获取单位信息
    try:
        uf_session = NXOpen.UF.UFSession.GetUFSession()
        # 尝试获取单位信息
        # UF API 可能有单位相关函数
        unit_info["uf_api_info"] = {
            "available": True,
            "session_type": str(type(uf_session))
        }
    except Exception as e:
        unit_info["uf_api_info"] = {"error": str(e)}
    
    # 7. 探索其他可能的单位相关类
    try:
        # 尝试导入可能的单位相关模块
        unit_info["other_unit_classes"] = {}
        
        # 检查是否有 UnitManager
        try:
            unit_manager = NXOpen.Session.GetSession().UnitManager
            unit_info["other_unit_classes"]["UnitManager"] = str(type(unit_manager))
        except:
            unit_info["other_unit_classes"]["UnitManager"] = "Not found"
            
        # 检查是否有 Preferences
        try:
            preferences = NXOpen.Session.GetSession().Preferences
            unit_info["other_unit_classes"]["Preferences"] = str(type(preferences))
        except:
            unit_info["other_unit_classes"]["Preferences"] = "Not found"
            
        # 检查是否有 UnitSystem
        try:
            unit_system = work_part.UnitSystem
            unit_info["other_unit_classes"]["UnitSystem"] = str(type(unit_system))
        except:
            unit_info["other_unit_classes"]["UnitSystem"] = "Not found"
            
    except Exception as e:
        unit_info["other_unit_classes"] = {"error": str(e)}
    
    # 8. 尝试获取单位转换信息
    try:
        # 尝试获取单位转换因子
        length_unit = uc.GetBase("长度")
        # 尝试调用 Measure 方法
        if hasattr(length_unit, 'Measure'):
            unit_info["conversion_info"] = {
                "has_measure_method": True
            }
        else:
            unit_info["conversion_info"] = {
                "has_measure_method": False
            }
    except Exception as e:
        unit_info["conversion_info"] = {"error": str(e)}
    
    # 9. 探索 Preferences 的单位设置
    try:
        preferences = NXOpen.Session.GetSession().Preferences
        unit_info["preferences_info"] = {
            "type": str(type(preferences)),
            "available": True
        }
        
        # 尝试获取 Preferences 的属性
        pref_attributes = []
        for attr in dir(preferences):
            if not attr.startswith("_") and "unit" in attr.lower():
                try:
                    value = getattr(preferences, attr)
                    if callable(value):
                        pref_attributes.append(f"{attr}: callable")
                    else:
                        pref_attributes.append(f"{attr}: {type(value).__name__}")
                except:
                    pref_attributes.append(f"{attr}: inaccessible")
        
        if pref_attributes:
            unit_info["preferences_info"]["unit_related_attributes"] = pref_attributes[:10]  # 只取前10个
        else:
            unit_info["preferences_info"]["unit_related_attributes"] = "No unit-related attributes found"
            
    except Exception as e:
        unit_info["preferences_info"] = {"error": str(e)}
    
    # 10. 探索 UnitCollection 的其他方法
    try:
        # 尝试 GetDefaultDataEntryUnits 方法
        try:
            data_entry_units = uc.GetDefaultDataEntryUnits()
            unit_info["unit_collection_methods"] = {
                "GetDefaultDataEntryUnits": str(type(data_entry_units))
            }
        except Exception as e1:
            unit_info["unit_collection_methods"] = {
                "GetDefaultDataEntryUnits_error": str(e1)
            }
        
        # 尝试 GetDefaultObjectInformationUnits 方法
        try:
            obj_info_units = uc.GetDefaultObjectInformationUnits()
            if "unit_collection_methods" in unit_info:
                unit_info["unit_collection_methods"]["GetDefaultObjectInformationUnits"] = str(type(obj_info_units))
            else:
                unit_info["unit_collection_methods"] = {
                    "GetDefaultObjectInformationUnits": str(type(obj_info_units))
                }
        except Exception as e2:
            if "unit_collection_methods" in unit_info:
                unit_info["unit_collection_methods"]["GetDefaultObjectInformationUnits_error"] = str(e2)
            else:
                unit_info["unit_collection_methods"] = {
                    "GetDefaultObjectInformationUnits_error": str(e2)
                }
                
    except Exception as e:
        if "unit_collection_methods" not in unit_info:
            unit_info["unit_collection_methods"] = {"error": str(e)}
    
    # 11. 尝试探索 Session 的单位相关属性
    try:
        session = NXOpen.Session.GetSession()
        session_attributes = []
        for attr in dir(session):
            if not attr.startswith("_") and "unit" in attr.lower():
                try:
                    value = getattr(session, attr)
                    if callable(value):
                        session_attributes.append(f"{attr}: callable")
                    else:
                        session_attributes.append(f"{attr}: {type(value).__name__}")
                except:
                    session_attributes.append(f"{attr}: inaccessible")
        
        if session_attributes:
            unit_info["session_unit_attributes"] = session_attributes[:10]
        else:
            unit_info["session_unit_attributes"] = "No unit-related attributes in Session"
            
    except Exception as e:
        unit_info["session_unit_attributes"] = {"error": str(e)}
    
    # 12. 探索 UF API 单位相关函数
    try:
        uf_session = NXOpen.UF.UFSession.GetUFSession()
        uf_unit_info = {}
        
        # 探索 UF API 中可能包含 "unit" 或 "unt" 的函数
        uf_methods = []
        for attr in dir(uf_session):
            if not attr.startswith("_") and ("unit" in attr.lower() or "unt" in attr.lower()):
                try:
                    value = getattr(uf_session, attr)
                    if callable(value):
                        uf_methods.append(f"{attr}: callable")
                    else:
                        uf_methods.append(f"{attr}: {type(value).__name__}")
                except:
                    uf_methods.append(f"{attr}: inaccessible")
        
        if uf_methods:
            uf_unit_info["unit_related_methods"] = uf_methods[:15]  # 只取前15个
        
        # 尝试调用一些已知的 UF API 单位函数
        try:
            # 尝试 UF_UNT_ask_units 或类似函数
            # 首先检查是否有 AskUnits 或类似方法
            if hasattr(uf_session, 'AskUnits'):
                uf_unit_info["has_AskUnits"] = True
            else:
                uf_unit_info["has_AskUnits"] = False
                
            # 尝试 UF_UNT_get_system_units
            if hasattr(uf_session, 'GetSystemUnits'):
                uf_unit_info["has_GetSystemUnits"] = True
            else:
                uf_unit_info["has_GetSystemUnits"] = False
                
            # 尝试 UF_UNT_get_display_units
            if hasattr(uf_session, 'GetDisplayUnits'):
                uf_unit_info["has_GetDisplayUnits"] = True
            else:
                uf_unit_info["has_GetDisplayUnits"] = False
                
        except Exception as e:
            uf_unit_info["function_check_error"] = str(e)
        
        # 尝试获取 UF 常量中与单位相关的常量
        try:
            # 探索 UFConstants 中与单位相关的常量
            uf_constants = NXOpen.UF.UFConstants
            unit_constants = []
            for attr in dir(uf_constants):
                if not attr.startswith("_") and ("unit" in attr.lower() or "unt" in attr.lower()):
                    try:
                        value = getattr(uf_constants, attr)
                        unit_constants.append(f"{attr}: {value}")
                    except:
                        unit_constants.append(f"{attr}: inaccessible")
            
            if unit_constants:
                uf_unit_info["unit_constants"] = unit_constants[:10]
        except Exception as e:
            uf_unit_info["constants_error"] = str(e)
        
        unit_info["uf_api_unit_info"] = uf_unit_info
        
    except Exception as e:
        unit_info["uf_api_unit_info"] = {"error": str(e)}
    
    # 13. 尝试通过 UF API 获取实际单位信息
    try:
        uf_session = NXOpen.UF.UFSession.GetUFSession()
        
        # 尝试获取零件单位
        try:
            # 获取零件标签
            part_tag = work_part.Tag
            
            # 尝试 UF_MODL_ask_part_units
            if hasattr(uf_session.Modl, 'AskPartUnits'):
                units = uf_session.Modl.AskPartUnits(part_tag)
                unit_info["uf_part_units"] = {
                    "AskPartUnits_result": str(units)
                }
        except Exception as e:
            unit_info["uf_part_units"] = {"error": str(e)}
            
        # 尝试获取显示单位
        try:
            # 检查是否有获取显示单位的方法
            if hasattr(uf_session, 'Pref'):
                # 尝试获取首选项中的单位设置
                unit_info["uf_pref_units"] = {
                    "has_Pref": True
                }
            else:
                unit_info["uf_pref_units"] = {
                    "has_Pref": False
                }
        except Exception as e:
            unit_info["uf_pref_units"] = {"error": str(e)}
            
    except Exception as e:
        unit_info["uf_actual_units"] = {"error": str(e)}
    
    # 14. 尝试 UnitCollection.Convert() 方法
    try:
        # 尝试在不同单位间转换
        length_unit = uc.GetBase("长度")
        area_unit = uc.GetBase("面积")
        volume_unit = uc.GetBase("体积")
        
        # 尝试将1毫米转换为米
        try:
            # 获取毫米单位
            mm_unit = uc.GetBase("长度")
            m_unit = None
            
            # 尝试查找米单位
            try:
                m_unit = uc.GetBase("长度")  # 注意：这里可能需要不同的参数
            except:
                pass
                
            unit_info["convert_test"] = {
                "has_convert_method": hasattr(uc, 'Convert'),
                "length_unit_type": str(type(length_unit)),
                "area_unit_type": str(type(area_unit)),
                "volume_unit_type": str(type(volume_unit))
            }
            
            # 如果Convert方法可用，尝试转换
            if hasattr(uc, 'Convert'):
                try:
                    # 尝试简单的转换
                    unit_info["convert_test"]["convert_available"] = True
                except Exception as conv_e:
                    unit_info["convert_test"]["convert_error"] = str(conv_e)
            else:
                unit_info["convert_test"]["convert_available"] = False
                
        except Exception as e:
            unit_info["convert_test"] = {"error": str(e)}
            
    except Exception as e:
        unit_info["convert_test"] = {"error": str(e)}
    
    # 15. 尝试单位对象的 Measure 方法
    try:
        length_unit = uc.GetBase("长度")
        if hasattr(length_unit, 'Measure'):
            unit_info["measure_test"] = {
                "has_measure_method": True,
                "measure_method_type": str(type(length_unit.Measure))
            }
            
            # 尝试调用Measure方法
            try:
                # 尝试测量一个值
                unit_info["measure_test"]["measure_callable"] = True
            except Exception as measure_e:
                unit_info["measure_test"]["measure_error"] = str(measure_e)
        else:
            unit_info["measure_test"] = {
                "has_measure_method": False
            }
    except Exception as e:
        unit_info["measure_test"] = {"error": str(e)}
    
    # 16. 探索其他 NX API 模块
    try:
        other_modules = {}
        
        # 尝试访问 PartCollection
        try:
            part_collection = the_session.Parts
            other_modules["PartCollection"] = str(type(part_collection))
        except:
            other_modules["PartCollection"] = "Not accessible"
        
        # 尝试访问 DisplayManager
        try:
            display_manager = the_session.DisplayManager
            other_modules["DisplayManager"] = str(type(display_manager))
        except:
            other_modules["DisplayManager"] = "Not accessible"
        
        # 尝试访问 ViewCollection
        try:
            view_collection = the_session.Views
            other_modules["ViewCollection"] = str(type(view_collection))
        except:
            other_modules["ViewCollection"] = "Not accessible"
        
        unit_info["other_nx_modules"] = other_modules
        
    except Exception as e:
        unit_info["other_nx_modules"] = {"error": str(e)}
    
    # 17. 尝试获取环境变量信息
    try:
        # 尝试获取 NX 环境信息
        env_info = {}
        
        # 检查是否有环境相关的方法
        try:
            session = NXOpen.Session.GetSession()
            # 尝试获取 NX 版本信息
            if hasattr(session, 'NXVersion'):
                env_info["nx_version"] = str(session.NXVersion)
        except:
            pass
            
        # 尝试获取执行信息
        try:
            exec_info = the_session.ExecutionInformation
            env_info["execution_info"] = str(type(exec_info))
        except:
            env_info["execution_info"] = "Not accessible"
        
        unit_info["environment_info"] = env_info
        
    except Exception as e:
        unit_info["environment_info"] = {"error": str(e)}
    
    return unit_info


def collect_system_unit_info():
    """
    收集系统级单位信息（配置文件、环境变量等）
    返回: 包含系统级单位信息的字典
    """
    system_info = {
        "config_files": {},
        "environment_variables": {},
        "registry_settings": {},
        "summary": []
    }
    
    try:
        import os
        import sys
        
        # 1. 检查NX环境变量
        nx_env_vars = [
            "UGII_ROOT_DIR",
            "UGII_BASE_DIR",
            "UGII_USER_DIR",
            "UGII_SITE_DIR",
            "UGII_LANG",
            "UGII_UNITS"
        ]
        
        for var in nx_env_vars:
            try:
                value = os.environ.get(var)
                if value:
                    system_info["environment_variables"][var] = value
                    system_info["summary"].append(f"环境变量 {var}: {value}")
                else:
                    system_info["environment_variables"][var] = "未设置"
            except Exception as e:
                system_info["environment_variables"][var] = f"读取错误: {str(e)}"
        
        # 2. 检查NX配置文件
        config_paths = []
        
        # 用户配置文件路径
        user_home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
        if user_home:
            # NX 12.0 配置文件路径
            nx120_config = os.path.join(user_home, "AppData", "Local", "Siemens", "NX120")
            if os.path.exists(nx120_config):
                config_paths.append(nx120_config)
            
            # NX 配置文件通用路径
            siemens_config = os.path.join(user_home, "AppData", "Local", "Siemens")
            if os.path.exists(siemens_config):
                config_paths.append(siemens_config)
        
        # 检查配置文件
        for config_path in config_paths:
            try:
                if os.path.exists(config_path) and os.path.isdir(config_path):
                    config_files = []
                    for file in os.listdir(config_path):
                        if file.lower().endswith(('.dpv', '.mtx', '.cfg', '.ini', '.dat')):
                            file_path = os.path.join(config_path, file)
                            config_files.append(file)
                            
                            # 尝试读取文件内容（限制大小）
                            try:
                                if os.path.getsize(file_path) < 100000:  # 限制100KB
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read(5000)  # 只读取前5000字符
                                    
                                    # 检查是否包含单位相关关键词
                                    unit_keywords = ['unit', 'units', 'measure', 'metric', 'imperial', '毫米', '米', 'inch', '英尺']
                                    if any(keyword.lower() in content.lower() for keyword in unit_keywords):
                                        system_info["config_files"][file] = {
                                            "path": file_path,
                                            "size": os.path.getsize(file_path),
                                            "has_unit_info": True,
                                            "preview": content[:500] if content else ""
                                        }
                                        system_info["summary"].append(f"配置文件 {file}: 包含单位信息")
                                    else:
                                        system_info["config_files"][file] = {
                                            "path": file_path,
                                            "size": os.path.getsize(file_path),
                                            "has_unit_info": False
                                        }
                                else:
                                    system_info["config_files"][file] = {
                                        "path": file_path,
                                        "size": os.path.getsize(file_path),
                                        "has_unit_info": "文件过大未分析"
                                    }
                            except Exception as file_e:
                                system_info["config_files"][file] = {
                                    "path": file_path,
                                    "error": f"读取错误: {str(file_e)}"
                                }
                    
                    if config_files:
                        system_info["summary"].append(f"配置目录 {config_path}: 找到 {len(config_files)} 个配置文件")
            except Exception as path_e:
                system_info["config_files"][config_path] = f"访问错误: {str(path_e)}"
        
        # 3. 尝试检查注册表（仅Windows）
        try:
            if sys.platform == "win32":
                import winreg
                
                reg_paths = [
                    r"SOFTWARE\Siemens\NX",
                    r"SOFTWARE\Siemens\NX\12.0",
                    r"SOFTWARE\Siemens\NX\NX120",
                    r"SOFTWARE\Siemens\Unigraphics NX"
                ]
                
                for reg_path in reg_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
                        system_info["registry_settings"][reg_path] = "可访问"
                        
                        # 尝试读取值
                        try:
                            i = 0
                            while True:
                                try:
                                    name, value, type_ = winreg.EnumValue(key, i)
                                    if 'unit' in name.lower():
                                        system_info["registry_settings"][f"{reg_path}\\{name}"] = str(value)
                                        system_info["summary"].append(f"注册表 {reg_path}\\{name}: {value}")
                                    i += 1
                                except OSError:
                                    break
                        except:
                            pass
                        finally:
                            winreg.CloseKey(key)
                    except Exception as reg_e:
                        system_info["registry_settings"][reg_path] = f"访问错误: {str(reg_e)}"
                        
        except Exception as reg_import_e:
            system_info["registry_settings"]["error"] = f"注册表模块不可用: {str(reg_import_e)}"
        
        # 4. 检查NX安装目录
        try:
            # 尝试通过环境变量查找安装目录
            ugii_root = os.environ.get("UGII_ROOT_DIR")
            if ugii_root:
                # 清理路径（去除末尾反斜杠）
                ugii_root = ugii_root.rstrip('\\')
                if os.path.exists(ugii_root):
                    system_info["installation_path"] = ugii_root
                    system_info["summary"].append(f"NX安装目录: {ugii_root}")
                    
                    # 检查安装目录下的配置文件
                    ug_configs = [
                        os.path.join(ugii_root, "ugii_env.dat"),
                        os.path.join(ugii_root, "ugii_env_ug.dat"),
                        os.path.join(ugii_root, "ug_metric.def"),
                        os.path.join(ugii_root, "ug_english.def")
                    ]
                    
                    for config_file in ug_configs:
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read(2000)
                                system_info["config_files"][os.path.basename(config_file)] = {
                                    "path": config_file,
                                    "preview": content[:500] if content else "",
                                    "has_unit_info": 'unit' in content.lower() or 'measure' in content.lower()
                                }
                            except Exception as config_e:
                                system_info["config_files"][os.path.basename(config_file)] = {
                                    "path": config_file,
                                    "error": f"读取错误: {str(config_e)}"
                                }
                else:
                    system_info["installation_path"] = f"路径不存在: {ugii_root}"
            else:
                system_info["installation_path"] = "未找到（UGII_ROOT_DIR未设置）"
        except Exception as install_e:
            system_info["installation_path"] = f"检查错误: {str(install_e)}"
        
        # 5. 检查Python路径中的NX模块
        try:
            nx_modules = []
            for path in sys.path:
                if "nx" in path.lower() or "siemens" in path.lower():
                    nx_modules.append(path)
            
            if nx_modules:
                system_info["python_paths"] = nx_modules[:5]  # 只显示前5个
                system_info["summary"].append(f"找到 {len(nx_modules)} 个NX相关Python路径")
        except Exception as path_e:
            system_info["python_paths"] = f"检查错误: {str(path_e)}"
        
    except Exception as e:
        system_info["error"] = f"系统级信息收集失败: {str(e)}"
    
    return system_info


def parse_config_files(config_files_info):
    """
    解析配置文件内容，查找显示单位设置
    参数: config_files_info - collect_system_unit_info返回的config_files字典
    返回: 包含解析结果的字典
    """
    parsed_info = {
        "display_unit_settings": [],
        "unit_related_settings": [],
        "file_analysis": {}
    }
    
    try:
        import os
        import re
        
        # 单位相关关键词
        unit_keywords = [
            # 显示单位相关
            "display units", "display_units", "display unit", "display_unit",
            "units display", "units_display",
            "part units", "part_units",
            "modeling units", "modeling_units",
            "units", "unit",
            # 单位类型
            "millimeter", "millimeters", "mm",
            "meter", "meters", "m",
            "inch", "inches", "in",
            "foot", "feet", "ft",
            # 中文本地化
            "毫米", "米", "英寸", "英尺",
            # 单位系统
            "metric", "imperial", "公制", "英制",
            # NX特定
            "ug_units", "ugii_units", "ug_display_units"
        ]
        
        for file_name, file_info in config_files_info.items():
            if not isinstance(file_info, dict):
                continue
                
            if "path" not in file_info:
                continue
                
            file_path = file_info.get("path")
            if not os.path.exists(file_path):
                continue
            
            file_analysis = {
                "path": file_path,
                "lines_with_units": [],
                "potential_display_unit_settings": [],
                "summary": []
            }
            
            try:
                # 读取整个文件（限制大小）
                file_size = os.path.getsize(file_path)
                if file_size > 1000000:  # 限制1MB
                    file_analysis["error"] = f"文件过大 ({file_size} bytes)，跳过详细分析"
                    parsed_info["file_analysis"][file_name] = file_analysis
                    continue
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 按行分析
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # 检查是否包含单位关键词
                    keyword_matches = []
                    for keyword in unit_keywords:
                        if keyword.lower() in line_lower:
                            keyword_matches.append(keyword)
                    
                    if keyword_matches:
                        # 检查是否是设置行（包含等号、冒号或设置语法）
                        is_setting_line = any(char in line for char in ['=', ':', '"', "'"]) or \
                                         any(word in line_lower for word in ['set', 'define', 'default', 'preference'])
                        
                        line_info = {
                            "line": line_num,
                            "content": line.strip(),
                            "keywords": keyword_matches,
                            "is_setting": is_setting_line
                        }
                        
                        file_analysis["lines_with_units"].append(line_info)
                        
                        # 如果是设置行，添加到潜在显示单位设置
                        if is_setting_line:
                            file_analysis["potential_display_unit_settings"].append(line_info)
                            
                            # 提取可能的设置值
                            setting_value = None
                            if '=' in line:
                                parts = line.split('=', 1)
                                if len(parts) > 1:
                                    setting_value = parts[1].strip()
                            elif ':' in line:
                                parts = line.split(':', 1)
                                if len(parts) > 1:
                                    setting_value = parts[1].strip()
                            
                            if setting_value:
                                # 检查设置值是否包含单位信息
                                unit_match = re.search(r'(millimeter|meter|inch|foot|mm|m|in|ft|毫米|米|英寸|英尺|metric|imperial|公制|英制)', 
                                                      setting_value, re.IGNORECASE)
                                if unit_match:
                                    display_setting = {
                                        "file": file_name,
                                        "line": line_num,
                                        "setting": line.strip(),
                                        "value": setting_value,
                                        "unit_match": unit_match.group(0)
                                    }
                                    parsed_info["display_unit_settings"].append(display_setting)
                                    file_analysis["summary"].append(f"行 {line_num}: 可能包含显示单位设置: {line.strip()}")
                
                # 添加文件分析摘要
                if file_analysis["lines_with_units"]:
                    file_analysis["summary"].append(f"找到 {len(file_analysis['lines_with_units'])} 行包含单位关键词")
                if file_analysis["potential_display_unit_settings"]:
                    file_analysis["summary"].append(f"找到 {len(file_analysis['potential_display_unit_settings'])} 个潜在显示单位设置")
                
                parsed_info["file_analysis"][file_name] = file_analysis
                
            except Exception as file_e:
                file_analysis["error"] = f"解析错误: {str(file_e)}"
                parsed_info["file_analysis"][file_name] = file_analysis
        
        # 汇总所有单位相关设置
        all_unit_settings = []
        for file_name, analysis in parsed_info["file_analysis"].items():
            if "potential_display_unit_settings" in analysis:
                for setting in analysis["potential_display_unit_settings"]:
                    all_unit_settings.append({
                        "file": file_name,
                        "line": setting["line"],
                        "content": setting["content"]
                    })
        
        parsed_info["unit_related_settings"] = all_unit_settings
        
    except Exception as e:
        parsed_info["error"] = f"配置文件解析失败: {str(e)}"
    
    return parsed_info


def check_part_attributes(work_part):
    """
    选项B：检查零件属性中的单位信息
    参数: work_part - 当前工作零件
    返回: 包含零件属性单位信息的字典
    """
    part_attrs_info = {
        "part_attributes": [],
        "unit_related_attributes": [],
        "summary": []
    }
    
    try:
        # 1. 检查零件是否有属性集合
        if hasattr(work_part, 'AttributeManager'):
            try:
                attr_manager = work_part.AttributeManager
                part_attrs_info["has_attribute_manager"] = True
                part_attrs_info["attribute_manager_type"] = str(type(attr_manager))
                
                # 尝试获取所有属性
                try:
                    # 检查是否有GetAttributes方法
                    if hasattr(attr_manager, 'GetAttributes'):
                        try:
                            attributes = attr_manager.GetAttributes()
                            part_attrs_info["attribute_count"] = len(attributes) if attributes else 0
                            part_attrs_info["summary"].append(f"零件属性数量: {part_attrs_info['attribute_count']}")
                            
                            # 检查属性中是否包含单位信息
                            unit_keywords = ['unit', 'units', 'measure', '毫米', '米', 'inch', '英尺', 'metric', 'imperial', '公制', '英制']
                            unit_related_attrs = []
                            
                            for i, attr in enumerate(attributes):
                                try:
                                    # 获取属性信息
                                    attr_info = {
                                        "index": i,
                                        "type": str(type(attr))
                                    }
                                    
                                    # 尝试获取属性名称
                                    if hasattr(attr, 'Title'):
                                        attr_info["title"] = attr.Title
                                    if hasattr(attr, 'Name'):
                                        attr_info["name"] = attr.Name
                                    if hasattr(attr, 'StringValue'):
                                        attr_info["string_value"] = attr.StringValue
                                    if hasattr(attr, 'Value'):
                                        attr_info["value"] = attr.Value
                                    
                                    # 检查是否包含单位关键词
                                    attr_str = str(attr_info).lower()
                                    if any(keyword in attr_str for keyword in unit_keywords):
                                        unit_related_attrs.append(attr_info)
                                        part_attrs_info["summary"].append(f"发现单位相关属性: {attr_info.get('title', 'N/A')} = {attr_info.get('string_value', 'N/A')}")
                                    
                                    part_attrs_info["part_attributes"].append(attr_info)
                                    
                                except Exception as attr_e:
                                    part_attrs_info["part_attributes"].append({"error": f"属性{i}读取错误: {str(attr_e)}"})
                            
                            part_attrs_info["unit_related_attributes"] = unit_related_attrs
                            
                        except Exception as get_attrs_e:
                            part_attrs_info["get_attributes_error"] = str(get_attrs_e)
                    else:
                        part_attrs_info["has_GetAttributes"] = False
                except Exception as attr_access_e:
                    part_attrs_info["attribute_access_error"] = str(attr_access_e)
                    
            except Exception as manager_e:
                part_attrs_info["attribute_manager_error"] = str(manager_e)
        else:
            part_attrs_info["has_attribute_manager"] = False
        
        # 2. 检查零件是否有单位相关属性
        try:
            # 尝试直接访问可能包含单位信息的属性
            direct_attrs = {}
            
            # 检查PartUnits属性（已经探索过）
            if hasattr(work_part, 'PartUnits'):
                direct_attrs["PartUnits"] = str(work_part.PartUnits)
            
            # 检查UnitSystem属性
            if hasattr(work_part, 'UnitSystem'):
                try:
                    unit_system = work_part.UnitSystem
                    direct_attrs["UnitSystem"] = str(type(unit_system))
                except:
                    direct_attrs["UnitSystem"] = "不可访问"
            
            # 检查DisplayUnits属性（如果存在）
            if hasattr(work_part, 'DisplayUnits'):
                try:
                    display_units = work_part.DisplayUnits
                    direct_attrs["DisplayUnits"] = str(display_units)
                    part_attrs_info["summary"].append(f"找到DisplayUnits属性: {display_units}")
                except:
                    direct_attrs["DisplayUnits"] = "不可访问"
            
            # 检查ModelingUnits属性
            if hasattr(work_part, 'ModelingUnits'):
                try:
                    modeling_units = work_part.ModelingUnits
                    direct_attrs["ModelingUnits"] = str(modeling_units)
                    part_attrs_info["summary"].append(f"找到ModelingUnits属性: {modeling_units}")
                except:
                    direct_attrs["ModelingUnits"] = "不可访问"
            
            part_attrs_info["direct_attributes"] = direct_attrs
            
        except Exception as direct_attr_e:
            part_attrs_info["direct_attributes_error"] = str(direct_attr_e)
        
        # 3. 检查UF API中的零件属性
        try:
            uf_session = NXOpen.UF.UFSession.GetUFSession()
            part_tag = work_part.Tag
            
            # 尝试使用UF API获取零件属性
            uf_attrs_info = {}
            
            # 尝试UF_ATTR_ask_part_attrs或类似函数
            if hasattr(uf_session, 'Attr'):
                uf_attrs_info["has_Attr_module"] = True
                
                # 尝试获取零件属性
                try:
                    # 检查是否有询问零件属性的方法
                    if hasattr(uf_session.Attr, 'AskPartAttrs'):
                        uf_attrs_info["has_AskPartAttrs"] = True
                    else:
                        uf_attrs_info["has_AskPartAttrs"] = False
                except:
                    uf_attrs_info["attr_module_error"] = "访问Attr模块错误"
            else:
                uf_attrs_info["has_Attr_module"] = False
            
            part_attrs_info["uf_api_attributes"] = uf_attrs_info
            
        except Exception as uf_e:
            part_attrs_info["uf_api_error"] = str(uf_e)
        
        # 4. 检查零件文件属性
        try:
            # 尝试获取零件文件路径和基本信息
            file_info = {
                "full_path": work_part.FullPath,
                "name": work_part.Name,
                "display_name": work_part.DisplayName if hasattr(work_part, 'DisplayName') else "N/A"
            }
            
            part_attrs_info["file_info"] = file_info
            
            # 检查文件扩展名和类型
            import os
            file_ext = os.path.splitext(work_part.FullPath)[1].lower()
            part_attrs_info["file_extension"] = file_ext
            
        except Exception as file_e:
            part_attrs_info["file_info_error"] = str(file_e)
        
    except Exception as e:
        part_attrs_info["error"] = f"零件属性检查失败: {str(e)}"
    
    return part_attrs_info


def explore_unit_conversion_methods(work_part):
    """
    选项C：深入探索单位转换和测量方法
    探索UnitCollection的Convert()和Measure()方法，尝试获取显示单位信息
    参数: work_part - 当前工作零件
    返回: 包含转换方法探索结果的字典
    """
    conversion_info = {
        "convert_method_exploration": {},
        "measure_method_exploration": {},
        "unit_detection_attempts": [],
        "summary": []
    }
    
    try:
        # 获取单位集合
        uc = work_part.UnitCollection
        
        # 1. 探索Convert方法
        try:
            if hasattr(uc, 'Convert'):
                conversion_info["convert_method_exploration"]["has_Convert"] = True
                
                # 尝试获取Convert方法的详细信息
                convert_method = uc.Convert
                conversion_info["convert_method_exploration"]["method_type"] = str(type(convert_method))
                
                # 尝试探索Convert方法的参数
                try:
                    # 获取长度单位
                    length_unit = uc.GetBase("长度")
                    conversion_info["convert_method_exploration"]["length_unit_info"] = {
                        "journal_identifier": length_unit.JournalIdentifier,
                        "name": length_unit.Name if hasattr(length_unit, 'Name') else "N/A",
                        "abbreviation": length_unit.Abbreviation if hasattr(length_unit, 'Abbreviation') else "N/A"
                    }
                    
                    # 尝试查找其他可能的单位（毫米、米、英寸）
                    # 首先检查是否有FindObject方法
                    if hasattr(uc, 'FindObject'):
                        try:
                            # 尝试查找毫米单位
                            mm_unit = uc.FindObject("MilliMeter")
                            conversion_info["convert_method_exploration"]["found_mm_unit"] = str(type(mm_unit)) if mm_unit else "未找到"
                            
                            # 尝试查找米单位
                            m_unit = uc.FindObject("Meter")
                            conversion_info["convert_method_exploration"]["found_m_unit"] = str(type(m_unit)) if m_unit else "未找到"
                            
                            # 尝试查找英寸单位
                            inch_unit = uc.FindObject("Inch")
                            conversion_info["convert_method_exploration"]["found_inch_unit"] = str(type(inch_unit)) if inch_unit else "未找到"
                        except Exception as find_e:
                            conversion_info["convert_method_exploration"]["find_object_error"] = str(find_e)
                    
                    # 尝试调用Convert方法进行单位转换测试
                    try:
                        # 获取当前长度单位
                        current_length_unit = uc.GetBase("长度")
                        
                        # 实验1：尝试不同参数格式调用Convert方法
                        conversion_experiments = []
                        
                        # 获取毫米和米单位对象
                        mm_unit = uc.FindObject("MilliMeter")
                        m_unit = uc.FindObject("Meter")
                        inch_unit = uc.FindObject("Inch")
                        
                        # 探索Convert方法的签名和参数
                        convert_method_info = {}
                        try:
                            convert_method = uc.Convert
                            convert_method_info["method_type"] = str(type(convert_method))
                            
                            # 尝试获取方法文档
                            if hasattr(convert_method, '__doc__'):
                                convert_method_info["doc"] = str(convert_method.__doc__)[:200] + "..." if len(str(convert_method.__doc__)) > 200 else str(convert_method.__doc__)
                            
                            # 尝试检查方法是否可调用
                            convert_method_info["callable"] = callable(convert_method)
                            
                            # 尝试使用dir获取方法属性
                            convert_method_info["dir_attributes"] = [attr for attr in dir(convert_method) if not attr.startswith('_')][:10]
                            
                            conversion_info["convert_method_exploration"]["method_signature_info"] = convert_method_info
                        except Exception as sig_e:
                            conversion_info["convert_method_exploration"]["signature_error"] = str(sig_e)
                        
                        # 实验1a：原始格式 Convert(value, from_unit, to_unit) - 根据错误信息可能不对
                        try:
                            result_mm_to_m = uc.Convert(1.0, mm_unit, m_unit)
                            conversion_experiments.append({
                                "format": "Convert(1.0, mm_unit, m_unit)",
                                "result": result_mm_to_m,
                                "expected": 0.001 if "MilliMeter" in current_length_unit.JournalIdentifier else 1000.0,
                                "status": "成功"
                            })
                        except Exception as e1a:
                            conversion_experiments.append({
                                "format": "Convert(1.0, mm_unit, m_unit)",
                                "error": str(e1a),
                                "status": "失败"
                            })
                        
                        # 实验1b：米转毫米
                        try:
                            result_m_to_mm = uc.Convert(1.0, m_unit, mm_unit)
                            conversion_experiments.append({
                                "format": "Convert(1.0, m_unit, mm_unit)",
                                "result": result_m_to_mm,
                                "expected": 1000.0 if "MilliMeter" in current_length_unit.JournalIdentifier else 0.001,
                                "status": "成功"
                            })
                        except Exception as e1b:
                            conversion_experiments.append({
                                "format": "Convert(1.0, m_unit, mm_unit)",
                                "error": str(e1b),
                                "status": "失败"
                            })
                        
                        # 实验1c：当前单位转自身
                        try:
                            result_self = uc.Convert(1.0, current_length_unit, current_length_unit)
                            conversion_experiments.append({
                                "format": "Convert(1.0, current_unit, current_unit)",
                                "result": result_self,
                                "expected": 1.0,
                                "status": "成功"
                            })
                        except Exception as e1c:
                            conversion_experiments.append({
                                "format": "Convert(1.0, current_unit, current_unit)",
                                "error": str(e1c),
                                "status": "失败"
                            })
                        
                        # 实验2：尝试新格式 Convert(from_unit, to_unit, value) - 根据错误信息第一个参数应该是单位
                        try:
                            result_mm_to_m = uc.Convert(mm_unit, m_unit, 1.0)
                            conversion_experiments.append({
                                "format": "Convert(mm_unit, m_unit, 1.0)",
                                "result": result_mm_to_m,
                                "expected": 0.001 if "MilliMeter" in current_length_unit.JournalIdentifier else 1000.0,
                                "status": "成功"
                            })
                        except Exception as e2:
                            conversion_experiments.append({
                                "format": "Convert(mm_unit, m_unit, 1.0)",
                                "error": str(e2),
                                "status": "失败"
                            })
                        
                        # 实验3：尝试新格式 Convert(from_unit, value, to_unit)
                        try:
                            result_mm_to_m = uc.Convert(mm_unit, 1.0, m_unit)
                            conversion_experiments.append({
                                "format": "Convert(mm_unit, 1.0, m_unit)",
                                "result": result_mm_to_m,
                                "expected": 0.001 if "MilliMeter" in current_length_unit.JournalIdentifier else 1000.0,
                                "status": "成功"
                            })
                        except Exception as e3:
                            conversion_experiments.append({
                                "format": "Convert(mm_unit, 1.0, m_unit)",
                                "error": str(e3),
                                "status": "失败"
                            })
                        
                        # 实验4：尝试字符串参数格式 Convert(value, "from_unit_name", "to_unit_name")
                        try:
                            result_str = uc.Convert(1.0, "MilliMeter", "Meter")
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "MilliMeter", "Meter")',
                                "result": result_str,
                                "expected": 0.001,
                                "status": "成功"
                            })
                        except Exception as e4:
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "MilliMeter", "Meter")',
                                "error": str(e4),
                                "status": "失败"
                            })
                        
                        # 实验5：尝试关键字参数格式 Convert(value=1.0, fromUnit=mm_unit, toUnit=m_unit)
                        try:
                            result_kw = uc.Convert(value=1.0, fromUnit=mm_unit, toUnit=m_unit)
                            conversion_experiments.append({
                                "format": "Convert(value=1.0, fromUnit=mm_unit, toUnit=m_unit)",
                                "result": result_kw,
                                "expected": 0.001,
                                "status": "成功"
                            })
                        except Exception as e5:
                            conversion_experiments.append({
                                "format": "Convert(value=1.0, fromUnit=mm_unit, toUnit=m_unit)",
                                "error": str(e5),
                                "status": "失败"
                            })
                        
                        # 实验6：尝试其他关键字参数组合
                        try:
                            result_kw2 = uc.Convert(fromUnit=mm_unit, toUnit=m_unit, value=1.0)
                            conversion_experiments.append({
                                "format": "Convert(fromUnit=mm_unit, toUnit=m_unit, value=1.0)",
                                "result": result_kw2,
                                "expected": 0.001,
                                "status": "成功"
                            })
                        except Exception as e6:
                            conversion_experiments.append({
                                "format": "Convert(fromUnit=mm_unit, toUnit=m_unit, value=1.0)",
                                "error": str(e6),
                                "status": "失败"
                            })
                        
                        # 实验7：尝试使用单位标识符字符串
                        try:
                            result_id = uc.Convert(1.0, "MilliMeter", "Meter")
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "MilliMeter", "Meter")',
                                "result": result_id,
                                "expected": 0.001,
                                "status": "成功"
                            })
                        except Exception as e7:
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "MilliMeter", "Meter")',
                                "error": str(e7),
                                "status": "失败"
                            })
                        
                        # 实验8：尝试使用单位缩写
                        try:
                            result_abbr = uc.Convert(1.0, "mm", "m")
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "mm", "m")',
                                "result": result_abbr,
                                "expected": 0.001,
                                "status": "成功"
                            })
                        except Exception as e8:
                            conversion_experiments.append({
                                "format": 'Convert(1.0, "mm", "m")',
                                "error": str(e8),
                                "status": "失败"
                            })
                        
                        # 分析转换实验结果
                        successful_experiments = [exp for exp in conversion_experiments if exp.get("status") == "成功"]
                        
                        if successful_experiments:
                            conversion_info["convert_method_exploration"]["convert_test"] = {
                                "status": "成功",
                                "successful_experiments": len(successful_experiments),
                                "total_experiments": len(conversion_experiments),
                                "experiments": conversion_experiments
                            }
                            
                            # 根据转换结果推断显示单位
                            if successful_experiments:
                                # 分析所有成功实验的结果
                                mm_to_m_results = []
                                m_to_mm_results = []
                                self_conversion_results = []
                                
                                for exp in successful_experiments:
                                    result_value = exp.get("result")
                                    if result_value is None:
                                        continue
                                    
                                    format_str = exp.get("format", "")
                                    
                                    # 分类实验类型
                                    if "mm_unit" in format_str and "m_unit" in format_str:
                                        if "Convert(1.0, mm_unit, m_unit)" in format_str or "Convert(mm_unit, m_unit" in format_str or "Convert(mm_unit, 1.0, m_unit)" in format_str:
                                            mm_to_m_results.append(result_value)
                                        elif "Convert(1.0, m_unit, mm_unit)" in format_str or "Convert(m_unit, mm_unit" in format_str or "Convert(m_unit, 1.0, mm_unit)" in format_str:
                                            m_to_mm_results.append(result_value)
                                    elif "current_unit" in format_str:
                                        self_conversion_results.append(result_value)
                                    elif "MilliMeter" in format_str and "Meter" in format_str:
                                        # 字符串格式实验
                                        if '"MilliMeter"' in format_str and '"Meter"' in format_str:
                                            mm_to_m_results.append(result_value)
                                    elif "mm" in format_str and "m" in format_str:
                                        # 缩写格式实验
                                        if '"mm"' in format_str and '"m"' in format_str:
                                            mm_to_m_results.append(result_value)
                                
                                # 根据转换结果推断显示单位
                                inferred_unit = None
                                
                                # 分析毫米转米的结果
                                if mm_to_m_results:
                                    avg_mm_to_m = sum(mm_to_m_results) / len(mm_to_m_results)
                                    if abs(avg_mm_to_m - 0.001) < 0.0001:  # 1毫米 = 0.001米
                                        inferred_unit = "毫米"
                                        conversion_info["summary"].append(f"Convert方法成功：毫米→米转换系数 {avg_mm_to_m:.6f}，显示单位可能是毫米")
                                    elif abs(avg_mm_to_m - 1000.0) < 1.0:  # 1米 = 1000毫米
                                        inferred_unit = "米"
                                        conversion_info["summary"].append(f"Convert方法成功：毫米→米转换系数 {avg_mm_to_m:.6f}，显示单位可能是米")
                                
                                # 分析米转毫米的结果
                                if m_to_mm_results and not inferred_unit:
                                    avg_m_to_mm = sum(m_to_mm_results) / len(m_to_mm_results)
                                    if abs(avg_m_to_mm - 1000.0) < 1.0:  # 1米 = 1000毫米
                                        inferred_unit = "米"
                                        conversion_info["summary"].append(f"Convert方法成功：米→毫米转换系数 {avg_m_to_mm:.6f}，显示单位可能是米")
                                    elif abs(avg_m_to_mm - 0.001) < 0.0001:  # 1毫米 = 0.001米
                                        inferred_unit = "毫米"
                                        conversion_info["summary"].append(f"Convert方法成功：米→毫米转换系数 {avg_m_to_mm:.6f}，显示单位可能是毫米")
                                
                                # 分析自转换结果
                                if self_conversion_results and not inferred_unit:
                                    avg_self = sum(self_conversion_results) / len(self_conversion_results)
                                    if abs(avg_self - 1.0) < 0.0001:  # 自转换应为1
                                        conversion_info["summary"].append(f"Convert方法成功：自转换系数 {avg_self:.6f}")
                                
                                # 设置推断的单位
                                if inferred_unit:
                                    conversion_info["convert_method_exploration"]["inferred_display_unit"] = inferred_unit
                                else:
                                    conversion_info["summary"].append("Convert方法成功但无法推断显示单位")
                        else:
                            conversion_info["convert_method_exploration"]["convert_test"] = {
                                "status": "全部失败",
                                "experiments": conversion_experiments
                            }
                            conversion_info["summary"].append("Convert方法实验全部失败，无法确定参数格式")
                        
                    except Exception as convert_test_e:
                        conversion_info["convert_method_exploration"]["convert_test_error"] = str(convert_test_e)
                        conversion_info["summary"].append(f"Convert方法测试错误: {str(convert_test_e)}")
                    
                except Exception as convert_explore_e:
                    conversion_info["convert_method_exploration"]["exploration_error"] = str(convert_explore_e)
            else:
                conversion_info["convert_method_exploration"]["has_Convert"] = False
        except Exception as convert_e:
            conversion_info["convert_method_exploration"]["error"] = str(convert_e)
        
        # 1.5 检查Unit对象是否有Convert方法
        try:
            # 获取长度单位对象
            length_unit = uc.GetBase("长度")
            
            if hasattr(length_unit, 'Convert'):
                conversion_info["unit_object_convert_exploration"] = {}
                conversion_info["unit_object_convert_exploration"]["has_Convert"] = True
                conversion_info["unit_object_convert_exploration"]["method_type"] = str(type(length_unit.Convert))
                
                # 尝试调用Unit对象的Convert方法
                try:
                    # 获取毫米和米单位对象
                    mm_unit = uc.FindObject("MilliMeter")
                    m_unit = uc.FindObject("Meter")
                    
                    if mm_unit and m_unit:
                        # 尝试不同参数顺序
                        unit_convert_experiments = []
                        
                        # 实验A: Convert(value, from_unit, to_unit)
                        try:
                            result = length_unit.Convert(1.0, mm_unit, m_unit)
                            unit_convert_experiments.append({
                                "format": "Unit.Convert(1.0, mm_unit, m_unit)",
                                "result": result,
                                "status": "成功"
                            })
                        except Exception as e_a:
                            unit_convert_experiments.append({
                                "format": "Unit.Convert(1.0, mm_unit, m_unit)",
                                "error": str(e_a),
                                "status": "失败"
                            })
                        
                        # 实验B: Convert(from_unit, to_unit, value)
                        try:
                            result = length_unit.Convert(mm_unit, m_unit, 1.0)
                            unit_convert_experiments.append({
                                "format": "Unit.Convert(mm_unit, m_unit, 1.0)",
                                "result": result,
                                "status": "成功"
                            })
                        except Exception as e_b:
                            unit_convert_experiments.append({
                                "format": "Unit.Convert(mm_unit, m_unit, 1.0)",
                                "error": str(e_b),
                                "status": "失败"
                            })
                        
                        conversion_info["unit_object_convert_exploration"]["experiments"] = unit_convert_experiments
                        conversion_info["unit_object_convert_exploration"]["successful_count"] = len([exp for exp in unit_convert_experiments if exp.get("status") == "成功"])
                        
                        if unit_convert_experiments:
                            conversion_info["summary"].append(f"Unit对象有Convert方法，实验成功数: {conversion_info['unit_object_convert_exploration']['successful_count']}/{len(unit_convert_experiments)}")
                except Exception as unit_convert_e:
                    conversion_info["unit_object_convert_exploration"]["experiment_error"] = str(unit_convert_e)
            else:
                conversion_info["unit_object_convert_exploration"] = {"has_Convert": False}
        except Exception as unit_convert_explore_e:
            conversion_info["unit_object_convert_exploration"] = {"error": str(unit_convert_explore_e)}
        
        # 2. 探索Measure方法
        try:
            # 获取长度单位
            length_unit = uc.GetBase("长度")
            
            if hasattr(length_unit, 'Measure'):
                conversion_info["measure_method_exploration"]["has_Measure"] = True
                conversion_info["measure_method_exploration"]["measure_method_type"] = str(type(length_unit.Measure))
                
                # 尝试探索Measure方法的参数
                try:
                    # Measure方法可能用于测量值并返回单位信息
                    # 尝试调用Measure方法
                    conversion_info["measure_method_exploration"]["measure_available"] = True
                    conversion_info["summary"].append("Measure方法可用，可能用于单位检测")
                    
                    # 尝试获取Measure方法的文档或帮助信息
                    # 在NX中，Measure可能用于测量距离、角度等
                    
                except Exception as measure_explore_e:
                    conversion_info["measure_method_exploration"]["exploration_error"] = str(measure_explore_e)
            else:
                conversion_info["measure_method_exploration"]["has_Measure"] = False
        except Exception as measure_e:
            conversion_info["measure_method_exploration"]["error"] = str(measure_e)
        
        # 3. 尝试通过其他方法检测显示单位
        try:
            # 尝试使用GetDefaultDataEntryUnits方法
            if hasattr(uc, 'GetDefaultDataEntryUnits'):
                try:
                    data_entry_units = uc.GetDefaultDataEntryUnits()
                    conversion_info["unit_detection_attempts"].append({
                        "method": "GetDefaultDataEntryUnits",
                        "result": str(type(data_entry_units)),
                        "description": "数据输入默认单位"
                    })
                    conversion_info["summary"].append("找到GetDefaultDataEntryUnits方法")
                except Exception as data_entry_e:
                    conversion_info["unit_detection_attempts"].append({
                        "method": "GetDefaultDataEntryUnits",
                        "error": str(data_entry_e)
                    })
            
            # 尝试使用GetDefaultObjectInformationUnits方法
            if hasattr(uc, 'GetDefaultObjectInformationUnits'):
                try:
                    obj_info_units = uc.GetDefaultObjectInformationUnits()
                    conversion_info["unit_detection_attempts"].append({
                        "method": "GetDefaultObjectInformationUnits",
                        "result": str(type(obj_info_units)),
                        "description": "对象信息默认单位"
                    })
                    conversion_info["summary"].append("找到GetDefaultObjectInformationUnits方法")
                except Exception as obj_info_e:
                    conversion_info["unit_detection_attempts"].append({
                        "method": "GetDefaultObjectInformationUnits",
                        "error": str(obj_info_e)
                    })
            
            # 尝试探索UnitCollection的其他方法
            unit_methods = []
            for attr_name in dir(uc):
                if not attr_name.startswith("_"):
                    try:
                        attr_value = getattr(uc, attr_name)
                        if callable(attr_value):
                            # 检查方法名是否包含单位相关关键词
                            unit_keywords = ['unit', 'measure', 'convert', 'display', 'length', 'area', 'volume']
                            if any(keyword in attr_name.lower() for keyword in unit_keywords):
                                unit_methods.append(attr_name)
                    except:
                        pass
            
            if unit_methods:
                conversion_info["unit_detection_attempts"].append({
                    "method": "UnitCollection方法扫描",
                    "found_methods": unit_methods[:10],  # 只显示前10个
                    "description": f"找到{len(unit_methods)}个单位相关方法"
                })
                conversion_info["summary"].append(f"扫描到{len(unit_methods)}个单位相关方法")
            
        except Exception as detection_e:
            conversion_info["unit_detection_attempts"].append({
                "method": "其他单位检测方法",
                "error": str(detection_e)
            })
        
        # 4. 尝试通过UF API获取单位信息
        try:
            uf_session = NXOpen.UF.UFSession.GetUFSession()
            
            # 检查UF API中的单位相关函数
            uf_unit_methods = []
            if hasattr(uf_session, 'Unit'):
                uf_unit_module = uf_session.Unit
                for attr_name in dir(uf_unit_module):
                    if not attr_name.startswith("_"):
                        uf_unit_methods.append(attr_name)
            
            if uf_unit_methods:
                conversion_info["unit_detection_attempts"].append({
                    "method": "UF API Unit模块",
                    "found_methods": uf_unit_methods[:10],  # 只显示前10个
                    "description": f"UF Unit模块有{len(uf_unit_methods)}个方法"
                })
                conversion_info["summary"].append(f"UF Unit模块有{len(uf_unit_methods)}个方法")
            
            # 尝试调用UF_UNIT_ask_units或类似函数
            if hasattr(uf_session, 'Unit') and hasattr(uf_session.Unit, 'AskUnits'):
                try:
                    # 获取零件标签
                    part_tag = work_part.Tag
                    # 尝试调用AskUnits
                    conversion_info["unit_detection_attempts"].append({
                        "method": "UF_UNIT_ask_units",
                        "status": "方法存在，需要参数",
                        "description": "可能用于查询零件单位"
                    })
                except Exception as ask_units_e:
                    conversion_info["unit_detection_attempts"].append({
                        "method": "UF_UNIT_ask_units",
                        "error": str(ask_units_e)
                    })
            
        except Exception as uf_api_e:
            conversion_info["unit_detection_attempts"].append({
                "method": "UF API单位检测",
                "error": str(uf_api_e)
            })
        
        # 5. 尝试通过数值特征推断（仅作为最后手段）
        try:
            # 获取测量管理器
            measure_manager = work_part.MeasureManager
            
            # 尝试创建一个简单的测量来观察单位
            conversion_info["unit_detection_attempts"].append({
                "method": "测量管理器分析",
                "status": "可用",
                "description": "MeasureManager可用于创建测量，可能反映显示单位"
            })
            conversion_info["summary"].append("MeasureManager可用于单位分析")
            
        except Exception as measure_mgr_e:
            conversion_info["unit_detection_attempts"].append({
                "method": "测量管理器分析",
                "error": str(measure_mgr_e)
            })
        
    except Exception as e:
        conversion_info["error"] = f"单位转换方法探索失败: {str(e)}"
    
    return conversion_info


def main():
    the_session = NXOpen.Session.GetSession()
    uf_session = NXOpen.UF.UFSession.GetUFSession()
    lw = the_session.ListingWindow
    lw.Open()
    lw.WriteLine("=" * 60)
    lw.WriteLine("质量属性提取脚本 v4.11 (精简版 + 最终单位检测)")
    lw.WriteLine("密度: 7.85 g/cm³ (7850 kg/m³)")
    lw.WriteLine("基于Convert方法的单位检测 + 质量属性提取")
    lw.WriteLine("=" * 60)
    
    # 定义要处理的零件文件
    folder_path = r"d:\python\nx-quotation-assistant"
    prt_files = [
        "m.prt",
        "mm.prt"
    ]
    
    # 密度 7.85 g/cm³ = 7850 kg/m³
    density = 7850.0  # kg/m³
    
    # 存储结果
    results = []
    
    # 系统级单位信息收集（选项A）
    lw.WriteLine(f"\n{'='*60}")
    lw.WriteLine("系统级单位信息收集（选项A）")
    lw.WriteLine(f"{'='*60}")
    system_unit_info = collect_system_unit_info()
    
    # 输出系统级信息摘要
    lw.WriteLine("\n系统级信息摘要:")
    if "error" in system_unit_info:
        lw.WriteLine(f"  错误: {system_unit_info['error']}")
    else:
        # 输出环境变量
        lw.WriteLine("  1. 环境变量:")
        for var, value in system_unit_info.get("environment_variables", {}).items():
            lw.WriteLine(f"    - {var}: {value}")
        
        # 输出配置文件信息
        lw.WriteLine("  2. 配置文件:")
        config_files = system_unit_info.get("config_files", {})
        if config_files:
            for file_name, file_info in config_files.items():
                if isinstance(file_info, dict):
                    if "has_unit_info" in file_info and file_info["has_unit_info"]:
                        lw.WriteLine(f"    - {file_name}: 包含单位信息")
                    elif "error" in file_info:
                        lw.WriteLine(f"    - {file_name}: 错误 - {file_info['error']}")
                    else:
                        lw.WriteLine(f"    - {file_name}: 已找到")
                else:
                    lw.WriteLine(f"    - {file_name}: {file_info}")
        else:
            lw.WriteLine("    - 未找到配置文件")
        
        # 输出注册表设置
        lw.WriteLine("  3. 注册表设置:")
        reg_settings = system_unit_info.get("registry_settings", {})
        if reg_settings:
            for key, value in reg_settings.items():
                lw.WriteLine(f"    - {key}: {value}")
        else:
            lw.WriteLine("    - 未找到注册表设置")
        
        # 输出安装目录
        lw.WriteLine("  4. NX安装目录:")
        lw.WriteLine(f"    - {system_unit_info.get('installation_path', '未找到')}")
        
        # 输出摘要
        lw.WriteLine("  5. 摘要:")
        for summary_item in system_unit_info.get("summary", []):
            lw.WriteLine(f"    - {summary_item}")
        
        # 6. 配置文件详细解析（已精简）
        lw.WriteLine("\n  6. 配置文件解析:")
        config_files = system_unit_info.get("config_files", {})
        if config_files:
            configs_with_unit_info = []
            for file_name, file_info in config_files.items():
                if isinstance(file_info, dict) and file_info.get("has_unit_info") == True:
                    configs_with_unit_info.append(file_name)
            
            if configs_with_unit_info:
                lw.WriteLine(f"    发现 {len(configs_with_unit_info)} 个配置文件包含单位信息")
                # 只进行简要解析，不输出详细内容
                parsed_configs = parse_config_files(config_files)
                if "error" in parsed_configs:
                    lw.WriteLine(f"    解析错误: {parsed_configs['error']}")
                else:
                    display_settings = parsed_configs.get("display_unit_settings", [])
                    if display_settings:
                        lw.WriteLine(f"    找到 {len(display_settings)} 个显示单位设置")
                    else:
                        lw.WriteLine(f"    未找到明确的显示单位设置")
            else:
                lw.WriteLine("    未找到包含单位信息的配置文件")
        else:
            lw.WriteLine("    未找到配置文件")
    
    lw.WriteLine(f"\n{'='*60}")
    lw.WriteLine("开始处理零件文件")
    lw.WriteLine(f"{'='*60}")
    
    for prt_file in prt_files:
        prt_path = os.path.join(folder_path, prt_file)
        
        try:
            # 打开零件文件
            lw.WriteLine(f"\n>>> 处理文件: {prt_file}")
            open_result = the_session.Parts.OpenBaseDisplay(prt_path)
            work_part = open_result[0]
            
            # 使用Convert方法检测显示单位
            lw.WriteLine(f"\n    === 单位检测 ===")
            detected_unit, conversion_result, method_used = detect_display_unit_with_convert(work_part)
            lw.WriteLine(f"    检测到的显示单位: {detected_unit}")
            lw.WriteLine(f"    检测方法: {method_used}")
            
            # 获取显示单位信息（保留GetBase的结果用于比较）
            unit_name_getbase, volume_factor_getbase, area_factor_getbase = get_display_unit_info(work_part)
            lw.WriteLine(f"    GetBase方法检测单位: {unit_name_getbase}")
            
            # 比较两种方法的检测结果
            if detected_unit != unit_name_getbase:
                lw.WriteLine(f"    注意: 两种方法检测结果不一致 - Convert方法: {detected_unit}, GetBase方法: {unit_name_getbase}")
            
            # 根据Convert方法的结果来确定单位和转换系数
            if detected_unit == "毫米":
                unit_name = "毫米"
                length_factor = 0.001      # mm -> m
                area_factor = 1e-6         # mm² -> m²
                volume_factor = 1e-9       # mm³ -> m³
            elif detected_unit == "米":
                unit_name = "米"
                length_factor = 1.0        # m -> m
                area_factor = 1.0          # m² -> m²
                volume_factor = 1.0        # m³ -> m³
            elif detected_unit == "英寸":
                unit_name = "英寸"
                length_factor = 0.0254     # inch -> m
                area_factor = 6.4516e-4    # inch² -> m²
                volume_factor = 1.6387e-5  # inch³ -> m³
            else:
                # 如果Convert方法无法检测，则使用GetBase方法的结果
                lw.WriteLine(f"    使用GetBase方法的结果作为默认值")
                unit_name = unit_name_getbase
                length_factor = volume_factor_getbase  # 这里复用GetBase的转换系数
                area_factor = area_factor_getbase
                volume_factor = volume_factor_getbase
            
            # 获取单位集合
            uc = work_part.UnitCollection
            units = [
                uc.GetBase("面积"),
                uc.GetBase("体积"),
                uc.GetBase("质量"),
                uc.GetBase("长度")
            ]
            
            measure_manager = work_part.MeasureManager
            
            # 获取所有实体
            bodies = get_all_bodies(work_part, uf_session)
            lw.WriteLine(f"\n    找到 {len(bodies)} 个实体")
            
            # 已在前面获取了单位信息，直接使用
            lw.WriteLine(f"    使用检测到的显示单位: {unit_name}")
            lw.WriteLine(f"    体积转换系数: {volume_factor}")
            lw.WriteLine(f"    面积转换系数: {area_factor}")
            
            total_volume_m3 = 0.0
            total_area_m2 = 0.0
            
            for i, body in enumerate(bodies):
                try:
                    # 获取质量属性
                    mass_props = measure_manager.NewMassProperties(units, 0.99, [body])
                    
                    # 获取原始值
                    volume_raw = mass_props.Volume
                    area_raw = mass_props.Area
                    
                    # 转换为标准单位 (m³ 和 m²)
                    volume_m3 = volume_raw * volume_factor
                    area_m2 = area_raw * area_factor
                    
                    lw.WriteLine(f"    实体 {i+1}:")
                    lw.WriteLine(f"      原始体积: {volume_raw:.6f} {unit_name}³")
                    lw.WriteLine(f"      原始面积: {area_raw:.6f} {unit_name}²")
                    lw.WriteLine(f"      转换后体积: {volume_m3:.6f} m³")
                    lw.WriteLine(f"      转换后面积: {area_m2:.6f} m²")
                    
                    total_volume_m3 += volume_m3
                    total_area_m2 += area_m2
                    
                except Exception as e:
                    lw.WriteLine(f"    实体 {i+1}: [错误] {e}")
            
            # 计算质量 (kg)
            total_mass = total_volume_m3 * density
            
            lw.WriteLine(f"\n    文件汇总:")
            lw.WriteLine(f"      实体数量: {len(bodies)}")
            lw.WriteLine(f"      总体积: {total_volume_m3:.6f} m³")
            lw.WriteLine(f"      总表面积: {total_area_m2:.6f} m²")
            lw.WriteLine(f"      计算质量: {total_mass:.4f} kg ({total_mass * 1000:.2f} g)")
            
            # 保存结果
            results.append({
                "file": prt_file,
                "unit": unit_name,
                "detection_method": method_used,
                "body_count": len(bodies),
                "volume_m3": total_volume_m3,
                "area_m2": total_area_m2,
                "mass_kg": total_mass
            })
            
            # 关闭零件 - 尝试不同的参数组合
            try:
                # 尝试使用枚举值
                the_session.Parts.CloseAll(NXOpen.BasePart.CloseModified.DoNotCloseModified, NXOpen.BasePart.CloseResponses.ProceedWithClose)
            except:
                try:
                    # 尝试使用整数值 1, 1
                    the_session.Parts.CloseAll(1, 1)
                except:
                    try:
                        # 尝试使用整数值 2, 2
                        the_session.Parts.CloseAll(2, 2)
                    except Exception as close_error:
                        lw.WriteLine(f"      关闭零件失败: {close_error}")
            
        except Exception as e:
            lw.WriteLine(f"    [错误] 无法处理文件: {e}")
    
    # 输出汇总
    lw.WriteLine("\n" + "=" * 60)
    lw.WriteLine("汇总结果")
    lw.WriteLine("=" * 60)
    lw.WriteLine(f"{'文件名':<30} {'单位':<8} {'检测方法':<12} {'表面积(m²)':<15} {'质量(kg)':<12}")
    lw.WriteLine("-" * 87)
    
    for r in results:
        file_name = r["file"][:28] if len(r["file"]) > 28 else r["file"]
        lw.WriteLine(f"{file_name:<30} {r['unit']:<8} {r['detection_method']:<12} {r['area_m2']:<15.4f} {r['mass_kg']:<12.4f}")
    
    lw.WriteLine("-" * 87)
    
    # 添加数值对比分析
    if len(results) == 2:
        lw.WriteLine("\n=== 数值对比分析 ===")
        r1, r2 = results[0], results[1]
        lw.WriteLine(f"文件1: {r1['file']}, 体积: {r1['volume_m3']:.6f} m³")
        lw.WriteLine(f"文件2: {r2['file']}, 体积: {r2['volume_m3']:.6f} m³")
        if r1['volume_m3'] > 0 and r2['volume_m3'] > 0:
            ratio = max(r1['volume_m3'], r2['volume_m3']) / min(r1['volume_m3'], r2['volume_m3'])
            lw.WriteLine(f"体积比值: {ratio:.2f}")
            if ratio > 1e6:  # 如果比值很大
                lw.WriteLine(f"  分析: 比值很大 (~{ratio:.2e})，表明单位不一致")
                lw.WriteLine(f"  可能情况: 一个文件是米制，另一个是毫米制")
            else:
                lw.WriteLine(f"  分析: 比值接近 1，单位可能一致")
    
    lw.WriteLine("\n完成!")
    
    # 输出到文件
    output_file = os.path.join(folder_path, "mass_properties_output.txt")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("质量属性提取结果 v4.11 (精简版 + 最终单位检测)\n")
            f.write(f"密度: 7.85 g/cm³ (7850 kg/m³)\n")
            f.write("基于Convert方法的单位检测 + 质量属性提取\n")
            f.write("=" * 60 + "\n\n")
            
            # 添加数值对比分析
            if len(results) == 2:
                r1, r2 = results[0], results[1]
                f.write("=== 数值对比分析 ===\n")
                f.write(f"文件1: {r1['file']}, 体积: {r1['volume_m3']:.6f} m³\n")
                f.write(f"文件2: {r2['file']}, 体积: {r2['volume_m3']:.6f} m³\n")
                if r1['volume_m3'] > 0 and r2['volume_m3'] > 0:
                    ratio = max(r1['volume_m3'], r2['volume_m3']) / min(r1['volume_m3'], r2['volume_m3'])
                    f.write(f"体积比值: {ratio:.2f} (预期: 1.0 如果单位相同, ~1e9 如果米 vs 毫米)\n")
                f.write("\n")
            
            for r in results:
                f.write(f"文件: {r['file']}\n")
                f.write(f"  检测到的单位: {r['unit']}\n")
                f.write(f"  检测方法: {r['detection_method']}\n")
                f.write(f"  实体数量: {r['body_count']}\n")
                f.write(f"  体积: {r['volume_m3']:.6f} m³\n")
                f.write(f"  表面积: {r['area_m2']:.6f} m²\n")
                f.write(f"  质量: {r['mass_kg']:.4f} kg ({r['mass_kg'] * 1000:.2f} g)\n")
                f.write("\n")
        lw.WriteLine(f"\n结果已保存到: {output_file}")
    except Exception as e:
        lw.WriteLine(f"[警告] 无法保存输出文件: {e}")
    
    lw.WriteLine("\n" + "=" * 60)
    lw.WriteLine("重要说明:")
    lw.WriteLine("1. 使用 GetBase() 获取显示单位，但可能不反映UI设置变化")
    lw.WriteLine("2. 根据 JournalIdentifier 判断单位类型")
    lw.WriteLine("3. 使用 Convert() 方法检测实际显示单位")
    lw.WriteLine("4. 数值差异表明 NX 返回的单位可能与 GetBase() 报告的不一致")
    lw.WriteLine("5. 探索 UF API 以寻找获取实际显示单位的方法")
    lw.WriteLine("6. 检查环境信息和执行信息")
    lw.WriteLine("7. v4.11新增：精简输出，集成Convert方法检测显示单位")
    lw.WriteLine("8. v4.10新增：完整显示Convert实验详情，添加Unit对象Convert实验和方法签名信息输出")
    lw.WriteLine("9. v4.9新增：改进Convert方法推断逻辑，分析所有成功实验的结果")
    lw.WriteLine("10. v4.8新增：实验 Convert() 方法参数，尝试通过单位转换检测显示单位")
    lw.WriteLine("=" * 60)

if __name__ == '__main__':
    main()