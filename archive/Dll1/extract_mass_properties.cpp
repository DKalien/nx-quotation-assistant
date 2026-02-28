// extract_mass_properties.cpp
// NXOpen C++ 程序 - 提取文件夹内 .prt 文件的质量和表面积
// 密度设置: 7.85 g/cm^3 = 7850 kg/m^3
// 此文件需要与 NX Open C++ 库链接

#include "pch.h"
#include <string>
#include <vector>
#include <algorithm>
#include <windows.h>  // For Windows API functions

// NX Open 头文件
#include <NXOpen/NXOpen.hxx>
#include <NXOpen/Part.hxx>
#include <NXOpen/PartCollection.hxx>
#include <NXOpen/Body.hxx>
#include <NXOpen/BodyCollection.hxx>
#include <NXOpen/MeasureManager.hxx>
#include <NXOpen/UnitCollection.hxx>
#include <NXOpen/Unit.hxx>
#include <NXOpen/ListingWindow.hxx>
#include <NXOpen/Session.hxx>

using namespace NXOpen;
using namespace std;

// 密度常数: 7.85 g/cm^3 = 7850 kg/m^3
const double DENSITY_KG_PER_M3 = 7850.0;

// 单位转换因子
struct UnitFactors
{
    string unitName;      // 单位名称
    double lengthFactor;  // 长度转换因子 (显示单位 -> 米)
    double areaFactor;    // 面积转换因子 (显示单位^2 -> 米^2)
    double volumeFactor;  // 体积转换因子 (显示单位^3 -> 米^3)
};

// 获取部件的显示单位信息
UnitFactors GetDisplayUnitFactors(Part* part)
{
    UnitFactors factors;
    factors.unitName = "未知";
    factors.lengthFactor = 0.001;  // 默认假设毫米
    factors.areaFactor = 1e-6;
    factors.volumeFactor = 1e-9;

    try
    {
        UnitCollection* unitCollection = part->UnitCollection();
        
        // 获取长度单位
        Unit* lengthUnit = unitCollection->GetBase("长度");
        string journalId = lengthUnit->JournalIdentifier();
        
        // 根据标识符判断单位
        if (journalId.find("MilliMeter") != string::npos)
        {
            factors.unitName = "毫米";
            factors.lengthFactor = 0.001;      // mm -> m
            factors.areaFactor = 1e-6;         // mm^2 -> m^2
            factors.volumeFactor = 1e-9;       // mm^3 -> m^3
        }
        else if (journalId.find("Meter") != string::npos)
        {
            factors.unitName = "米";
            factors.lengthFactor = 1.0;        // m -> m
            factors.areaFactor = 1.0;          // m^2 -> m^2
            factors.volumeFactor = 1.0;        // m^3 -> m^3
        }
        else if (journalId.find("Inch") != string::npos)
        {
            factors.unitName = "英寸";
            factors.lengthFactor = 0.0254;     // inch -> m
            factors.areaFactor = 6.4516e-4;    // inch^2 -> m^2
            factors.volumeFactor = 1.6387e-5;  // inch^3 -> m^3
        }
        else if (journalId.find("Foot") != string::npos)
        {
            factors.unitName = "英尺";
            factors.lengthFactor = 0.3048;     // foot -> m
            factors.areaFactor = 0.092903;     // ft^2 -> m^2
            factors.volumeFactor = 0.0283168;  // ft^3 -> m^3
        }
    }
    catch (exception& e)
    {
        // 如果获取单位失败，使用默认值（毫米）
        factors.unitName = "默认（毫米）";
    }
    
    return factors;
}

// 获取部件中所有实体
vector<Body*> GetAllBodies(Part* part)
{
    vector<Body*> bodies;
    
    try
    {
        BodyCollection* bodyCollection = part->Bodies();
        int count = bodyCollection->GetSize();
        
        for (int i = 0; i < count; i++)
        {
            Body* body = bodyCollection->GetItem(i);
            if (body != nullptr)
            {
                bodies.push_back(body);
            }
        }
    }
    catch (exception& e)
    {
        // 如果通过常规方法失败，尝试使用 ToArray
        try
        {
            BodyCollection* bodyCollection = part->Bodies();
            Body** bodyArray = bodyCollection->ToArray();
            int count = bodyCollection->GetSize();
            
            for (int i = 0; i < count; i++)
            {
                bodies.push_back(bodyArray[i]);
            }
            
            delete[] bodyArray;
        }
        catch (exception& e2)
        {
            throw runtime_error("无法获取实体");
        }
    }
    
    return bodies;
}

// 计算部件的质量和表面积
void CalculateMassProperties(Part* part, double densityKgPerM3, 
                             double& totalMassKg, double& totalSurfaceAreaM2, 
                             string& unitName, double& volumeM3)
{
    totalMassKg = 0.0;
    totalSurfaceAreaM2 = 0.0;
    volumeM3 = 0.0;
    
    // 获取显示单位信息
    UnitFactors factors = GetDisplayUnitFactors(part);
    unitName = factors.unitName;
    
    // 获取所有实体
    vector<Body*> bodies = GetAllBodies(part);
    
    if (bodies.empty())
    {
        return;
    }
    
    // 获取测量管理器
    MeasureManager* measureMgr = part->MeasureManager();
    
    // 计算所有实体的总质量属性
    try
    {
        // 创建质量属性对象
        MassProperties* massProps = measureMgr->NewMassProperties(bodies);
        
        // 获取体积（显示单位^3）
        double volumeDisplayUnits = massProps->Volume();
        
        // 转换为立方米
        volumeM3 = volumeDisplayUnits * factors.volumeFactor;
        
        // 计算质量（kg）= 体积（m^3）× 密度（kg/m^3）
        totalMassKg = volumeM3 * densityKgPerM3;
        
        // 获取表面积（显示单位^2）
        double surfaceAreaDisplayUnits = massProps->SurfaceArea();
        
        // 转换为平方米
        totalSurfaceAreaM2 = surfaceAreaDisplayUnits * factors.areaFactor;
        
        // 释放资源
        delete massProps;
    }
    catch (exception& e)
    {
        // 如果 NewMassProperties 失败，尝试逐个实体计算
        totalMassKg = 0.0;
        totalSurfaceAreaM2 = 0.0;
        volumeM3 = 0.0;
        
        for (Body* body : bodies)
        {
            try
            {
                vector<Body*> singleBody = { body };
                MassProperties* bodyProps = measureMgr->NewMassProperties(singleBody);
                
                double bodyVolume = bodyProps->Volume() * factors.volumeFactor;
                double bodySurfaceArea = bodyProps->SurfaceArea() * factors.areaFactor;
                
                volumeM3 += bodyVolume;
                totalSurfaceAreaM2 += bodySurfaceArea;
                
                delete bodyProps;
            }
            catch (exception& bodyE)
            {
                // 跳过无法计算的实体
                continue;
            }
        }
        
        totalMassKg = volumeM3 * densityKgPerM3;
    }
}

// 获取文件夹中所有 .prt 文件（使用 Windows API）
vector<string> GetPrtFilesInFolder(const string& folderPath)
{
    vector<string> prtFiles;
    
    WIN32_FIND_DATAA findData;
    HANDLE hFind;
    
    // 搜索模式: 所有 .prt 文件
    string searchPath = folderPath + "\\*.prt";
    
    hFind = FindFirstFileA(searchPath.c_str(), &findData);
    if (hFind == INVALID_HANDLE_VALUE)
    {
        // 尝试搜索 .PRT（大写）
        searchPath = folderPath + "\\*.PRT";
        hFind = FindFirstFileA(searchPath.c_str(), &findData);
        
        if (hFind == INVALID_HANDLE_VALUE)
        {
            return prtFiles; // 空向量
        }
    }
    
    do
    {
        // 跳过目录
        if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY))
        {
            string fileName = findData.cFileName;
            string filePath = folderPath + "\\" + fileName;
            prtFiles.push_back(filePath);
        }
    } while (FindNextFileA(hFind, &findData) != 0);
    
    FindClose(hFind);
    
    return prtFiles;
}

// NX Open 入口函数
extern "C" __declspec(dllexport) void ufusr(char* param, int* retcode, int paramLen)
{
    *retcode = 0;
    
    try
    {
        Session* session = Session::GetSession();
        ListingWindow* lw = session->ListingWindow();
        
        lw->Open();
        lw->WriteLine("=== NX 质量属性提取器 (C++ 版本) ===");
        lw->WriteLine("密度: 7.85 g/cm^3 = 7850 kg/m^3");
        lw->WriteLine("");
        
        // 获取当前工作目录
        char currentDir[MAX_PATH];
        GetCurrentDirectoryA(MAX_PATH, currentDir);
        string folderPath = currentDir;
        
        lw->WriteLine("扫描文件夹: " + folderPath);
        
        // 获取所有 .prt 文件
        vector<string> prtFiles = GetPrtFilesInFolder(folderPath);
        
        if (prtFiles.empty())
        {
            lw->WriteLine("未找到 .prt 文件。");
            lw->WriteLine("请将 .prt 文件放在当前目录: " + folderPath);
            return;
        }
        
        lw->WriteLine("找到 " + to_string(prtFiles.size()) + " 个 .prt 文件:");
        for (const string& file : prtFiles)
        {
            // 提取文件名
            size_t lastSlash = file.find_last_of("\\/");
            string fileName = (lastSlash != string::npos) ? file.substr(lastSlash + 1) : file;
            lw->WriteLine("  - " + fileName);
        }
        lw->WriteLine("");
        
        // 处理每个文件
        PartCollection* partCollection = session->Parts();
        
        for (const string& filePath : prtFiles)
        {
            try
            {
                // 提取文件名用于显示
                size_t lastSlash = filePath.find_last_of("\\/");
                string fileName = (lastSlash != string::npos) ? filePath.substr(lastSlash + 1) : filePath;
                
                lw->WriteLine("处理文件: " + fileName);
                
                // 打开部件
                PartLoadStatus* loadStatus = nullptr;
                Part* part = partCollection->OpenBasePart(filePath.c_str(), 
                                                          PartCollection::PartCloseWholeTreeFalse,
                                                          PartCollection::PartCloseModifiedCloseModified,
                                                          &loadStatus);
                
                if (part == nullptr)
                {
                    lw->WriteLine("  错误: 无法打开部件");
                    continue;
                }
                
                // 计算质量属性
                double totalMassKg = 0.0;
                double totalSurfaceAreaM2 = 0.0;
                string unitName;
                double volumeM3 = 0.0;
                
                CalculateMassProperties(part, DENSITY_KG_PER_M3, 
                                        totalMassKg, totalSurfaceAreaM2, 
                                        unitName, volumeM3);
                
                // 输出结果
                lw->WriteLine("  单位系统: " + unitName);
                lw->WriteLine("  体积: " + to_string(volumeM3) + " m^3");
                lw->WriteLine("  质量: " + to_string(totalMassKg) + " kg");
                lw->WriteLine("  表面积: " + to_string(totalSurfaceAreaM2) + " m^2");
                
                // 转换为常用单位
                double massGrams = totalMassKg * 1000.0;
                double surfaceAreaCm2 = totalSurfaceAreaM2 * 10000.0;
                
                lw->WriteLine("  质量: " + to_string(massGrams) + " g");
                lw->WriteLine("  表面积: " + to_string(surfaceAreaCm2) + " cm^2");
                lw->WriteLine("");
                
                // 关闭部件
                part->Close(BasePart::CloseWholeTreeFalse, 
                           BasePart::CloseModifiedCloseModified);
                
                if (loadStatus != nullptr)
                {
                    delete loadStatus;
                }
            }
            catch (exception& e)
            {
                lw->WriteLine("  错误处理文件: " + string(e.what()));
                lw->WriteLine("");
            }
        }
        
        lw->WriteLine("=== 处理完成 ===");
    }
    catch (exception& e)
    {
        try
        {
            Session* session = Session::GetSession();
            ListingWindow* lw = session->ListingWindow();
            lw->WriteLine("致命错误: " + string(e.what()));
        }
        catch (...)
        {
            // 如果连 ListingWindow 都不可用，则无法报告错误
        }
        *retcode = 1;
    }
}