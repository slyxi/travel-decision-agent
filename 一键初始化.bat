@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   出行决策 Agent  -  首次使用初始化
echo   项目目录: %CD%
echo ==========================================================
echo.

rem ---------- 1. git 安全目录（exFAT 盘无文件属主，git 默认拒绝） ----------
where git >nul 2>nul
if errorlevel 1 (
    echo [1/5] 未检测到 Git。请先安装: https://git-scm.com/install/windows
) else (
    git config --global --add safe.directory "%CD%"
    git config --global --add safe.directory "%CD%/.venv" 2>nul
    echo [1/5] 已登记 git 安全目录  ^(解决 "dubious ownership" 报错^)
)

rem ---------- 2. 检测 Python ----------
set "PY="
py -3 --version >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python --version >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo [2/5] 未检测到 Python。请安装 Python 3.10+ 并在安装时勾选 "Add Python to PATH"
    goto :skip_python
)
echo [2/5] 检测到 Python:
%PY% --version

rem ---------- 3. 虚拟环境 + Python 依赖 ----------
if exist ".venv\Scripts\python.exe" (
    echo [3/5] .venv 已存在，跳过创建
) else (
    echo [3/5] 正在创建虚拟环境 .venv ...
    %PY% -m venv .venv
)
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo       ^! Python 依赖安装失败，请检查网络或代理后重试
    ) else (
        echo       Python 依赖安装完成
    )
)

:skip_python

rem ---------- 4. 前端依赖 ----------
where npm >nul 2>nul
if errorlevel 1 (
    echo [4/5] 未检测到 Node.js。请安装 Node.js 18+ : https://nodejs.org/
) else (
    if exist "node_modules" (
        echo [4/5] node_modules 已存在，跳过安装
    ) else (
        echo [4/5] 正在安装前端依赖 ...
        call npm install
    )
)

rem ---------- 5. .env ----------
if exist ".env" (
    echo [5/5] .env 已存在，未覆盖
) else (
    copy /y ".env.example" ".env" >nul
    echo [5/5] 已由 .env.example 生成 .env
)

echo.
echo ==========================================================
echo   初始化结束。接下来你需要做两件事:
echo.
echo   1) 用记事本打开 .env，填入你自己的两个 Key:
echo        AI_GATEWAY_API_KEY  ^<- EdgeOne Makers 控制台 / 模型与密钥
echo        AMAP_API_KEY        ^<- 高德开放平台 / 应用管理 / Web服务 Key
echo.
echo   2) 启动本地服务（需先登录腾讯云账号）:
echo        npm i -g edgeone
echo        edgeone login
echo        edgeone makers dev
echo.
echo   详细步骤见: 课程复现操作手册.md
echo ==========================================================
echo.
pause
