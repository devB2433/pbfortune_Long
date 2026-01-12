#!/bin/bash

# 数据备份和恢复管理脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DB_FILE="data/trading_plans.db"
BACKUP_DIR="data/backups"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

case "$1" in
    backup)
        # 备份数据库
        if [ ! -f "$DB_FILE" ]; then
            echo -e "${RED}错误: 数据库文件不存在: $DB_FILE${NC}"
            exit 1
        fi
        
        BACKUP_FILE="$BACKUP_DIR/trading_plans_$(date +%Y%m%d_%H%M%S).db"
        cp "$DB_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓ 数据已备份到: $BACKUP_FILE${NC}"
        
        # 清理旧备份（保留最近10个）
        cd "$BACKUP_DIR"
        ls -t trading_plans_*.db 2>/dev/null | tail -n +11 | xargs -r rm
        cd ../..
        echo -e "${GREEN}✓ 已清理旧备份（保留最近10个）${NC}"
        ;;
        
    list)
        # 列出所有备份
        echo -e "${YELLOW}可用备份列表:${NC}"
        if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
            ls -lh "$BACKUP_DIR"/trading_plans_*.db | awk '{print NR". "$9" ("$5")"}'
        else
            echo "没有找到任何备份文件"
        fi
        ;;
        
    restore)
        # 恢复数据库
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定备份文件名${NC}"
            echo "用法: $0 restore <备份文件名>"
            echo "示例: $0 restore trading_plans_20260112_143000.db"
            exit 1
        fi
        
        RESTORE_FILE="$BACKUP_DIR/$2"
        if [ ! -f "$RESTORE_FILE" ]; then
            echo -e "${RED}错误: 备份文件不存在: $RESTORE_FILE${NC}"
            exit 1
        fi
        
        # 在恢复前先备份当前数据
        if [ -f "$DB_FILE" ]; then
            CURRENT_BACKUP="$BACKUP_DIR/before_restore_$(date +%Y%m%d_%H%M%S).db"
            cp "$DB_FILE" "$CURRENT_BACKUP"
            echo -e "${GREEN}✓ 当前数据已备份到: $CURRENT_BACKUP${NC}"
        fi
        
        # 恢复数据
        cp "$RESTORE_FILE" "$DB_FILE"
        echo -e "${GREEN}✓ 数据已从 $2 恢复${NC}"
        
        # 如果使用 Docker，需要重启容器
        if docker ps | grep -q pbfortune_app; then
            echo -e "${YELLOW}重启 Docker 容器以应用更改...${NC}"
            docker-compose restart
            echo -e "${GREEN}✓ 容器已重启${NC}"
        fi
        ;;
        
    auto)
        # 自动备份（用于定时任务）
        if [ ! -f "$DB_FILE" ]; then
            exit 0
        fi
        
        BACKUP_FILE="$BACKUP_DIR/auto_$(date +%Y%m%d_%H%M%S).db"
        cp "$DB_FILE" "$BACKUP_FILE"
        
        # 清理7天前的自动备份
        find "$BACKUP_DIR" -name "auto_*.db" -mtime +7 -delete
        ;;
        
    *)
        echo "股票交易计划系统 - 数据备份管理工具"
        echo ""
        echo "用法:"
        echo "  $0 backup              - 创建数据库备份"
        echo "  $0 list                - 列出所有备份"
        echo "  $0 restore <文件名>    - 从备份恢复数据库"
        echo "  $0 auto                - 自动备份（用于定时任务）"
        echo ""
        echo "示例:"
        echo "  $0 backup"
        echo "  $0 list"
        echo "  $0 restore trading_plans_20260112_143000.db"
        echo ""
        echo "设置自动备份（每天凌晨2点）："
        echo "  (crontab -l 2>/dev/null; echo \"0 2 * * * cd $(pwd) && ./backup.sh auto\") | crontab -"
        exit 1
        ;;
esac
