#!/usr/bin/env bash
# 出行决策 Agent — 首次使用初始化（Git Bash / macOS / Linux）
# 用法：在项目目录执行  bash 一键初始化.sh

set -u
cd "$(dirname "$0")"
PROJ="$(pwd)"

echo "=========================================================="
echo "  出行决策 Agent — 首次使用初始化"
echo "  项目目录: $PROJ"
echo "=========================================================="
echo

# ---------- 1. git 安全目录（exFAT 盘无文件属主，git 默认拒绝） ----------
if command -v git >/dev/null 2>&1; then
  git config --global --add safe.directory "$PROJ"
  echo "[1/5] 已登记 git 安全目录（解决 dubious ownership 报错）"
else
  echo "[1/5] 未检测到 Git，请先安装: https://git-scm.com/install/windows"
fi

# ---------- 2. 检测 Python ----------
PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "[2/5] 未检测到 Python，请安装 Python 3.10+"
else
  echo "[2/5] 检测到 Python: $($PY --version 2>&1)"
fi

# ---------- 3. 虚拟环境 + Python 依赖 ----------
if [ -n "$PY" ]; then
  if [ -x ".venv/Scripts/python.exe" ]; then
    VENV_PY=".venv/Scripts/python.exe"        # Windows
  elif [ -x ".venv/bin/python" ]; then
    VENV_PY=".venv/bin/python"                # macOS / Linux
  else
    VENV_PY=""
  fi

  if [ -z "$VENV_PY" ]; then
    echo "[3/5] 正在创建虚拟环境 .venv ..."
    "$PY" -m venv .venv || true
    if [ -x ".venv/Scripts/python.exe" ]; then VENV_PY=".venv/Scripts/python.exe"
    elif [ -x ".venv/bin/python" ]; then VENV_PY=".venv/bin/python"; fi
  else
    echo "[3/5] .venv 已存在，跳过创建"
  fi

  if [ -n "$VENV_PY" ]; then
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r requirements.txt \
      && echo "      Python 依赖安装完成" \
      || echo "      ! Python 依赖安装失败，请检查网络或代理后重试"
  fi
fi

# ---------- 4. 前端依赖 ----------
if ! command -v npm >/dev/null 2>&1; then
  echo "[4/5] 未检测到 Node.js，请安装 Node.js 18+: https://nodejs.org/"
elif [ -d node_modules ]; then
  echo "[4/5] node_modules 已存在，跳过安装"
else
  echo "[4/5] 正在安装前端依赖 ..."
  npm install
fi

# ---------- 5. .env ----------
if [ -f .env ]; then
  echo "[5/5] .env 已存在，未覆盖"
else
  cp .env.example .env
  echo "[5/5] 已由 .env.example 生成 .env"
fi

cat <<'EOF'

==========================================================
  初始化结束。接下来你需要做两件事:

  1) 打开 .env，填入你自己的两个 Key:
       AI_GATEWAY_API_KEY  <- EdgeOne Makers 控制台 / 模型与密钥
       AMAP_API_KEY        <- 高德开放平台 / 应用管理 / Web服务 Key

  2) 启动本地服务（需先登录腾讯云账号）:
       npm i -g edgeone
       edgeone login
       edgeone makers dev

  详细步骤见: 课程复现操作手册.md
==========================================================
EOF
