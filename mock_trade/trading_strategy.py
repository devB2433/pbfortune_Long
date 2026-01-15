"""
Trading Strategy - Trading Signal Detection
交易策略 - 交易信号检测
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingCondition:
    """交易条件"""
    symbol: str
    entry_price: Optional[float] = None  # 买入价格
    stop_loss: Optional[float] = None    # 止损价格
    take_profit: Optional[float] = None  # 止盈价格
    quantity: int = 0                     # 持仓数量
    
    # 条件类型
    entry_condition: str = 'price'  # price, breakout, pullback
    exit_condition: str = 'fixed'   # fixed, trailing, percentage


class TradingStrategy:
    """交易策略引擎"""
    
    # 价格容差百分比（1%）
    PRICE_TOLERANCE = 0.01
    
    def __init__(self):
        self.conditions: Dict[str, TradingCondition] = {}
    
    def add_condition(self, condition: TradingCondition):
        """
        添加交易条件
        
        Args:
            condition: 交易条件对象
        """
        self.conditions[condition.symbol] = condition
        logger.info(f"Added trading condition for {condition.symbol}")
    
    def remove_condition(self, symbol: str):
        """移除交易条件"""
        if symbol in self.conditions:
            del self.conditions[symbol]
            logger.info(f"Removed trading condition for {symbol}")
    
    def check_entry_signal(
        self, 
        symbol: str, 
        current_price: float
    ) -> Optional[str]:
        """
        检查买入信号
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            'BUY' 如果满足买入条件, 否则 None
        """
        if symbol not in self.conditions:
            return None
        
        condition = self.conditions[symbol]
        
        # 如果已有持仓,不再买入
        if condition.quantity > 0:
            return None
        
        # 检查买入条件
        if condition.entry_price is None:
            return None
        
        # 买入价格区间: 买入价 * (1 ± 1%)
        entry_lower = condition.entry_price * (1 - self.PRICE_TOLERANCE)
        entry_upper = condition.entry_price * (1 + self.PRICE_TOLERANCE)
        
        # 在买入价格区间内触发
        if entry_lower <= current_price <= entry_upper:
            logger.info(
                f"BUY signal for {symbol}: "
                f"current ${current_price:.2f} in range [${entry_lower:.2f}, ${entry_upper:.2f}] "
                f"(entry ${condition.entry_price:.2f} ±1%)"
            )
            return 'BUY'
        
        return None
    
    def check_exit_signal(
        self, 
        symbol: str, 
        current_price: float
    ) -> Optional[str]:
        """
        检查卖出信号
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            'SELL' 如果满足卖出条件, 否则 None
        """
        if symbol not in self.conditions:
            return None
        
        condition = self.conditions[symbol]
        
        # 如果没有持仓,无需卖出
        if condition.quantity == 0:
            return None
        
        # 检查止损: 止损价 * (1 ± 1%)
        if condition.stop_loss:
            stop_loss_lower = condition.stop_loss * (1 - self.PRICE_TOLERANCE)
            stop_loss_upper = condition.stop_loss * (1 + self.PRICE_TOLERANCE)
            
            if stop_loss_lower <= current_price <= stop_loss_upper:
                logger.warning(
                    f"STOP LOSS triggered for {symbol}: "
                    f"current ${current_price:.2f} in range [${stop_loss_lower:.2f}, ${stop_loss_upper:.2f}] "
                    f"(stop loss ${condition.stop_loss:.2f} ±1%)"
                )
                return 'SELL'
        
        # 检查止盈: 止盈价 * (1 ± 1%)
        if condition.take_profit:
            take_profit_lower = condition.take_profit * (1 - self.PRICE_TOLERANCE)
            take_profit_upper = condition.take_profit * (1 + self.PRICE_TOLERANCE)
            
            if take_profit_lower <= current_price <= take_profit_upper:
                logger.info(
                    f"TAKE PROFIT triggered for {symbol}: "
                    f"current ${current_price:.2f} in range [${take_profit_lower:.2f}, ${take_profit_upper:.2f}] "
                    f"(take profit ${condition.take_profit:.2f} ±1%)"
                )
                return 'SELL'
        
        return None
    
    def update_position(self, symbol: str, quantity: int):
        """
        更新持仓数量
        
        Args:
            symbol: 股票代码
            quantity: 新的持仓数量
        """
        if symbol in self.conditions:
            self.conditions[symbol].quantity = quantity
            logger.info(f"Updated position for {symbol}: {quantity} shares")
    
    def get_all_symbols(self) -> List[str]:
        """获取所有监控的股票代码"""
        return list(self.conditions.keys())
    
    def get_condition(self, symbol: str) -> Optional[TradingCondition]:
        """获取指定股票的交易条件"""
        return self.conditions.get(symbol)


def create_simple_strategy(
    symbol: str,
    entry_price: float,
    stop_loss_pct: float = 0.05,  # 5% 止损
    take_profit_pct: float = 0.10  # 10% 止盈
) -> TradingCondition:
    """
    创建简单的交易策略
    
    Args:
        symbol: 股票代码
        entry_price: 买入价格
        stop_loss_pct: 止损百分比 (默认5%)
        take_profit_pct: 止盈百分比 (默认10%)
        
    Returns:
        TradingCondition 对象
    """
    return TradingCondition(
        symbol=symbol,
        entry_price=entry_price,
        stop_loss=entry_price * (1 - stop_loss_pct),
        take_profit=entry_price * (1 + take_profit_pct),
        quantity=0
    )
