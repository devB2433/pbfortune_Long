"""
Trading Monitor - Automated Trading Monitoring Service
交易监控器 - 自动化交易监控服务
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from typing import Optional
import logging

from market_data import MarketDataProvider
from virtual_account import VirtualAccount
from trading_strategy import TradingStrategy, TradingCondition
from database_integration import TradingPlanLoader
from trade_database import TradeDatabase
from config import (
    INITIAL_CAPITAL, 
    MONITOR_INTERVAL_SECONDS, 
    COMMISSION_RATE,
    MAX_POSITION_SIZE,
    MAX_STOCKS
)

logger = logging.getLogger(__name__)


class TradingMonitor:
    """交易监控器"""
    
    def __init__(self):
        self.account = VirtualAccount(INITIAL_CAPITAL)
        self.strategy = TradingStrategy()
        self.market_data = MarketDataProvider()
        self.db_loader = TradingPlanLoader()
        self.trade_db = TradeDatabase()
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        # 恢复持仓状态
        self._restore_positions()
        
        logger.info("Trading Monitor initialized")
    
    def add_log(self, message: str, log_type: str = 'info'):
        """
        添加监控日志（写入数据库）
        
        Args:
            message: 日志消息
            log_type: 日志类型 (info/success/warning/error/trade)
        """
        try:
            self.trade_db.save_monitor_log(message, log_type)
        except Exception as e:
            logger.error(f"Failed to save monitor log: {e}")
    
    def get_logs(self, limit: int = 50):
        """
        获取监控日志（从数据库读取）
        
        Args:
            limit: 返回条数
        
        Returns:
            list: 日志列表
        """
        try:
            return self.trade_db.get_monitor_logs(limit)
        except Exception as e:
            logger.error(f"Failed to get monitor logs: {e}")
            return []
    
    def _restore_positions(self):
        """从数据库恢复持仓状态"""
        try:
            # 获取所有交易记录
            trades = self.trade_db.get_all_trades(limit=1000)
            
            if not trades:
                logger.info("没有历史交易记录")
                return
            
            # 计算每个股票的持仓
            positions_data = {}  # symbol -> {'qty': int, 'total_cost': float}
            total_commission = 0
            
            for trade in reversed(trades):  # 从早到晚处理
                symbol = trade['symbol']
                action = trade['action']
                qty = trade['quantity']
                price = trade['price']
                commission = trade.get('commission', 0)
                total_commission += commission
                
                if symbol not in positions_data:
                    positions_data[symbol] = {'qty': 0, 'total_cost': 0}
                
                if action == 'BUY':
                    positions_data[symbol]['qty'] += qty
                    positions_data[symbol]['total_cost'] += qty * price
                elif action == 'SELL':
                    positions_data[symbol]['qty'] -= qty
                    # 卖出时按比例减少成本
                    if positions_data[symbol]['qty'] > 0:
                        avg_price = positions_data[symbol]['total_cost'] / (positions_data[symbol]['qty'] + qty)
                        positions_data[symbol]['total_cost'] -= qty * avg_price
                    else:
                        positions_data[symbol]['total_cost'] = 0
            
            # 清除空仓
            positions_data = {k: v for k, v in positions_data.items() if v['qty'] > 0}
            
            # 计算已用资金
            total_invested = sum(v['total_cost'] for v in positions_data.values()) + total_commission
            self.account.cash = INITIAL_CAPITAL - total_invested
            
            # 恢复持仓到账户
            for symbol, data in positions_data.items():
                if data['qty'] > 0:
                    avg_price = data['total_cost'] / data['qty']
                    # 获取当前价格
                    current_price = self.market_data.get_current_price(symbol)
                    if current_price is None:
                        current_price = avg_price  # fallback
                    
                    from virtual_account import Position
                    self.account.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=data['qty'],
                        avg_price=avg_price,
                        current_price=current_price
                    )
                    
                    # 更新策略中的持仓数量
                    condition = self.strategy.get_condition(symbol)
                    if condition:
                        condition.quantity = data['qty']
                    
                    logger.info(f"恢复持仓: {symbol} {data['qty']}股 @ ${avg_price:.2f}")
                    print(f"   📊 恢复持仓: {symbol} {data['qty']}股 @ ${avg_price:.2f}")
            
            if positions_data:
                print(f"   💰 剩余现金: ${self.account.cash:,.2f}")
                logger.info(f"持仓恢复完成: {len(positions_data)} 个持仓, 现金 ${self.account.cash:,.2f}")
        except Exception as e:
            logger.error(f"恢复持仓失败: {e}")
            print(f"   ⚠️  恢复持仓失败: {e}")
    
    def load_strategies_from_db(self):
        """从数据库加载交易策略"""
        logger.info("从数据库加载交易策略...")
        
        # 加载策略
        strategies = self.db_loader.load_trading_strategies(max_count=MAX_STOCKS)
        
        if not strategies:
            logger.warning("没有找到有效的交易计划")
            print("\n⚠️  数据库中没有有效的交易计划")
            return 0
        
        # 保存现有的持仓信息
        existing_positions = {}
        for symbol, condition in self.strategy.conditions.items():
            if condition.quantity > 0:
                existing_positions[symbol] = condition.quantity
        
        # 清空现有策略
        self.strategy.conditions.clear()
        
        # 添加新策略
        for strat in strategies:
            symbol = strat['symbol']
            
            # 检查是否已有持仓：优先从 account 中获取，其次从之前的 condition
            position = self.account.get_position(symbol)
            if position:
                current_quantity = position.quantity
            elif symbol in existing_positions:
                current_quantity = existing_positions[symbol]
            else:
                current_quantity = 0
            
            condition = TradingCondition(
                symbol=symbol,
                entry_price=strat['entry_price'],
                stop_loss=strat['stop_loss'],
                take_profit=strat['take_profit'],
                quantity=current_quantity  # 使用实际持仓数量，而不是一律为0
            )
            self.strategy.add_condition(condition)
        
        logger.info(f"已加载 {len(strategies)} 个交易策略")
        print(f"\n✅ 已加载 {len(strategies)} 个交易策略:")
        
        for strat in strategies:
            symbol = strat['symbol']
            starred = "⭐" if strat['is_starred'] else ""
            position = self.account.get_position(symbol)
            status = f" [已持仓: {position.quantity}股]" if position else ""
            print(f"   {starred} {symbol} ({strat['name']}){status}")
            print(f"      买入: ${strat['entry_price']:.2f}, 止损: ${strat['stop_loss']:.2f}, 止盈: ${strat['take_profit']:.2f}")
        
        return len(strategies)
    
    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("Monitor is already running")
            return
        
        # 添加定时任务
        self.scheduler.add_job(
            self.monitor_task,
            'interval',
            seconds=MONITOR_INTERVAL_SECONDS,
            id='trading_monitor',
            name='Trading Monitor Task'
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"Trading Monitor started (interval: {MONITOR_INTERVAL_SECONDS}s)")
        print(f"\n✅ 监控已启动!")
        print(f"   监控间隔: {MONITOR_INTERVAL_SECONDS} 秒")
        print(f"   监控股票: {', '.join(self.strategy.get_all_symbols()) or '无'}")
    
    def stop(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("Monitor is not running")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        
        logger.info("Trading Monitor stopped")
        print("\n❌ 监控已停止")
    
    def monitor_task(self):
        """监控任务 - 定期执行"""
        logger.info("="*60)
        logger.info(f"Monitor task started at {datetime.now()}")
            
        # 检查市场是否开盘
        if not self.market_data.is_market_open():
            logger.info("Market is closed, skipping monitor task")
            self.add_log("🚫 交易市场已关闭，等待下次监控", 'info')
            return
        
        # 每次监控前重新加载最新的交易策略
        logger.info("重新加载交易策略...")
        count = self.load_strategies_from_db()
        if count == 0:
            logger.warning("No strategies loaded from database")
            self.add_log("⚠️ 没有找到有效的交易计划", 'warning')
            return
        
        symbols = self.strategy.get_all_symbols()
        
        if not symbols:
            logger.info("No symbols to monitor")
            return
        
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行监控任务...")
        
        # 监控每个股票
        for symbol in symbols:
            self._monitor_symbol(symbol)
        
        # 更新所有持仓的当前价格
        self._update_positions()
        
        # 打印账户摘要
        self._print_summary()
        
        logger.info("Monitor task completed")
    
    def _monitor_symbol(self, symbol: str):
        """
        监控单个股票
        
        Args:
            symbol: 股票代码
        """
        # 获取当前价格
        current_price = self.market_data.get_current_price(symbol)
        
        if current_price is None:
            logger.error(f"Failed to get price for {symbol}")
            self.add_log(f"{symbol}: 无法获取股价", 'error')
            return
        
        # 获取交易条件
        condition = self.strategy.get_condition(symbol)
        if not condition:
            self.add_log(f"{symbol}: 没有交易计划", 'warning')
            return
        
        # 检查买入信号
        entry_signal = self.strategy.check_entry_signal(symbol, current_price)
        if entry_signal == 'BUY':
            # 执行买入
            self._execute_buy_with_log(symbol, current_price, condition)
            return
        
        # 检查卖出信号
        exit_signal = self.strategy.check_exit_signal(symbol, current_price)
        if exit_signal == 'SELL':
            # 执行卖出
            self._execute_sell_with_log(symbol, current_price, condition)
            return
        
        # 没有触发任何信号
        if condition.quantity > 0:
            # 持有中
            self.add_log(
                f"{symbol}: 当前 ${current_price:.2f}, 持有中 (止损 ${condition.stop_loss:.2f}, 止盈 ${condition.take_profit:.2f})",
                'info'
            )
        else:
            # 未持仓，未满足买入条件
            if current_price > condition.entry_price:
                self.add_log(
                    f"{symbol}: 当前 ${current_price:.2f}, 价格高于买入价 ${condition.entry_price:.2f}, 未买入",
                    'info'
                )
            else:
                self.add_log(
                    f"{symbol}: 当前 ${current_price:.2f}, 未满足买入条件 (买入价 ${condition.entry_price:.2f})",
                    'info'
                )
    
    def _execute_buy_with_log(self, symbol: str, price: float, condition):
        """
        执行买入并记录单行日志
        
        Args:
            symbol: 股票代码
            price: 买入价格
            condition: 交易条件
        """
        # 计算买入数量
        max_investment = self.account.total_equity * MAX_POSITION_SIZE
        affordable_qty = int(max_investment / price)
        
        if affordable_qty < 1:
            logger.warning(f"Insufficient funds to buy {symbol}")
            self.add_log(f"{symbol}: 当前 ${price:.2f}, 资金不足无法买入", 'warning')
            return
        
        # 计算手续费
        commission = price * affordable_qty * COMMISSION_RATE
        
        # 执行买入
        success = self.account.buy(symbol, affordable_qty, price, commission)
        
        if success:
            # 更新策略中的持仓数量
            self.strategy.update_position(symbol, affordable_qty)
            
            # 保存到数据库
            self.trade_db.save_trade(
                symbol=symbol,
                action='BUY',
                quantity=affordable_qty,
                price=price,
                commission=commission
            )
            
            print(f"   📥 买入 {symbol}: {affordable_qty} 股 @ ${price:.2f}")
            logger.info(f"BUY executed: {affordable_qty} {symbol} @ ${price:.2f}")
            
            # 单行日志
            self.add_log(
                f"{symbol}: 买入 {affordable_qty}股 @ ${price:.2f} (买入价 ${condition.entry_price:.2f}, 止损 ${condition.stop_loss:.2f}, 止盈 ${condition.take_profit:.2f})",
                'trade'
            )
        else:
            logger.error(f"BUY failed for {symbol}")
            self.add_log(f"{symbol}: 买入失败", 'error')
    
    def _execute_sell_with_log(self, symbol: str, price: float, condition):
        """
        执行卖出并记录单行日志
        
        Args:
            symbol: 股票代码
            price: 卖出价格
            condition: 交易条件
        """
        position = self.account.get_position(symbol)
        if not position:
            logger.warning(f"No position to sell for {symbol}")
            return
        
        quantity = position.quantity
        commission = price * quantity * COMMISSION_RATE
        
        # 执行卖出
        success = self.account.sell(symbol, quantity, price, commission)
        
        if success:
            # 更新策略中的持仓数量
            self.strategy.update_position(symbol, 0)
            
            # 计算盈亏
            pnl = (price - position.avg_price) * quantity - commission
            pnl_pct = (pnl / (position.avg_price * quantity)) * 100
            
            # 判断是止损还是止盈
            if price <= condition.stop_loss:
                reason = "止损"
            elif price >= condition.take_profit:
                reason = "止盈"
            else:
                reason = "卖出"
            
            # 保存到数据库
            self.trade_db.save_trade(
                symbol=symbol,
                action='SELL',
                quantity=quantity,
                price=price,
                commission=commission,
                notes=f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)"
            )
            
            print(f"   📤 卖出 {symbol}: {quantity} 股 @ ${price:.2f}")
            print(f"      盈亏: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            logger.info(f"SELL executed: {quantity} {symbol} @ ${price:.2f}, P&L: ${pnl:.2f}")
            
            # 单行日志
            self.add_log(
                f"{symbol}: {reason} {quantity}股 @ ${price:.2f}, 盈亏 ${pnl:.2f} ({pnl_pct:+.2f}%)",
                'trade'
            )
        else:
            logger.error(f"SELL failed for {symbol}")
            self.add_log(f"{symbol}: 卖出失败", 'error')
    
    def _update_positions(self):
        """更新所有持仓的当前价格"""
        if not self.account.positions:
            return
        
        prices = {}
        for symbol in self.account.positions.keys():
            price = self.market_data.get_current_price(symbol)
            if price:
                prices[symbol] = price
        
        self.account.update_prices(prices)
    
    def _print_summary(self):
        """打印账户摘要"""
        summary = self.account.get_summary()
        
        print(f"\n💼 账户状态:")
        print(f"   现金: ${summary['cash']:,.2f}")
        print(f"   持仓市值: ${summary['market_value']:,.2f}")
        print(f"   总权益: ${summary['total_equity']:,.2f}")
        print(f"   总盈亏: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:+.2f}%)")
        
        # 保存账户快照到数据库
        self.trade_db.save_account_snapshot(
            cash=summary['cash'],
            market_value=summary['market_value'],
            total_equity=summary['total_equity'],
            total_pnl=summary['total_pnl'],
            total_pnl_pct=summary['total_pnl_pct']
        )
        
        # 显示持仓
        if self.account.positions:
            print(f"\n📊 当前持仓:")
            for pos in self.account.get_positions_list():
                pnl_emoji = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
                print(f"   {pnl_emoji} {pos['symbol']}: {pos['quantity']} 股")
                print(f"      成本: ${pos['avg_price']:.2f}, 当前: ${pos['current_price']:.2f}")
                print(f"      盈亏: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_pct']:+.2f}%)")
                
                # 保存持仓快照
                self.trade_db.save_position_snapshot(
                    symbol=pos['symbol'],
                    quantity=pos['quantity'],
                    avg_price=pos['avg_price'],
                    current_price=pos['current_price'],
                    unrealized_pnl=pos['unrealized_pnl'],
                    unrealized_pnl_pct=pos['unrealized_pnl_pct']
                )
    
    def get_account_summary(self) -> dict:
        """获取账户摘要"""
        return self.account.get_summary()
    
    def get_positions(self) -> list:
        """获取持仓列表"""
        return self.account.get_positions_list()
    
    def get_trades(self, limit: int = 50) -> list:
        """获取交易历史(从数据库)"""
        return self.trade_db.get_all_trades(limit)
    
    def get_trading_stats(self) -> dict:
        """获取交易统计"""
        return self.trade_db.get_trading_stats()


# 全局监控器实例
_monitor_instance: Optional[TradingMonitor] = None


def get_monitor() -> TradingMonitor:
    """获取监控器单例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = TradingMonitor()
    return _monitor_instance
