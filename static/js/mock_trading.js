/**
 * Mock Trading UI Controller
 * 模拟交易前端控制器
 */

const PASSWORD = '72#V9DI#^2lU0q'; // 应该从配置或环境变量读取
let refreshInterval = null;
let equityChart = null;
let currentTimeRange = 'default'; // 当前选中的时间范围

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initMockTrading();
    initTabNavigation();
    initEquityChart();
    initTimeRangeFilter();
    
    // 监听语言切换，重新加载日志
    document.addEventListener('languageChanged', () => {
        updateMonitorLogs();
    });
});

function initTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            
            // 切换按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 切换内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            if (tabName === 'mock-trading') {
                document.getElementById('mockTradingTab').classList.add('active');
            } else if (tabName === 'trading-plans') {
                document.getElementById('tradingPlansTab').classList.add('active');
                // 切换到交易计划Tab时,触发加载
                if (window.tradingPlanManager) {
                    window.tradingPlanManager.loadPlans();
                }
            }
        });
    });
}

function initMockTrading() {
    // 初始加载数据
    refreshData();
    
    // 每10秒自动刷新
    refreshInterval = setInterval(refreshData, 10000);
}

// 刷新数据
async function refreshData() {
    await Promise.all([
        updateAccount(),
        updatePositions(),
        updateTrades(),
        updateMonitorLogs(), // 更新监控日志
        updateEquityChart()
    ]);
}

// 初始化权益曲线图
function initEquityChart() {
    const ctx = document.getElementById('equityChart');
    if (!ctx) return;
    
    equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '总权益',
                data: [],
                borderColor: '#000000',
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                tension: 0.4,
                fill: true,
                pointRadius: 2,
                pointHoverRadius: 4,
                pointBackgroundColor: '#000000',
                pointBorderColor: '#000000'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return '权益: $' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 10,
                            family: "'SF Mono', 'Monaco', monospace"
                        },
                        color: '#000000',
                        maxTicksLimit: 6
                    },
                    border: {
                        color: '#000000'
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        borderColor: '#000000'
                    },
                    ticks: {
                        font: {
                            size: 10,
                            family: "'SF Mono', 'Monaco', monospace"
                        },
                        color: '#000000',
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'k';
                        }
                    },
                    border: {
                        color: '#000000'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// 初始化时间范围筛选器
function initTimeRangeFilter() {
    const filterBtns = document.querySelectorAll('.time-filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const range = btn.getAttribute('data-range');
            
            // 更新按钮状态
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新时间范围并刷新图表
            currentTimeRange = range;
            updateEquityChart();
        });
    });
}

// 更新权益曲线数据
async function updateEquityChart() {
    try {
        // 根据时间范围构建API URL
        const url = `/api/mock-trading/equity-curve?range=${currentTimeRange}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success' && equityChart) {
            const chartData = data.data || [];
            
            // 更新图表数据
            equityChart.data.labels = chartData.map(d => {
                const date = new Date(d.timestamp);
                return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
            });
            
            equityChart.data.datasets[0].data = chartData.map(d => d.total_equity);
            
            // 统一使用黑色，不再根据盈亏变色
            equityChart.data.datasets[0].borderColor = '#000000';
            equityChart.data.datasets[0].backgroundColor = 'rgba(0, 0, 0, 0.05)';
            equityChart.data.datasets[0].pointBackgroundColor = '#000000';
            equityChart.data.datasets[0].pointBorderColor = '#000000';
            
            equityChart.update('none'); // 无动画更新
        }
    } catch (error) {
        console.error('Update equity chart error:', error);
    }
}

// 更新账户信息
async function updateAccount() {
    try {
        const response = await fetch('/api/mock-trading/account');
        const data = await response.json();
        
        if (data.status === 'success') {
            const account = data.account;
            
            // 更新显示
            document.getElementById('totalEquity').textContent = formatCurrency(account.total_equity);
            document.getElementById('cash').textContent = formatCurrency(account.cash);
            document.getElementById('marketValue').textContent = formatCurrency(account.market_value);
            
            // 更新盈亏
            const pnlElement = document.getElementById('totalPnl');
            const pnlParent = pnlElement.closest('.summary-item');
            pnlElement.textContent = `${formatCurrency(account.total_pnl)} (${account.total_pnl_pct >= 0 ? '+' : ''}${account.total_pnl_pct.toFixed(2)}%)`;
            
            // 更新盈亏颜色
            pnlParent.classList.remove('positive', 'negative');
            if (account.total_pnl > 0) {
                pnlParent.classList.add('positive');
            } else if (account.total_pnl < 0) {
                pnlParent.classList.add('negative');
            }
        }
    } catch (error) {
        console.error('Update account error:', error);
    }
}

// 更新持仓
async function updatePositions() {
    try {
        const response = await fetch('/api/mock-trading/positions');
        const data = await response.json();
        
        if (data.status === 'success') {
            const positions = data.positions;
            const positionsSection = document.getElementById('positionsSection');
            const positionsList = document.getElementById('positionsList');
            
            if (positions.length > 0) {
                positionsSection.style.display = 'block';
                positionsList.innerHTML = positions.map(pos => `
                    <div class="position-item">
                        <div>
                            <span class="position-symbol">${pos.symbol}</span>
                            <span style="color: #64748b;"> ${pos.quantity}股 @ $${pos.avg_price.toFixed(2)}</span>
                        </div>
                        <div class="position-pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                            ${pos.unrealized_pnl >= 0 ? '+' : ''}$${pos.unrealized_pnl.toFixed(2)} (${pos.unrealized_pnl_pct >= 0 ? '+' : ''}${pos.unrealized_pnl_pct.toFixed(2)}%)
                        </div>
                    </div>
                `).join('');
            } else {
                positionsSection.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Update positions error:', error);
    }
}

// 更新交易历史
async function updateTrades() {
    try {
        const response = await fetch('/api/mock-trading/trades');
        const data = await response.json();
        
        if (data.status === 'success') {
            const trades = data.trades.slice(0, 5); // 只显示最近5条
            const tradesSection = document.getElementById('tradesSection');
            const tradesList = document.getElementById('tradesList');
            
            if (trades.length > 0) {
                tradesSection.style.display = 'block';
                tradesList.innerHTML = trades.map(trade => {
                    const date = new Date(trade.timestamp);
                    const dateStr = date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
                    
                    return `
                        <div class="trade-item">
                            <div>
                                <span class="trade-action ${trade.action.toLowerCase()}">${trade.action === 'BUY' ? '📥' : '📤'} ${trade.action}</span>
                                <span> ${trade.quantity} ${trade.symbol} @ $${trade.price.toFixed(2)}</span>
                            </div>
                            <div style="font-size: 10px;">${dateStr}</div>
                        </div>
                    `;
                }).join('');
            } else {
                tradesSection.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Update trades error:', error);
    }
}

// 更新监控日志
async function updateMonitorLogs() {
    try {
        // 获取当前语言
        const currentLang = window.i18n ? window.i18n.currentLang : 'zh';
        
        const response = await fetch(`/api/mock-trading/monitor-logs?lang=${currentLang}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const logs = data.logs || [];
            const monitorConsole = document.getElementById('monitorConsole');
            
            if (!monitorConsole) return;
            
            if (logs.length > 0) {
                // 渲染日志
                monitorConsole.innerHTML = logs.map(log => {
                    const iconMap = {
                        'info': 'ℹ️',
                        'success': '✅',
                        'warning': '⚠️',
                        'error': '❌',
                        'trade': '💰'
                    };
                    
                    const icon = iconMap[log.type] || 'ℹ️';
                    
                    return `
                        <div class="console-line ${log.type}">
                            <span class="console-time">[${log.timestamp}]</span>
                            <span class="console-icon">${icon}</span>
                            <span class="console-message">${log.message}</span>
                        </div>
                    `;
                }).join('');
                
                // 自动滚动到底部（使用 setTimeout 确保渲染完成）
                setTimeout(() => {
                    monitorConsole.scrollTop = monitorConsole.scrollHeight;
                }, 100);
            } else {
                const loadingText = window.i18n ? window.i18n.t('monitorLogsLoading') : '等待监控任务执行...';
                monitorConsole.innerHTML = `<div class="console-loading">${loadingText}</div>`;
            }
        }
    } catch (error) {
        console.error('Update monitor logs error:', error);
        const monitorConsole = document.getElementById('monitorConsole');
        if (monitorConsole) {
            const errorText = window.i18n ? window.i18n.t('monitorLogsError') : '加载失败';
            monitorConsole.innerHTML = `<div class="console-loading" style="color: #ef4444;">${errorText}</div>`;
        }
    }
}

// 格式化货币
function formatCurrency(value) {
    return '$' + value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// 显示通知
function showNotification(message, type = 'info') {
    // 简单的通知实现，可以后续改进
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#0ea5e9'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        font-size: 14px;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 添加动画样式
const mockTradingStyle = document.createElement('style');
mockTradingStyle.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(mockTradingStyle);
