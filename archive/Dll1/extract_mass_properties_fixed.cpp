// extract_mass_properties.cpp
// NXOpen C++ Program - Extract mass and surface area of .prt files in folder
// Density: 7.85 g/cm^3 = 7850 kg/m^3
// This file needs to be linked with NX Open C++ libraries

#include "pch.h"
#include <string>
#include <vector>
#include <algorithm>
#include <windows.h>  // For Windows API functions

// NX Open headers
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

// Density constant: 7.85 g/cm^3 = 7850 kg/m^3
const double DENSITY_KG_PER_M3 = 7850.0;

// Unit conversion factors
struct UnitFactors
{
    string unitName;      // Unit name
    double lengthFactor;  // Length conversion factor (display unit -> meter)
    double areaFactor;    // Area conversion factor (display unit^2 -> m^2)
    double volumeFactor;  // Volume conversion factor (display unit^3 -> m^3)
};

// Get display unit information of a part
UnitFactors GetDisplayUnitFactors(NXOpen::Part* part)
{
    UnitFactors factors;
    factors.unitName = "Unknown";
    factors.lengthFactor = 0.001;  // Default assume millimeters
    factors.areaFactor = 1e-6;
    factors.volumeFactor = 1e-9;

    try
    {
        UnitCollection* unitCollection = part->UnitCollection();
        
        // Get length unit
        Unit* lengthUnit = unitCollection->GetBase("Length");
        string journalId = lengthUnit->JournalIdentifier();
        
        // Determine unit based on identifier
        if (journalId.find("MilliMeter") != string::npos)
        {
            factors.unitName = "Millimeter";
            factors.lengthFactor = 0.001;      // mm -> m
            factors.areaFactor = 1e-6;         // mm^2 -> m^2
            factors.volumeFactor = 1e-9;       // mm^3 -> m^3
        }
        else if (journalId.find("Meter") != string::npos)
        {
            factors.unitName = "Meter";
            factors.lengthFactor = 1.0;        // m -> m
            factors.areaFactor = 1.0;          // m^2 -> m^2
            factors.volumeFactor = 1.0;        // m^3 -> m^3
        }
        else if (journalId.find("Inch") != string::npos)
        {
            factors.unitName = "Inch";
            factors.lengthFactor = 0.0254;     // inch -> m
            factors.areaFactor = 6.4516e-4;    // inch^2 -> m^2
            factors.volumeFactor = 1.6387e-5;  // inch^3 -> m^3
        }
        else if (journalId.find("Foot") != string::npos)
        {
            factors.unitName = "Foot";
            factors.lengthFactor = 0.3048;     // foot -> m
            factors.areaFactor = 0.092903;     // ft^2 -> m^2
            factors.volumeFactor = 0.0283168;  // ft^3 -> m^3
        }
    }
    catch (exception& e)
    {
        // If failed to get unit, use default (millimeters)
        factors.unitName = "Default (mm)";
    }
    
    return factors;
}

// Get all bodies in a part
vector<NXOpen::Body*> GetAllBodies(NXOpen::Part* part)
{
    vector<NXOpen::Body*> bodies;
    
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
        // If regular method fails, try using ToArray
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
            throw runtime_error("Cannot get bodies");
        }
    }
    
    return bodies;
}

// Calculate mass properties of a part
void CalculateMassProperties(NXOpen::Part* part, double densityKgPerM3, 
                             double& totalMassKg, double& totalSurfaceAreaM2, 
                             string& unitName, double& volumeM3)
{
    totalMassKg = 0.0;
    totalSurfaceAreaM2 = 0.0;
    volumeM3 = 0.0;
    
    // Get display unit information
    UnitFactors factors = GetDisplayUnitFactors(part);
    unitName = factors.unitName;
    
    // Get all bodies
    vector<NXOpen::Body*> bodies = GetAllBodies(part);
    
    if (bodies.empty())
    {
        return;
    }
    
    // Get measure manager
    MeasureManager* measureMgr = part->MeasureManager();
    
    // Calculate total mass properties of all bodies
    try
    {
        // Create mass properties object
        MassProperties* massProps = measureMgr->NewMassProperties(bodies);
        
        // Get volume (display units^3)
        double volumeDisplayUnits = massProps->Volume();
        
        // Convert to cubic meters
        volumeM3 = volumeDisplayUnits * factors.volumeFactor;
        
        // Calculate mass (kg) = volume (m^3) * density (kg/m^3)
        totalMassKg = volumeM3 * densityKgPerM3;
        
        // Get surface area (display units^2)
        double surfaceAreaDisplayUnits = massProps->SurfaceArea();
        
        // Convert to square meters
        totalSurfaceAreaM2 = surfaceAreaDisplayUnits * factors.areaFactor;
        
        // Release resources
        delete massProps;
    }
    catch (exception& e)
    {
        // If NewMassProperties fails, try calculating body by body
        totalMassKg = 0.0;
        totalSurfaceAreaM2 = 0.0;
        volumeM3 = 0.0;
        
        for (NXOpen::Body* body : bodies)
        {
            try
            {
                vector<NXOpen::Body*> singleBody = { body };
                MassProperties* bodyProps = measureMgr->NewMassProperties(singleBody);
                
                double bodyVolume = bodyProps->Volume() * factors.volumeFactor;
                double bodySurfaceArea = bodyProps->SurfaceArea() * factors.areaFactor;
                
                volumeM3 += bodyVolume;
                totalSurfaceAreaM2 += bodySurfaceArea;
                
                delete bodyProps;
            }
            catch (exception& bodyE)
            {
                // Skip bodies that cannot be calculated
                continue;
            }
        }
        
        totalMassKg = volumeM3 * densityKgPerM3;
    }
}

// Get all .prt files in a folder (using Windows API)
vector<string> GetPrtFilesInFolder(const string& folderPath)
{
    vector<string> prtFiles;
    
    WIN32_FIND_DATAA findData;
    HANDLE hFind;
    
    // Search pattern: all .prt files
    string searchPath = folderPath + "\\*.prt";
    
    hFind = FindFirstFileA(searchPath.c_str(), &findData);
    if (hFind == INVALID_HANDLE_VALUE)
    {
        // Try searching for .PRT (uppercase)
        searchPath = folderPath + "\\*.PRT";
        hFind = FindFirstFileA(searchPath.c_str(), &findData);
        
        if (hFind == INVALID_HANDLE_VALUE)
        {
            return prtFiles; // Empty vector
        }
    }
    
    do
    {
        // Skip directories
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

// NX Open entry function
extern "C" __declspec(dllexport) void ufusr(char* param, int* retcode, int paramLen)
{
    *retcode = 0;
    
    try
    {
        Session* session = Session::GetSession();
        ListingWindow* lw = session->ListingWindow();
        
        lw->Open();
        lw->WriteLine("=== NX Mass Property Extractor (C++ Version) ===");
        lw->WriteLine("Density: 7.85 g/cm^3 = 7850 kg/m^3");
        lw->WriteLine("");
        
        // Get current working directory
        char currentDir[MAX_PATH];
        GetCurrentDirectoryA(MAX_PATH, currentDir);
        string folderPath = currentDir;
        
        lw->WriteLine("Scanning folder: " + folderPath);
        
        // Get all .prt files
        vector<string> prtFiles = GetPrtFilesInFolder(folderPath);
        
        if (prtFiles.empty())
        {
            lw->WriteLine("No .prt files found.");
            lw->WriteLine("Please place .prt files in current directory: " + folderPath);
            return;
        }
        
        lw->WriteLine("Found " + to_string(prtFiles.size()) + " .prt files:");
        for (const string& file : prtFiles)
        {
            // Extract filename
            size_t lastSlash = file.find_last_of("\\/");
            string fileName = (lastSlash != string::npos) ? file.substr(lastSlash + 1) : file;
            lw->WriteLine("  - " + fileName);
        }
        lw->WriteLine("");
        
        // Process each file
        PartCollection* partCollection = session->Parts();
        
        for (const string& filePath : prtFiles)
        {
            try
            {
                // Extract filename for display
                size_t lastSlash = filePath.find_last_of("\\/");
                string fileName = (lastSlash != string::npos) ? filePath.substr(lastSlash + 1) : filePath;
                
                lw->WriteLine("Processing file: " + fileName);
                
                // Open part
                PartLoadStatus* loadStatus = nullptr;
                Part* part = partCollection->OpenBasePart(filePath.c_str(), 
                                                          PartCollection::PartCloseWholeTreeFalse,
                                                          PartCollection::PartCloseModifiedCloseModified,
                                                          &loadStatus);
                
                if (part == nullptr)
                {
                    lw->WriteLine("  Error: Cannot open part");
                    continue;
                }
                
                // Calculate mass properties
                double totalMassKg = 0.0;
                double totalSurfaceAreaM2 = 0.0;
                string unitName;
                double volumeM3 = 0.0;
                
                CalculateMassProperties(part, DENSITY_KG_PER_M3, 
                                        totalMassKg, totalSurfaceAreaM2, 
                                        unitName, volumeM3);
                
                // Output results
                lw->WriteLine("  Unit system: " + unitName);
                lw->WriteLine("  Volume: " + to_string(volumeM3) + " m^3");
                lw->WriteLine("  Mass: " + to_string(totalMassKg) + " kg");
                lw->WriteLine("  Surface area: " + to_string(totalSurfaceAreaM2) + " m^2");
                
                // Convert to common units
                double massGrams = totalMassKg * 1000.0;
                double surfaceAreaCm2 = totalSurfaceAreaM2 * 10000.0;
                
                lw->WriteLine("  Mass: " + to_string(massGrams) + " g");
                lw->WriteLine("  Surface area: " + to_string(surfaceAreaCm2) + " cm^2");
                lw->WriteLine("");
                
                // Close part
                part->Close(BasePart::CloseWholeTreeFalse, 
                           BasePart::CloseModifiedCloseModified);
                
                if (loadStatus != nullptr)
                {
                    delete loadStatus;
                }
            }
            catch (exception& e)
            {
                lw->WriteLine("  Error processing file: " + string(e.what()));
                lw->WriteLine("");
            }
        }
        
        lw->WriteLine("=== Processing completed ===");
    }
    catch (exception& e)
    {
        try
        {
            Session* session = Session::GetSession();
            ListingWindow* lw = session->ListingWindow();
            lw->WriteLine("Fatal error: " + string(e.what()));
        }
        catch (...)
        {
            // If even ListingWindow is not available, cannot report error
        }
        *retcode = 1;
    }
}