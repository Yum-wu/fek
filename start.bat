@echo off

title FEK 本地启动器

cd /d "%~dp0"

set "PY="

where python >nul 2>&1 && set "PY=python"

if not defined PY where py >nul 2>&1 && set "PY=py"

if not defined PY set "PY=C:\Users\Yum\.workbuddy\binaries\python\versions\3.13.12\python.exe"

if not defined PY (
  echo [错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH，或编辑本脚本里的 PY 路径。
  pause
  exit /b 1
)

echo 已选定 Python 解释器：
%PY% --version

:menu
cls
echo ============================================
echo   FEK 本地启动器
echo ============================================
echo  [1] 基础 Demo  —— 离线运行，零依赖（推荐先跑这个）
echo  [2] 对战 Demo  —— 离线运行，三策略成本/质量对比
echo  [3] Web 界面   —— 浏览器可视化（自动安装 streamlit）
echo  [4] 运行测试   —— 零依赖 unittest
echo  [0] 退出
echo ============================================
set /p CHOICE=请选择 [1-4 / 0]：

if "%CHOICE%"=="1" goto DEMO
if "%CHOICE%"=="2" goto BATTLE
if "%CHOICE%"=="3" goto WEB
if "%CHOICE%"=="4" goto TEST
if "%CHOICE%"=="0" exit /b 0

echo 无效输入，请重试。
goto menu

:DEMO
echo.
echo 运行基础 Demo（mock 模式，离线）...
%PY% examples/basic_demo.py
echo.
pause
goto menu

:BATTLE
echo.
echo 运行对战 Demo（mock 模式，离线）...
%PY% examples/battle_demo.py
echo.
pause
goto menu

:WEB
echo.
echo 检查 streamlit（首次安装可能稍慢）...
%PY% -m pip install -q streamlit
echo 启动 Web 界面，浏览器将自动打开（默认 http://localhost:8501）...
echo 按 Ctrl+C 停止。
%PY% -m streamlit run web/app.py
echo.
pause
goto menu

:TEST
echo.
echo 运行测试套件（零依赖）...
%PY% -m unittest discover -s tests -v
echo.
pause
goto menu
