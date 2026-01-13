"""
Mock Trading System Configuration
模拟交易系统配置
"""

import os

# 初始资金配置
INITIAL_CAPITAL = 100000.0  # 初始模拟资金 $100,000

# 监控配置
MONITOR_INTERVAL_SECONDS = 300  # 监控频率: 每5分钟 (300秒)
# MONITOR_INTERVAL_SECONDS = 60   # 测试时可以改为每分钟
# MONITOR_INTERVAL_SECONDS = 3600  # 每小时

# 交易配置
MAX_POSITION_SIZE = 0.1  # 单只股票最大仓位 10%
MAX_STOCKS = 10  # 最多监10只股票
COMMISSION_RATE = 0.001  # 手续费率 0.1%
SLIPPAGE_RATE = 0.001  # 滑点率 0.1%

# 数据源配置
DATA_SOURCE = "yahoo"  # yahoo / alphavantage / finnhub
MARKET_TIMEZONE = "America/New_York"  # 市场时区

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "mock_trade.log"

# 数据库配置 (使用项目现有的数据库)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stock_trading.db")
