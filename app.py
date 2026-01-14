#!/usr/bin/env python3
"""
PB Fortune - Stock Trading Plan Manager
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import yaml
import re
import sys
import os
import logging
from database import TradingPlanDB

logger = logging.getLogger(__name__)

# Add mock_trade directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mock_trade'))
from monitor import get_monitor

app = Flask(__name__)
CORS(app)

# Load configuration
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Initialize database
db = TradingPlanDB()

# Initialize mock trading monitor (singleton)
monitor = get_monitor()

# Auto-start monitoring on startup
def init_monitoring():
    """Initialize and start monitoring automatically"""
    print("\n" + "="*60)
    print("  🚀 自动启动模拟交易监控")
    print("="*60)
    
    # Load strategies from database
    count = monitor.load_strategies_from_db()
    if count > 0:
        print(f"✅ 已加载 {count} 个交易策略")
        # Start monitoring
        monitor.start()
        print("✅ 监控已启动 (每小时检查一次)")
        print("="*60 + "\n")
    else:
        print("⚠️  数据库中暂无交易计划,监控未启动")
        print("="*60 + "\n")

# Initialize monitoring when app starts
init_monitoring()


@app.route('/')
def index():
    """Home page"""
    dify_url = config.get('dify', {}).get('chatbot_url', '')
    return render_template('trading_plans.html', dify_url=dify_url)


def parse_trading_plan(content):
    """Parse trading plan content and extract stock info"""
    # Try pattern 1: 股票名称：SYMBOL (Name)
    stock_match = re.search(r'股票名称[：:]\s*([A-Z]+)\s*\(([^)]+)\)', content)
    
    # Try pattern 2: 股票名称：Name (SYMBOL)
    if not stock_match:
        stock_match = re.search(r'股票名称[：:]\s*([^(]+?)\s*\(([A-Z]+)\)', content)
        if stock_match:
            # Swap: group1 is name, group2 is symbol
            stock_name = stock_match.group(1).strip()
            stock_symbol = stock_match.group(2).strip()
            return stock_symbol, stock_name, content
    
    if not stock_match:
        return None, None, content
    
    stock_symbol = stock_match.group(1)
    stock_name = stock_match.group(2)
    
    return stock_symbol, stock_name, content


@app.route('/api/plans', methods=['GET', 'POST'])
def handle_plans():
    """Handle trading plans"""
    if request.method == 'POST':
        data = request.get_json()
        content = data.get('content', '')
        password = data.get('password', '')
        conversation_id = data.get('conversation_id')
        
        # 验证密码（后端验证，无法绕过）
        correct_password = config.get('app', {}).get('save_password', '')
        if password != correct_password:
            return jsonify({
                'status': 'error',
                'message': '密码错误，无权保存'
            }), 403
        
        # Parse the content
        stock_symbol, stock_name, plan_content = parse_trading_plan(content)
        
        if not stock_symbol:
            return jsonify({
                'status': 'error',
                'message': 'Could not extract stock symbol'
            }), 400
        
        # Save to database
        plan_id = db.save_plan(
            stock_symbol=stock_symbol,
            stock_name=stock_name,
            plan_content=plan_content,
            conversation_id=conversation_id
        )
        
        return jsonify({
            'status': 'success',
            'plan_id': plan_id,
            'stock_symbol': stock_symbol,
            'stock_name': stock_name
        })
    
    else:  # GET
        status = request.args.get('status', 'active')
        plans = db.get_latest_plans(status)
        return jsonify({
            'status': 'success',
            'plans': plans
        })


@app.route('/api/plans/<int:plan_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_plan(plan_id):
    """Handle single trading plan"""
    if request.method == 'GET':
        plan = db.get_plan_by_id(plan_id)
        if plan:
            return jsonify({
                'status': 'success',
                'plan': plan
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Plan not found'
            }), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        success = db.update_plan(plan_id, **data)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({
                'status': 'error',
                'message': 'Update failed'
            }), 400
    
    elif request.method == 'DELETE':
        db.delete_plan(plan_id)
        return jsonify({'status': 'success'})


@app.route('/api/plans/versions/<stock_symbol>')
def get_stock_versions(stock_symbol):
    """Get all versions of a stock's trading plans"""
    versions = db.get_plan_versions(stock_symbol)
    return jsonify({
        'status': 'success',
        'stock_symbol': stock_symbol,
        'versions': versions,
        'total': len(versions)
    })


@app.route('/api/plans/<int:plan_id>/star', methods=['POST'])
def toggle_star(plan_id):
    """Toggle star status (requires authentication)"""
    data = request.get_json()
    password = data.get('password', '')
    
    # 验证密码
    correct_password = config.get('app', {}).get('save_password', '')
    if password != correct_password:
        return jsonify({
            'status': 'error',
            'message': '密码错误，无权操作'
        }), 403
    
    new_status = db.toggle_star(plan_id)
    return jsonify({
        'status': 'success',
        'is_starred': new_status
    })


@app.route('/api/plans/search')
def search_plans():
    """Search trading plans"""
    keyword = request.args.get('q', '')
    plans = db.search_plans(keyword)
    return jsonify({
        'status': 'success',
        'plans': plans
    })


@app.route('/api/chat/unlock', methods=['POST'])
def unlock_chat():
    """Verify password for chat unlock"""
    data = request.get_json()
    password = data.get('password', '')
    
    # 验证密码
    correct_password = config.get('app', {}).get('save_password', '')
    if password != correct_password:
        return jsonify({
            'status': 'error',
            'message': '密码错误'
        }), 403
    
    return jsonify({
        'status': 'success',
        'message': '验证成功'
    })


# ============================================================
# Mock Trading API Endpoints
# ============================================================

@app.route('/api/mock-trading/status')
def get_trading_status():
    """获取交易监控状态"""
    return jsonify({
        'status': 'success',
        'is_running': monitor.is_running,
        'monitored_stocks': monitor.strategy.get_all_symbols()
    })


@app.route('/api/mock-trading/account')
def get_account_info():
    """获取账户信息"""
    summary = monitor.get_account_summary()
    return jsonify({
        'status': 'success',
        'account': summary
    })


@app.route('/api/mock-trading/positions')
def get_positions():
    """获取持仓列表"""
    positions = monitor.get_positions()
    return jsonify({
        'status': 'success',
        'positions': positions
    })


@app.route('/api/mock-trading/trades')
def get_trades():
    """获取交易历史"""
    trades = monitor.get_trades()
    return jsonify({
        'status': 'success',
        'trades': trades
    })


@app.route('/api/mock-trading/monitor-logs')
def get_monitor_logs():
    """获取监控日志"""
    # 获取语言参数
    lang = request.args.get('lang', 'zh')
    logs = monitor.get_logs(limit=50)
    
    # 翻译日志
    if lang == 'en':
        logs = translate_logs_to_english(logs)
    
    return jsonify({
        'status': 'success',
        'logs': logs
    })


def translate_logs_to_english(logs):
    """将中文日志翻译为英文"""
    translations = {
        '当前': 'Current',
        '持有中': 'Holding',
        '止损': 'Stop Loss',
        '止盈': 'Take Profit',
        '价格高于买入价': 'Price above entry',
        '未买入': 'Not bought',
        '未满足买入条件': 'Entry condition not met',
        '买入价': 'Entry',
        '买入': 'Buy',
        '卖出': 'Sell',
        '盈亏': 'P&L',
        '股': 'shares',
        '无法获取股价': 'Failed to get price',
        '没有交易计划': 'No trading plan',
        '资金不足无法买入': 'Insufficient funds',
        '买入失败': 'Buy failed',
        '卖出失败': 'Sell failed'
    }
    
    translated_logs = []
    for log in logs:
        message = log['message']
        # 替换中文为英文
        for zh, en in translations.items():
            message = message.replace(zh, en)
        
        translated_logs.append({
            'timestamp': log['timestamp'],
            'message': message,
            'type': log['type']
        })
    
    return translated_logs


@app.route('/api/mock-trading/trigger-monitor', methods=['POST'])
def trigger_monitor():
    """手动触发一次监控任务（用于测试）"""
    try:
        monitor.monitor_task()
        return jsonify({
            'status': 'success',
            'message': '监控任务已执行'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/mock-trading/start', methods=['POST'])
def start_trading():
    """启动交易监控"""
    data = request.get_json() or {}
    password = data.get('password', '')
    
    # 验证密码
    correct_password = config.get('app', {}).get('save_password', '')
    if password != correct_password:
        return jsonify({
            'status': 'error',
            'message': '密码错误，无权操作'
        }), 403
    
    if monitor.is_running:
        return jsonify({
            'status': 'error',
            'message': '监控已在运行中'
        }), 400
    
    # 从数据库加载策略
    count = monitor.load_strategies_from_db()
    
    if count == 0:
        return jsonify({
            'status': 'error',
            'message': '没有找到有效的交易计划'
        }), 400
    
    # 启动监控
    monitor.start()
    
    return jsonify({
        'status': 'success',
        'message': f'监控已启动，加载了{count}个交易策略',
        'strategy_count': count
    })


@app.route('/api/mock-trading/stop', methods=['POST'])
def stop_trading():
    """停止交易监控"""
    data = request.get_json() or {}
    password = data.get('password', '')
    
    # 验证密码
    correct_password = config.get('app', {}).get('save_password', '')
    if password != correct_password:
        return jsonify({
            'status': 'error',
            'message': '密码错误，无权操作'
        }), 403
    
    if not monitor.is_running:
        return jsonify({
            'status': 'error',
            'message': '监控未在运行'
        }), 400
    
    monitor.stop()
    
    # 返回最终状态
    summary = monitor.get_account_summary()
    
    return jsonify({
        'status': 'success',
        'message': '监控已停止',
        'final_summary': summary
    })


@app.route('/api/mock-trading/reload', methods=['POST'])
def reload_strategies():
    """重新加载交易策略"""
    data = request.get_json() or {}
    password = data.get('password', '')
    
    # 验证密码
    correct_password = config.get('app', {}).get('save_password', '')
    if password != correct_password:
        return jsonify({
            'status': 'error',
            'message': '密码错误，无权操作'
        }), 403
    
    # 重新加载策略
    count = monitor.load_strategies_from_db()
    
    return jsonify({
        'status': 'success',
        'message': f'已重新加载{count}个交易策略',
        'strategy_count': count
    })


@app.route('/api/mock-trading/stats')
def get_trading_stats():
    """获取交易统计"""
    stats = monitor.get_trading_stats()
    return jsonify({
        'status': 'success',
        'stats': stats
    })


@app.route('/api/mock-trading/equity-curve')
def get_equity_curve():
    """获取权益曲线数据"""
    try:
        # 获取时间范围参数
        time_range = request.args.get('range', 'default')  # 'all' | 'default'
        
        # 从数据库获取账户快照
        if time_range == 'all':
            snapshots = monitor.trade_db.get_account_snapshots(time_range='all')
        else:
            # 默认显示最近30条
            snapshots = monitor.trade_db.get_account_snapshots(limit=30)
        
        # 如果没有快照，生成默认数据
        if not snapshots:
            from datetime import datetime, timedelta
            now = datetime.now()
            snapshots = [
                {
                    'timestamp': (now - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S'),
                    'total_equity': 100000.0
                }
                for i in range(6, -1, -1)  # 生成过去7天的数据
            ]
        
        # 添加当前权益
        from datetime import datetime
        current_summary = monitor.get_account_summary()
        snapshots.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_equity': current_summary['total_equity']
        })
        
        return jsonify({
            'status': 'success',
            'data': snapshots,
            'range': time_range
        })
    except Exception as e:
        logger.error(f"Get equity curve error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': []
        })


if __name__ == '__main__':
    app.run(
        host=config.get('app', {}).get('host', '0.0.0.0'),
        port=config.get('app', {}).get('port', 8888),
        debug=config.get('app', {}).get('debug', False)
    )
