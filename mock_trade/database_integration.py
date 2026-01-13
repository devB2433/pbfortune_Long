"""
Database Integration for Mock Trading
模拟交易数据库集成
"""

import sys
import os
import re
import logging
from typing import List, Dict, Optional, Tuple

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import TradingPlanDB

logger = logging.getLogger(__name__)


class TradingPlanLoader:
    """交易计划加载器"""
    
    def __init__(self, db_path='data/trading_plans.db'):
        self.db = TradingPlanDB(db_path)
    
    def get_trading_plans(self, max_count: int = 10) -> List[Dict]:
        """
        获取交易计划
        优先选择 starred 的股票,然后是 tracking_status='active' 的
        
        Args:
            max_count: 最多返回的股票数量
            
        Returns:
            交易计划列表
        """
        # 获取最新的计划
        all_plans = self.db.get_latest_plans(status='active')
        
        # 过滤:只要 tracking_status='active' 的
        active_plans = [
            plan for plan in all_plans 
            if plan.get('tracking_status') == 'active'
        ]
        
        # 排序:starred 优先
        active_plans.sort(key=lambda x: x.get('is_starred', 0), reverse=True)
        
        # 限制数量
        selected_plans = active_plans[:max_count]
        
        logger.info(f"Loaded {len(selected_plans)} trading plans from database")
        for plan in selected_plans:
            starred = "⭐" if plan.get('is_starred') else ""
            logger.info(f"  {starred} {plan['stock_symbol']} - {plan['stock_name']}")
        
        return selected_plans
    
    def parse_trading_conditions(self, plan_content: str) -> Optional[Dict[str, float]]:
        """
        从交易计划内容中解析买入价、止损、止盈
        
        Args:
            plan_content: 计划内容文本
            
        Returns:
            {
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float
            }
            如果解析失败返回 None
        """
        conditions = {}
        
        # 匹配模式: 
        # 买入价 XXX
        # 止损价 XXX
        # 止盈价 XXX
        
        # 买入价
        entry_match = re.search(r'买入价[：:\s]+(\d+(?:\.\d+)?)', plan_content)
        if entry_match:
            conditions['entry_price'] = float(entry_match.group(1))
        
        # 止损价
        stop_loss_match = re.search(r'止损价[：:\s]+(\d+(?:\.\d+)?)', plan_content)
        if stop_loss_match:
            conditions['stop_loss'] = float(stop_loss_match.group(1))
        
        # 止盈价
        take_profit_match = re.search(r'止盈价[：:\s]+(\d+(?:\.\d+)?)', plan_content)
        if take_profit_match:
            conditions['take_profit'] = float(take_profit_match.group(1))
        
        # 如果没有找到买入价,尝试其他模式
        if 'entry_price' not in conditions:
            # 尝试: 价格：XXX (买入)
            alt_match = re.search(r'价格[：:\s]+(\d+(?:\.\d+)?)[^\n]*买入', plan_content)
            if alt_match:
                conditions['entry_price'] = float(alt_match.group(1))
        
        # 必须至少有买入价才算有效
        if 'entry_price' not in conditions or conditions['entry_price'] == 0:
            logger.warning(f"Could not parse entry price from plan")
            return None
        
        # 如果没有止损/止盈,使用默认值(基于买入价)
        if 'stop_loss' not in conditions:
            conditions['stop_loss'] = conditions['entry_price'] * 0.95  # -5%
            logger.info(f"Using default stop loss: {conditions['stop_loss']:.2f} (-5%)")
        
        if 'take_profit' not in conditions:
            conditions['take_profit'] = conditions['entry_price'] * 1.10  # +10%
            logger.info(f"Using default take profit: {conditions['take_profit']:.2f} (+10%)")
        
        return conditions
    
    def load_trading_strategies(self, max_count: int = 10) -> List[Dict]:
        """
        加载交易策略
        
        Returns:
            [
                {
                    'symbol': str,
                    'name': str,
                    'entry_price': float,
                    'stop_loss': float,
                    'take_profit': float,
                    'plan_id': int
                }
            ]
        """
        plans = self.get_trading_plans(max_count)
        strategies = []
        
        for plan in plans:
            conditions = self.parse_trading_conditions(plan['plan_content'])
            
            if conditions:
                strategy = {
                    'symbol': plan['stock_symbol'],
                    'name': plan['stock_name'],
                    'entry_price': conditions['entry_price'],
                    'stop_loss': conditions['stop_loss'],
                    'take_profit': conditions['take_profit'],
                    'plan_id': plan['id'],
                    'is_starred': plan.get('is_starred', 0)
                }
                strategies.append(strategy)
                
                starred = "⭐" if strategy['is_starred'] else ""
                logger.info(
                    f"{starred} {strategy['symbol']}: "
                    f"Entry ${strategy['entry_price']:.2f}, "
                    f"SL ${strategy['stop_loss']:.2f}, "
                    f"TP ${strategy['take_profit']:.2f}"
                )
            else:
                logger.warning(
                    f"Skipping {plan['stock_symbol']} - could not parse trading conditions"
                )
        
        return strategies
