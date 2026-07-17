@echo off
echo ========================================
echo 工作日报助手 - 打包脚本
echo ========================================
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 激活conda环境
echo [1/4] 激活conda环境...
call C:\Users\20057\miniconda3\envs\deeplearning\activate.bat

REM 清理旧的构建文件
echo [2/4] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "work_daily.spec" del /q "work_daily.spec"

REM 执行打包
echo [3/4] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller ^
    --name "工作日报助手" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "UI/styles.qss;UI" ^
    --add-data "UI/main_window.ui;UI" ^
    --hidden-import "PyQt5" ^
    --hidden-import "PyQt5.QtWidgets" ^
    --hidden-import "PyQt5.QtCore" ^
    --hidden-import "PyQt5.QtGui" ^
    --hidden-import "qfluentwidgets" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "mss" ^
    --hidden-import "ollama" ^
    --hidden-import "csv" ^
    --hidden-import "json" ^
    --hidden-import "base64" ^
    UI/main_fluent.py

echo.
echo [4/4] 打包完成!
echo.

if exist "dist\工作日报助手\工作日报助手.exe" (
    echo 打包成功！
    echo 可执行文件位置: dist\工作日报助手\工作日报助手.exe
    echo.
    echo 正在复制数据文件...
    
    REM 复制data文件夹
    if not exist "dist\工作日报助手\data" mkdir "dist\工作日报助手\data"
    if exist "data\*.csv" copy /y "data\*.csv" "dist\工作日报助手\data\" >nul
    if exist "data\config.txt" copy /y "data\config.txt" "dist\工作日报助手\data\" >nul
    
    echo 复制完成！
    echo.
    echo ========================================
    echo 打包成功完成！
    echo 请查看 dist\工作日报助手 文件夹
    echo ========================================
) else (
    echo 打包失败，请检查错误信息。
)

pause
