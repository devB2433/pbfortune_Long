#!/bin/bash

set -e

echo "=========================================="
echo "  PB Fortune 股票交易计划系统 - 部署脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 检查 Python3
echo -e "${YELLOW}[1/5] 检查 Python3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 未安装，正在安装...${NC}"
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
    echo -e "${GREEN}✓ Python3 安装完成${NC}"
else
    echo -e "${GREEN}✓ Python3 已安装 ($(python3 --version))${NC}"
fi

# 2. 创建虚拟环境
echo -e "${YELLOW}[2/5] 创建虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 3. 安装依赖
echo -e "${YELLOW}[3/5] 安装依赖...${NC}"
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 4. 配置文件
echo -e "${YELLOW}[4/5] 检查配置文件...${NC}"
if [ ! -f "config.yaml" ]; then
    cp config.yaml.example config.yaml
    echo -e "${YELLOW}请编辑 config.yaml 文件，填入你的密码和 Dify URL${NC}"
    echo -e "${YELLOW}按任意键继续...${NC}"
    read -n 1 -s
fi
echo -e "${GREEN}✓ 配置文件已就绪${NC}"

# 5. 创建数据目录
mkdir -p data

# 6. 停止旧进程
echo -e "${YELLOW}[5/5] 部署应用...${NC}"
if [ -f "app.pid" ]; then
    OLD_PID=$(cat app.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧进程 (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f app.pid
fi

# 7. 启动应用
echo "启动应用..."
source venv/bin/activate
nohup python3 app.py > logs/app.log 2>&1 &
echo $! > app.pid

# 8. 等待启动
sleep 3

# 9. 检查状态
if [ -f "app.pid" ] && ps -p $(cat app.pid) > /dev/null 2>&1; then
    PID=$(cat app.pid)
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✓ 部署成功！"
    echo "==========================================${NC}"
    echo ""
    echo "应用信息："
    echo "  - 进程 PID: $PID"
    echo "  - 监听端口: 8888"
    echo "  - 访问地址: http://localhost:8888"
    echo ""
    echo "常用命令："
    echo "  查看日志: tail -f logs/app.log"
    echo "  停止应用: kill \$(cat app.pid)"
    echo "  重启应用: ./deploy.sh"
    echo "  更新应用: git pull && ./deploy.sh"
    echo ""
    echo "数据库文件位置: ./data/trading_plans.db"
    echo ""
else
    echo -e "${RED}部署失败，请检查日志：${NC}"
    tail -n 50 logs/app.log
    exit 1
fi
