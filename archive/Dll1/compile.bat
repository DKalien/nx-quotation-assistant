@echo off
chcp 65001 >nul
echo ========================================
echo    NX Open C++ 程序编译助手
echo ========================================
echo.

REM 检查是否在正确目录
if not exist "Dll1.vcxproj" (
    echo 错误：请在包含 Dll1.vcxproj 的目录中运行此脚本。
    echo 当前目录：%cd%
    pause
    exit /b 1
)

echo 步骤1：检查 Visual Studio 安装...
echo.

REM 尝试查找 MSBuild
set MSBUILD_PATH=
where msbuild >nul 2>&1
if %errorlevel% equ 0 (
    echo 找到 MSBuild（在 PATH 中）
    set MSBUILD_PATH=msbuild
) else (
    REM 尝试常见路径
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH="C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
        echo 找到 MSBuild 2022 Community
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH="C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"
        echo 找到 MSBuild 2022 Professional
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
        set MSBUILD_PATH="C:\Program Files\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
        echo 找到 MSBuild 2019 Community
    ) else if exist "C:\Program Files\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe" (
        set MSBUILD_PATH="C:\Program Files\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
        echo 找到 MSBuild 2017 Community
    ) else (
        echo 未找到 MSBuild，请确保已安装 Visual Studio。
        echo.
        echo 建议使用 Visual Studio 打开 Dll1.vcxproj 手动编译。
        echo 请查看 README_编译说明.txt 获取详细步骤。
        pause
        exit /b 1
    )
)

echo.
echo 步骤2：检查 NX 安装...
echo.

REM 检查环境变量
if not "%UGII_BASE_DIR%"=="" (
    echo 找到 NX 环境变量 UGII_BASE_DIR: %UGII_BASE_DIR%
) else (
    echo 未设置 UGII_BASE_DIR 环境变量。
    echo 将使用默认路径：C:\Program Files\Siemens\NX 12.0
    echo 如果 NX 安装在其他位置，请手动设置 UGII_BASE_DIR。
)

echo.
echo 步骤3：选择编译配置...
echo.

set /p PLATFORM="选择平台 (1=x64, 2=Win32, 默认=x64): "
if "%PLATFORM%"=="1" set PLATFORM=x64
if "%PLATFORM%"=="2" set PLATFORM=Win32
if "%PLATFORM%"=="" set PLATFORM=x64
if not "%PLATFORM%"=="x64" if not "%PLATFORM%"=="Win32" set PLATFORM=x64

echo 使用平台: %PLATFORM%
echo 使用配置: Release

echo.
echo 步骤4：开始编译...
echo.

echo 执行命令：%MSBUILD_PATH% Dll1.vcxproj /p:Configuration=Release /p:Platform=%PLATFORM%
echo.

%MSBUILD_PATH% Dll1.vcxproj /p:Configuration=Release /p:Platform=%PLATFORM%

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   编译成功！
    echo ========================================
    echo.
    echo 生成的 DLL 文件在：%PLATFORM%\Release\Dll1.dll
    echo.
    echo 使用方法：
    echo 1. 将 Dll1.dll 复制到任意目录
    echo 2. 在 NX 中：File -> Execute -> NX Open
    echo 3. 选择 Dll1.dll
    echo 4. 点击 OK
    echo.
    echo 程序将扫描当前文件夹内的所有 .prt 文件。
) else (
    echo.
    echo ========================================
    echo   编译失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. Visual Studio 版本不兼容
    echo 2. NX 开发环境未安装
    echo 3. NX 安装路径不正确
    echo.
    echo 建议：
    echo 1. 使用 Visual Studio 打开 Dll1.vcxproj 手动编译
    echo 2. 检查 nxopen.props 文件中的 NX 安装路径
    echo 3. 查看 README_编译说明.txt 获取更多帮助
)

echo.
pause