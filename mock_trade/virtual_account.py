"""
Virtual Account - Mock Trading Account Management
虚拟账户 - 模拟交易账户管理
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """成本"""
        return self.quantity * self.avg_price
    
    @property
    def unrealized_pnl(self) -> float:
        """未实现盈亏"""
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """未实现盈亏百分比"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


@dataclass
class Trade:
    """交易记录"""
    trade_id: int
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float
    timestamp: datetime
    order_type: str = 'MARKET'  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT
    
    @property
    def total_value(self) -> float:
        """交易总额(含手续费)"""
        base_value = self.quantity * self.price
        if self.action == 'BUY':
            return base_value + self.commission
        else:
            return base_value - self.commission


class VirtualAccount:
    """虚拟交易账户"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.next_trade_id = 1
        
    @property
    def total_market_value(self) -> float:
        """总市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_equity(self) -> float:
        """总权益(现金+持仓市值)"""
        return self.cash + self.total_market_value
    
    @property
    def total_pnl(self) -> float:
        """总盈亏"""
        return self.total_equity - self.initial_capital
    
    @property
    def total_pnl_pct(self) -> float:
        """总盈亏百分比"""
        return (self.total_pnl / self.initial_capital) * 100
    
    def buy(
        self, 
        symbol: str, 
        quantity: int, 
        price: float, 
        commission: float = 0.0,
        order_type: str = 'MARKET'
    ) -> bool:
        """
        买入股票
        
        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格
            commission: 手续费
            order_type: 订单类型
            
        Returns:
            是否成功
        """
        total_cost = (quantity * price) + commission
        
        if total_cost > self.cash:
            logger.warning(f"Insufficient funds: need ${total_cost:.2f}, have ${self.cash:.2f}")
            return False
        
        # 扣除资金
        self.cash -= total_cost
        
        # 更新持仓
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos.quantity + quantity
            total_cost_basis = (pos.quantity * pos.avg_price) + (quantity * price)
            pos.quantity = total_qty
            pos.avg_price = total_cost_basis / total_qty
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price
            )
        
        # 记录交易
        trade = Trade(
            trade_id=self.next_trade_id,
            symbol=symbol,
            action='BUY',
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now(),
            order_type=order_type
        )
        self.trades.append(trade)
        self.next_trade_id += 1
        
        logger.info(f"BUY {quantity} {symbol} @ ${price:.2f}, Total: ${total_cost:.2f}")
        return True
    
    def sell(
        self, 
        symbol: str, 
        quantity: int, 
        price: float, 
        commission: float = 0.0,
        order_type: str = 'MARKET'
    ) -> bool:
        """
        卖出股票
        
        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格
            commission: 手续费
            order_type: 订单类型
            
        Returns:
            是否成功
        """
        if symbol not in self.positions:
            logger.warning(f"No position for {symbol}")
            return False
        
        pos = self.positions[symbol]
        if pos.quantity < quantity:
            logger.warning(f"Insufficient shares: have {pos.quantity}, need {quantity}")
            return False
        
        # 增加资金
        proceeds = (quantity * price) - commission
        self.cash += proceeds
        
        # 更新持仓
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]
        
        # 记录交易
        trade = Trade(
            trade_id=self.next_trade_id,
            symbol=symbol,
            action='SELL',
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now(),
            order_type=order_type
        )
        self.trades.append(trade)
        self.next_trade_id += 1
        
        logger.info(f"SELL {quantity} {symbol} @ ${price:.2f}, Proceeds: ${proceeds:.2f}")
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """
        更新持仓的当前价格
        
        Args:
            prices: {symbol: current_price}
        """
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.current_price = prices[symbol]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_summary(self) -> Dict:
        """获取账户摘要"""
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'market_value': self.total_market_value,
            'total_equity': self.total_equity,
            'total_pnl': self.total_pnl,
            'total_pnl_pct': self.total_pnl_pct,
            'num_positions': len(self.positions),
            'num_trades': len(self.trades)
        }
    
    def get_positions_list(self) -> List[Dict]:
        """获取持仓列表"""
        return [
            {
                **asdict(pos),
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl_pct,
                'market_value': pos.market_value,
                'cost_basis': pos.cost_basis
            }
            for pos in self.positions.values()
        ]
    
    def get_trades_history(self, limit: int = 50) -> List[Dict]:
        """获取交易历史"""
        recent_trades = self.trades[-limit:]
        return [
            {
                **asdict(trade),
                'timestamp': trade.timestamp.isoformat()
            }
            for trade in recent_trades
        ]
