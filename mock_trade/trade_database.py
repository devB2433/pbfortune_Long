"""
Trade Database for Mock Trading
模拟交易数据库持久化
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TradeDatabase:
    """交易数据库管理"""
    
    def __init__(self, db_path='data/mock_trades.db'):
        self.db_path = db_path
        # 确保数据目录存在
        import os
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            # 交易记录表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    commission REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    plan_id INTEGER,
                    notes TEXT
                )
            ''')
            
            # 持仓快照表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS position_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    unrealized_pnl REAL,
                    unrealized_pnl_pct REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 账户快照表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS account_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash REAL NOT NULL,
                    market_value REAL NOT NULL,
                    total_equity REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    total_pnl_pct REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 监控日志表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitor_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    log_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                ON trades(symbol, timestamp DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
                ON trades(timestamp DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_monitor_logs_timestamp 
                ON monitor_logs(timestamp DESC)
            ''')
    
    def save_trade(
        self, 
        symbol: str, 
        action: str, 
        quantity: int, 
        price: float,
        commission: float = 0,
        plan_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        保存交易记录
        
        Args:
            symbol: 股票代码
            action: BUY 或 SELL
            quantity: 数量
            price: 价格
            commission: 手续费
            plan_id: 关联的交易计划ID
            notes: 备注
            
        Returns:
            交易记录ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO trades 
                (symbol, action, quantity, price, commission, plan_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, action, quantity, price, commission, plan_id, notes))
            
            trade_id = cursor.lastrowid
            logger.info(
                f"Saved trade: {action} {quantity} {symbol} @ ${price:.2f} "
                f"(ID: {trade_id})"
            )
            return trade_id
    
    def get_all_trades(self, limit: int = 100) -> List[Dict]:
        """获取所有交易记录"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trades 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict]:
        """获取指定股票的交易记录"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trades 
                WHERE symbol = ?
                ORDER BY timestamp DESC
            ''', (symbol,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def save_position_snapshot(
        self,
        symbol: str,
        quantity: int,
        avg_price: float,
        current_price: float,
        unrealized_pnl: float,
        unrealized_pnl_pct: float
    ):
        """保存持仓快照"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO position_snapshots
                (symbol, quantity, avg_price, current_price, 
                 unrealized_pnl, unrealized_pnl_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol, quantity, avg_price, current_price,
                unrealized_pnl, unrealized_pnl_pct
            ))
    
    def save_account_snapshot(
        self,
        cash: float,
        market_value: float,
        total_equity: float,
        total_pnl: float,
        total_pnl_pct: float
    ):
        """保存账户快照"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO account_snapshots
                (cash, market_value, total_equity, total_pnl, total_pnl_pct)
                VALUES (?, ?, ?, ?, ?)
            ''', (cash, market_value, total_equity, total_pnl, total_pnl_pct))
    
    def get_latest_account_snapshot(self) -> Optional[Dict]:
        """获取最新的账户快照"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM account_snapshots 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_account_history(self, limit: int = 100) -> List[Dict]:
        """获取账户历史快照"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM account_snapshots 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_account_snapshots(self, limit: int = 30, time_range: str = None) -> List[Dict]:
        """获取账户快照(按时间正序)
        
        Args:
            limit: 最大返回数量
            time_range: 时间范围 ('all' | None)
        """
        with self.get_connection() as conn:
            if time_range == 'all':
                # 获取所有数据（不限制limit）
                cursor = conn.execute('''
                    SELECT timestamp, total_equity 
                    FROM account_snapshots 
                    ORDER BY timestamp ASC
                ''')
            else:
                # 默认：最近N条
                cursor = conn.execute('''
                    SELECT timestamp, total_equity 
                    FROM account_snapshots 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trading_stats(self) -> Dict:
        """获取交易统计"""
        with self.get_connection() as conn:
            # 总交易次数
            cursor = conn.execute('SELECT COUNT(*) as total FROM trades')
            total_trades = cursor.fetchone()[0]
            
            # 买入次数
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM trades WHERE action = 'BUY'"
            )
            buy_count = cursor.fetchone()[0]
            
            # 卖出次数
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM trades WHERE action = 'SELL'"
            )
            sell_count = cursor.fetchone()[0]
            
            # 总手续费
            cursor = conn.execute('SELECT SUM(commission) as total FROM trades')
            total_commission = cursor.fetchone()[0] or 0
            
            # 交易的股票数量
            cursor = conn.execute('SELECT COUNT(DISTINCT symbol) as total FROM trades')
            unique_symbols = cursor.fetchone()[0]
            
            return {
                'total_trades': total_trades,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'total_commission': total_commission,
                'unique_symbols': unique_symbols
            }
    
    def save_monitor_log(self, message: str, log_type: str = 'info'):
        """
        保存监控日志
        
        Args:
            message: 日志消息
            log_type: 日志类型 (info/success/warning/error/trade)
        """
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO monitor_logs (message, log_type)
                VALUES (?, ?)
            ''', (message, log_type))
    
    def get_monitor_logs(self, limit: int = 50) -> List[Dict]:
        """
        获取监控日志
        
        Args:
            limit: 返回条数
        
        Returns:
            list: 日志列表
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:%M:%S', timestamp) as timestamp,
                    message,
                    log_type as type
                FROM monitor_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            # 按时间正序返回（最旧的在前）
            return [dict(row) for row in reversed(rows)]
