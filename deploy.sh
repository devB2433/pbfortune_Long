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

# 1. 检查 Docker
echo -e "${YELLOW}[1/5] 检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}✓ Docker 安装完成${NC}"
else
    echo -e "${GREEN}✓ Docker 已安装${NC}"
fi

# 2. 检查 docker-compose
echo -e "${YELLOW}[2/5] 检查 Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose 未安装，正在安装...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose 安装完成${NC}"
else
    echo -e "${GREEN}✓ Docker Compose 已安装${NC}"
fi

# 3. 配置文件
echo -e "${YELLOW}[3/5] 检查配置文件...${NC}"
if [ ! -f "config.yaml" ]; then
    cp config.yaml.example config.yaml
    echo -e "${YELLOW}请编辑 config.yaml 文件，填入你的密码和 Dify URL${NC}"
    echo -e "${YELLOW}按任意键继续...${NC}"
    read -n 1 -s
fi
echo -e "${GREEN}✓ 配置文件已就绪${NC}"

# 4. 创建 Dockerfile
echo -e "${YELLOW}[4/5] 创建 Dockerfile...${NC}"
cat > Dockerfile <<'EOF'
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8888

# 启动应用
CMD ["python", "app.py"]
EOF
echo -e "${GREEN}✓ Dockerfile 创建完成${NC}"

# 5. 创建 docker-compose.yml
cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  pbfortune:
    build: .
    container_name: pbfortune_app
    restart: always
    ports:
      - "8888:8888"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
EOF
echo -e "${GREEN}✓ docker-compose.yml 创建完成${NC}"

# 6. 创建数据目录
mkdir -p data

# 7. 部署
echo -e "${YELLOW}[5/5] 部署应用...${NC}"
if [ "$(docker ps -aq -f name=pbfortune_app)" ]; then
    echo "停止旧容器..."
    docker-compose down
fi

echo "构建镜像..."
docker-compose build

echo "启动应用..."
docker-compose up -d

sleep 5

# 8. 检查状态
if docker ps | grep -q pbfortune_app; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✓ 部署成功！"
    echo "==========================================${NC}"
    echo ""
    echo "应用信息："
    echo "  - 容器名称: pbfortune_app"
    echo "  - 监听端口: 8888"
    echo "  - 访问地址: http://localhost:8888"
    echo ""
    echo "常用命令："
    echo "  查看日志: docker-compose logs -f"
    echo "  重启应用: docker-compose restart"
    echo "  停止应用: docker-compose down"
    echo "  更新应用: git pull && docker-compose up -d --build"
    echo ""
    echo "数据库文件位置: ./data/trading_plans.db"
    echo ""
else
    echo -e "${RED}部署失败，请检查日志：${NC}"
    docker-compose logs
    exit 1
fi
