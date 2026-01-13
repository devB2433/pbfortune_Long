"""
Market Data Provider
行情数据提供者
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """市场数据提供者"""
    
    def __init__(self):
        self.cache = {}  # 简单的内存缓存
        self.cache_ttl = 300  # 缓存5分钟
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取股票当前价格
        
        Args:
            symbol: 股票代码 (如 'AAPL')
            
        Returns:
            当前价格,失败返回 None
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            current_price = data['Close'].iloc[-1]
            logger.info(f"{symbol} current price: ${current_price:.2f}")
            return float(current_price)
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        获取历史行情数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            logger.info(f"Retrieved {len(data)} bars for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return None
    
    def get_latest_ohlcv(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        获取最新的 OHLCV 数据
        
        Returns:
            {'open': float, 'high': float, 'low': float, 'close': float, 'volume': int}
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            
            if data.empty:
                return None
            
            latest = data.iloc[-1]
            return {
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {symbol}: {e}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取实时报价信息
        
        Returns:
            包含价格、涨跌幅等信息的字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
            }
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """
        检查市场是否开盘
        
        简化版本: 检查是否为工作日的交易时段
        TODO: 可以考虑使用更精确的市场日历
        """
        now = datetime.now()
        
        # 周末不开盘
        if now.weekday() >= 5:
            return False
        
        # 美股交易时间: 9:30 - 16:00 ET
        # 这里简化处理,实际应该转换时区
        hour = now.hour
        if 9 <= hour < 16:
            return True
        
        return False
