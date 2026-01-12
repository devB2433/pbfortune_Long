#!/usr/bin/env python3
"""
Wicked Stock Trading Tool - Main Application
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import yaml
import re
from database import TradingPlanDB

app = Flask(__name__)
CORS(app)

# Load configuration
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Initialize database
db = TradingPlanDB()


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


if __name__ == '__main__':
    app.run(
        host=config.get('app', {}).get('host', '0.0.0.0'),
        port=config.get('app', {}).get('port', 8888),
        debug=config.get('app', {}).get('debug', False)
    )
