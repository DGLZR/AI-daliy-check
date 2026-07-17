@echo off
echo 正在启动工作日报助手 (Fluent Design版)...
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 使用deeplearning环境的Python直接运行
"C:\Users\20057\miniconda3\envs\deeplearning\python.exe" "UI\main_fluent.py"

REM 如果程序退出，暂停查看输出
pause
