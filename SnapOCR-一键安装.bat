@echo off
chcp 65001 >nul 2>&1
title SnapOCR 截图识别 - 一键安装
color 0F
setlocal EnableDelayedExpansion

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║                                               ║
echo  ║       SnapOCR 截图识别 - 一键安装             ║
echo  ║                                               ║
echo  ║   免费本地截图OCR · 翻译 · 高亮标注          ║
echo  ║   无需登录  无需API  完全离线可用             ║
echo  ║                                               ║
echo  ╚═══════════════════════════════════════════════╝
echo.
echo  本程序将自动安装:
echo.
echo    [1] 检查/安装 Python
echo    [2] 安装 SnapOCR 及所有依赖
echo    [3] 创建桌面快捷方式
echo.
echo  全程自动，等待即可。
echo.
echo  ═══════════════════════════════════════════════════
echo   按任意键开始安装...
echo  ═══════════════════════════════════════════════════
pause >nul

set "INSTALL_DIR=%LOCALAPPDATA%\SnapOCR"
set "SCRIPT_DIR=%~dp0"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM ═══════════════════════════════════════
REM  第1步: 检查 Python
REM ═══════════════════════════════════════
echo.
echo  ─────────────────────────────────────
echo   [1/3] 检查 Python 环境
echo  ─────────────────────────────────────

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!] 未检测到 Python，正在自动下载安装...
    echo.

    set "PY_INSTALLER=%TEMP%\python-installer.exe"

    echo  正在下载 Python 安装包...
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe' -OutFile '!PY_INSTALLER!' }"

    if not exist "!PY_INSTALLER!" (
        echo.
        echo  [X] Python 下载失败!
        echo      请手动下载: https://www.python.org/downloads/
        echo      安装时勾选 "Add Python to PATH"
        echo      安装完成后重新运行本程序
        pause
        exit /b 1
    )

    echo  正在安装 Python...
    start /wait "" "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del "!PY_INSTALLER!" 2>nul

    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"

    python --version >nul 2>&1
    if errorlevel 1 (
        echo  [X] Python 安装可能需要重启电脑
        echo      请重启后重新运行本安装程序
        pause
        exit /b 1
    )
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYVER=%%a
echo  [OK] Python %PYVER%

REM ═══════════════════════════════════════
REM  第2步: 安装 SnapOCR
REM ═══════════════════════════════════════
echo.
echo  ─────────────────────────────────────
echo   [2/3] 安装 SnapOCR 及依赖
echo  ─────────────────────────────────────
echo.
echo  正在复制程序文件...
xcopy /E /Y /I /Q "%SCRIPT_DIR%snapocr" "%INSTALL_DIR%\snapocr" >nul 2>&1
copy /Y "%SCRIPT_DIR%pyproject.toml" "%INSTALL_DIR%\" >nul 2>&1

echo  正在安装依赖（首次约需2-3分钟）...
echo.

pip install rapidocr-onnxruntime Pillow PyQt6 pynput numpy -q 2>nul

if errorlevel 1 (
    echo  [!] 部分依赖安装遇到问题，正在重试...
    pip install rapidocr-onnxruntime -q 2>nul
    pip install Pillow PyQt6 pynput numpy -q 2>nul
)

echo  [OK] SnapOCR 安装完成

REM ═══════════════════════════════════════
REM  第3步: 创建快捷方式
REM ═══════════════════════════════════════
echo.
echo  ─────────────────────────────────────
echo   [3/3] 创建快捷方式
echo  ─────────────────────────────────────

REM 创建 .pyw 启动器（无控制台窗口）
(
echo import sys, os
echo if sys.stdout is None or not hasattr(sys.stdout, "write"):
echo     sys.stdout = open(os.devnull, "w")
echo if sys.stderr is None or not hasattr(sys.stderr, "write"):
echo     sys.stderr = open(os.devnull, "w")
echo sys.path.insert(0, r"%INSTALL_DIR%")
echo from snapocr.gui.app import run_gui
echo run_gui()
) > "%INSTALL_DIR%\SnapOCR.pyw"

REM 创建桌面快捷方式
powershell -Command "& { $WshShell = New-Object -ComObject WScript.Shell; $Desktop = [Environment]::GetFolderPath('Desktop'); $Shortcut = $WshShell.CreateShortcut(\"$Desktop\SnapOCR 截图识别.lnk\"); $Shortcut.TargetPath = '%INSTALL_DIR%\SnapOCR.pyw'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'SnapOCR - 免费截图OCR工具'; $Shortcut.WindowStyle = 7; $Shortcut.Save(); Write-Host '  [OK] 桌面快捷方式已创建' }"

REM ═══════════════════════════════════════
REM  安装完成
REM ═══════════════════════════════════════
echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║                                               ║
echo  ║            安装完成!                           ║
echo  ║                                               ║
echo  ╚═══════════════════════════════════════════════╝
echo.
echo  使用方法:
echo.
echo    1. 双击桌面「SnapOCR 截图识别」图标
echo    2. 按 F4 截取屏幕任意区域
echo    3. 自动识别文字，可翻译、高亮标注
echo.
echo  功能列表:
echo.
echo    截图识别   按 F4 框选区域，自动识别文字
echo    表格识别   识别表格结构，输出整齐格式
echo    翻译       识别后一键翻译为英语/日语等
echo    高亮标注   在截图上画框，突出重点区域
echo    从文件     直接打开图片文件识别
echo.
echo  关闭窗口 = 缩小到右下角托盘，不会退出。
echo  右键托盘图标可以快捷操作或退出。
echo.
echo  ═══════════════════════════════════════════════════
echo   按任意键关闭安装程序...
echo  ═══════════════════════════════════════════════════
pause >nul
