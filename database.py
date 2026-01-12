#!/usr/bin/env python3
"""
Database operations for trading plans
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class TradingPlanDB:
    def __init__(self, db_path='data/trading_plans.db'):
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
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_symbol TEXT NOT NULL,
                    stock_name TEXT,
                    plan_content TEXT NOT NULL,
                    spot_plan TEXT,
                    option_plan TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    conversation_id TEXT,
                    version INTEGER DEFAULT 1,
                    is_starred INTEGER DEFAULT 0
                )
            ''')
            
            # Create index for faster queries
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_stock_symbol 
                ON trading_plans(stock_symbol, created_at DESC)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_starred 
                ON trading_plans(is_starred DESC, created_at DESC)
            ''')
    
    def save_plan(self, stock_symbol, stock_name, plan_content, 
                  spot_plan=None, option_plan=None, conversation_id=None):
        """Save a new trading plan with version control"""
        with self.get_connection() as conn:
            # Get the latest version for this stock
            cursor = conn.execute('''
                SELECT MAX(version) FROM trading_plans 
                WHERE stock_symbol = ?
            ''', (stock_symbol,))
            result = cursor.fetchone()
            next_version = (result[0] or 0) + 1
            
            cursor = conn.execute('''
                INSERT INTO trading_plans 
                (stock_symbol, stock_name, plan_content, spot_plan, option_plan, conversation_id, version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                stock_symbol,
                stock_name,
                plan_content,
                json.dumps(spot_plan) if spot_plan else None,
                json.dumps(option_plan) if option_plan else None,
                conversation_id,
                next_version
            ))
            return cursor.lastrowid
    
    def get_all_plans(self, status='active'):
        """Get all trading plans"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trading_plans 
                WHERE status = ?
                ORDER BY created_at DESC
            ''', (status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_plan_by_id(self, plan_id):
        """Get a specific trading plan"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trading_plans WHERE id = ?
            ''', (plan_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_plan(self, plan_id, **kwargs):
        """Update a trading plan"""
        allowed_fields = ['stock_symbol', 'stock_name', 'plan_content', 
                         'spot_plan', 'option_plan', 'status']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                if key in ['spot_plan', 'option_plan'] and value:
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not updates:
            return False
        
        values.append(plan_id)
        query = f"UPDATE trading_plans SET {', '.join(updates)} WHERE id = ?"
        
        with self.get_connection() as conn:
            conn.execute(query, values)
            return True
    
    def delete_plan(self, plan_id):
        """Delete a trading plan"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM trading_plans WHERE id = ?', (plan_id,))
            return True
    
    def get_plan_versions(self, stock_symbol):
        """Get all versions of a stock's trading plans"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trading_plans 
                WHERE stock_symbol = ?
                ORDER BY version DESC
            ''', (stock_symbol,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_latest_plans(self, status='active'):
        """Get only the latest version of each stock's plan, starred first"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT t1.* FROM trading_plans t1
                INNER JOIN (
                    SELECT stock_symbol, MAX(version) as max_version
                    FROM trading_plans
                    WHERE status = ?
                    GROUP BY stock_symbol
                ) t2 ON t1.stock_symbol = t2.stock_symbol 
                     AND t1.version = t2.max_version
                ORDER BY t1.is_starred DESC, t1.created_at DESC
            ''', (status,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def toggle_star(self, plan_id):
        """Toggle star status of a plan"""
        with self.get_connection() as conn:
            # Get current star status
            cursor = conn.execute('SELECT is_starred FROM trading_plans WHERE id = ?', (plan_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            new_status = 0 if row[0] else 1
            conn.execute('UPDATE trading_plans SET is_starred = ? WHERE id = ?', (new_status, plan_id))
            return new_status
    
    def search_plans(self, keyword):
        """Search trading plans by stock symbol or name"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM trading_plans 
                WHERE stock_symbol LIKE ? OR stock_name LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{keyword}%', f'%{keyword}%'))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
