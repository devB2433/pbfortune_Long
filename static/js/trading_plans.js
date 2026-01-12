// Trading Plans JavaScript

class TradingPlanManager {
    constructor() {
        this.plans = [];
        this.modal = document.getElementById('planModal');
        this.password = null; // 存储解锁后的密码
        this.init();
    }

    init() {
        // Load initial plans
        this.loadPlans();

        // Setup event listeners
        document.getElementById('searchBtn').addEventListener('click', () => this.searchPlans());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchPlans();
        });

        // Save plan button
        document.getElementById('savePlanBtn').addEventListener('click', () => this.savePlanFromTextarea());
        
        // Chat unlock button
        document.getElementById('chatUnlockBtn').addEventListener('click', () => this.unlockChat());
        document.getElementById('chatPasswordInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.unlockChat();
        });
        
        // Chat lock button
        document.getElementById('chatLockBtn').addEventListener('click', () => this.lockChat());

        // Modal close
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
    }

    unlockChat() {
        const password = document.getElementById('chatPasswordInput').value.trim();
        
        if (!password) {
            this.showError('请输入密码');
            return;
        }
        
        // 存储密码用于保存
        this.password = password;
        
        // 显示聊天界面
        document.getElementById('unlockOverlay').style.display = 'none';
        document.getElementById('chatContent').style.display = 'flex';
        document.getElementById('chatPasswordInput').value = '';
        
        this.showSuccess('解锁成功');
    }
    
    lockChat() {
        if (!confirm('确定要锁定吗？')) {
            return;
        }
        
        this.password = null;
        document.getElementById('unlockOverlay').style.display = 'flex';
        document.getElementById('chatContent').style.display = 'none';
        document.getElementById('planInput').value = '';
        this.showSuccess('已锁定');
    }

    togglePlanContent(planId) {
        const content = document.getElementById(`plan-content-${planId}`);
        const actions = document.getElementById(`plan-actions-${planId}`);
        const icon = document.getElementById(`expand-icon-${planId}`);
        
        if (content.style.display === 'none') {
            // 展开
            content.style.display = 'block';
            actions.style.display = 'flex';
            icon.textContent = '▲';
        } else {
            // 收起
            content.style.display = 'none';
            actions.style.display = 'none';
            icon.textContent = '▼';
        }
    }

    async toggleStar(planId) {
        if (!this.password) {
            this.showError('请先解锁才能操作');
            return;
        }

        try {
            const response = await fetch(`/api/plans/${planId}/star`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    password: this.password
                })
            });

            const data = await response.json();
            
            if (response.status === 403) {
                this.showError('密码错误，已重新锁定');
                this.lockChat();
                return;
            }
            
            if (data.status === 'success') {
                // 重新加载列表，星标计划会自动置顶
                this.loadPlans();
                const msg = data.is_starred ? '已添加到重点关注' : '已取消关注';
                this.showSuccess(msg);
            } else {
                this.showError(data.message || '操作失败');
            }
        } catch (error) {
            console.error('Failed to toggle star:', error);
            this.showError('操作失败');
        }
    }

    unlock() {
        const password = document.getElementById('passwordInput').value.trim();
        
        if (!password) {
            this.showError('请输入密码');
            return;
        }
        
        // 存储密码，后端会验证
        this.password = password;
        
        // 显示保存表单
        document.getElementById('unlockSection').style.display = 'none';
        document.getElementById('saveForm').style.display = 'block';
        document.getElementById('passwordInput').value = '';
        
        this.showSuccess('解锁成功');
    }
    
    lock() {
        this.password = null;
        document.getElementById('unlockSection').style.display = 'block';
        document.getElementById('saveForm').style.display = 'none';
        document.getElementById('planInput').value = '';
        this.showSuccess('已锁定');
    }

    async loadPlans() {
        try {
            const response = await fetch('/api/plans');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.plans = data.plans;
                this.renderPlans();
            }
        } catch (error) {
            console.error('Failed to load plans:', error);
            this.showError('加载计划失败');
        }
    }

    renderPlans() {
        const plansList = document.getElementById('plansList');
        
        if (this.plans.length === 0) {
            plansList.innerHTML = `
                <div class="empty-state">
                    <div style="font-size: 48px; margin-bottom: 20px;">📋</div>
                    <p>${window.i18n.t('emptyState')}</p>
                    <p style="font-size: 14px; margin-top: 10px;">${window.i18n.t('emptyHint')}</p>
                </div>
            `;
            return;
        }

        // 按跟踪状态分组
        const starred = this.plans.filter(p => p.is_starred && p.tracking_status !== 'paused');
        const active = this.plans.filter(p => !p.is_starred && p.tracking_status !== 'paused');
        const paused = this.plans.filter(p => p.tracking_status === 'paused');

        let html = '';

        // 星标区域
        if (starred.length > 0) {
            html += `
                <div class="plan-section">
                    <div class="section-header">
                        <span class="section-icon">⭐</span>
                        <span class="section-title">${window.i18n.t('starredSection').replace('⭐ ', '')}</span>
                        <span class="section-count">${starred.length}</span>
                    </div>
                    <div class="section-content">
                        ${starred.map(plan => this.createPlanCard(plan)).join('')}
                    </div>
                </div>
            `;
        }

        // 跟踪中区域
        if (active.length > 0) {
            html += `
                <div class="plan-section">
                    <div class="section-header">
                        <span class="section-icon">📋</span>
                        <span class="section-title">${window.i18n.t('trackingSection').replace('📋 ', '')}</span>
                        <span class="section-count">${active.length}</span>
                    </div>
                    <div class="section-content">
                        ${active.map(plan => this.createPlanCard(plan)).join('')}
                    </div>
                </div>
            `;
        }

        // 暂停跟踪区域
        if (paused.length > 0) {
            html += `
                <div class="plan-section paused-section">
                    <div class="section-header" onclick="window.tradingPlanManager.togglePausedSection()" style="cursor: pointer;">
                        <span class="section-icon">⏸️</span>
                        <span class="section-title">${window.i18n.t('pausedSection').replace('⏸️ ', '')}</span>
                        <span class="section-count">${paused.length}</span>
                        <span class="expand-icon" id="paused-expand-icon">▼</span>
                    </div>
                    <div class="section-content" id="paused-content" style="display: none;">
                        ${paused.map(plan => this.createPlanCard(plan)).join('')}
                    </div>
                </div>
            `;
        }

        plansList.innerHTML = html;

        // Add event listeners to buttons
        this.plans.forEach(plan => {
            document.getElementById(`view-${plan.id}`).addEventListener('click', (e) => {
                e.stopPropagation();
                this.viewPlanDetail(plan.id);
            });
            document.getElementById(`versions-${plan.id}`).addEventListener('click', (e) => {
                e.stopPropagation();
                this.viewVersions(plan.stock_symbol);
            });
        });
    }

    togglePausedSection() {
        const content = document.getElementById('paused-content');
        const icon = document.getElementById('paused-expand-icon');
        
        if (content && icon) {
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '▲';
            } else {
                content.style.display = 'none';
                icon.textContent = '▼';
            }
        }
    }

    createPlanCard(plan) {
        const date = new Date(plan.created_at).toLocaleString('zh-CN');
        const preview = this.formatPlanPreview(plan.plan_content);
        const versionBadge = plan.version > 1 ? `<span class="version-badge">v${plan.version}</span>` : '';
        const starIcon = plan.is_starred ? '⭐' : '☆';
        const starClass = plan.is_starred ? 'starred' : '';
        
        // 提取推荐度（兼容多种字段名）
        const recommendMatch = plan.plan_content.match(/(建议推荐度|交易推荐度|推荐度)[：:]\s*([^\n]+)/);
        const recommend = recommendMatch ? recommendMatch[2].trim() : null;
        
        // 推荐度翻译映射
        const recommendTranslations = {
            '高': 'Highly Recommend',
            '中': 'Recommend',
            '低': 'Low',
            '一般': 'Recommend'
        };
        
        // 推荐度徽章样式
        let recommendBadge = '';
        if (recommend) {
            const level = recommend.includes('高') ? 'high' : (recommend.includes('中') || recommend.includes('一般')) ? 'medium' : 'low';
            const lang = window.i18n.getCurrentLang();
            const displayText = lang === 'zh' ? recommend : (recommendTranslations[recommend] || recommend);
            recommendBadge = `<span class="recommend-badge recommend-${level}">${displayText}</span>`;
        }
        
        return `
            <div class="plan-card ${starClass}" data-plan-id="${plan.id}">
                <div class="plan-header" onclick="window.tradingPlanManager.togglePlanContent(${plan.id})">
                    <div class="plan-title">
                        <button class="star-btn" id="star-${plan.id}" onclick="event.stopPropagation(); window.tradingPlanManager.toggleStar(${plan.id});" title="重点关注">${starIcon}</button>
                        <span class="plan-symbol">${plan.stock_symbol}</span>
                        ${plan.stock_name ? ` - ${plan.stock_name}` : ''}
                        ${versionBadge}
                        ${recommendBadge}
                        <span class="expand-icon" id="expand-icon-${plan.id}">▼</span>
                    </div>
                    <div class="plan-date">${date}</div>
                </div>
                <div class="plan-content" id="plan-content-${plan.id}" style="display: none;">
                    ${preview}
                </div>
                <div class="plan-actions" id="plan-actions-${plan.id}" style="display: none;">
                    <button id="view-${plan.id}" class="btn btn-primary">${window.i18n.t('viewDetail')}</button>
                    <button id="versions-${plan.id}" class="btn btn-secondary">${window.i18n.t('historyVersions')}</button>
                </div>
            </div>
        `;
    }

    formatPlanPreview(content) {
        // Parse and format the plan content
        const lines = content.split('\n');
        let html = '';
        let inPlan = false;
        
        // 中英文术语映射
        const translations = {
            zh: {
                spotPlan: '📈 现货计划：',
                optionPlan: '📊 期权计划：',
                profitRate: '预期收益率',
                target: '目标',
                buyPrice: '买入价',
                sellPrice: '止盈价',
                stopLoss: '止损价'
            },
            en: {
                spotPlan: '📈 Spot Trading:',
                optionPlan: '📊 Options Trading:',
                profitRate: 'Expected Return',
                target: 'Target',
                buyPrice: 'Buy',
                sellPrice: 'Target',
                stopLoss: 'Stop Loss'
            }
        };
        
        const lang = window.i18n.getCurrentLang();
        const t = translations[lang];
        
        for (let line of lines) {
            line = line.trim();
            if (!line) continue;
            
            // 跳过推荐度和股票名称（已在卡片标题显示）
            if (line.includes('推荐度') || line.includes('股票名称')) {
                continue;
            }
            
            // 翻译计划标题
            if (line.includes('现货计划')) {
                if (inPlan) html += '</div>';
                html += `<div class="plan-section"><div class="plan-section-title">${t.spotPlan}</div>`;
                inPlan = true;
            } else if (line.includes('期权计划')) {
                if (inPlan) html += '</div>';
                html += `<div class="plan-section"><div class="plan-section-title">${t.optionPlan}</div>`;
                inPlan = true;
            } else if (line.startsWith('-')) {
                // 先提取收益率（在翻译之前）
                const profitMatch = line.match(/(预期收益率|收益率)[：:]?\s*(\d+)%/);
                let profit = null;
                let profitClass = '';
                if (profitMatch) {
                    profit = parseInt(profitMatch[2]);
                    profitClass = profit >= 50 ? 'profit-high' : profit >= 30 ? 'profit-medium' : 'profit-low';
                }
                
                // 翻译关键词
                let translatedLine = line;
                if (lang === 'en') {
                    translatedLine = translatedLine
                        .replace(/目标(\d+)/g, 'Target $1')
                        .replace(/买入价/g, 'Buy Price')
                        .replace(/止盈价/g, 'Take Profit')
                        .replace(/止损价/g, 'Stop Loss')
                        .replace(/（T1后调整至/g, '(Adjust to')
                        .replace(/）/g, ')')
                        .replace(/(预期收益率|收益率)[：:]?\s*(\d+)%/, `${t.profitRate} $2%`);
                }
                
                // 高亮显示收益率
                if (profit !== null) {
                    const profitText = lang === 'zh' ? `预期收益率 ${profit}%` : `${t.profitRate} ${profit}%`;
                    const profitRegex = lang === 'zh' ? 
                        new RegExp(`(预期收益率|收益率)[：:]?\\s*${profit}%`) :
                        new RegExp(`${t.profitRate}\\s+${profit}%`);
                    translatedLine = translatedLine.replace(profitRegex, `<span class="profit-badge ${profitClass}">${profitText}</span>`);
                }
                
                html += `<div class="plan-target">${translatedLine}</div>`;
            }
        }
        
        if (inPlan) html += '</div>';
        
        return html;
    }

    async savePlan(content, conversationId = null) {
        try {
            const response = await fetch('/api/plans', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    password: this.password, // 发送密码到后端验证
                    conversation_id: conversationId
                })
            });

            const data = await response.json();
            
            if (response.status === 403) {
                // 密码错误，重新锁定
                this.lock();
                this.showError('密码错误，已重新锁定');
                return false;
            }
            
            if (data.status === 'success') {
                this.showSuccess(`已保存 ${data.stock_symbol} 的交易计划`);
                this.loadPlans(); // Reload the list
                return true;
            } else {
                this.showError(data.message || '保存失败');
                return false;
            }
        } catch (error) {
            console.error('Failed to save plan:', error);
            this.showError('保存失败');
            return false;
        }
    }

    async deletePlan(planId) {
        if (!confirm('确定要删除这个交易计划吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/plans/${planId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess('删除成功');
                this.loadPlans();
            }
        } catch (error) {
            console.error('Failed to delete plan:', error);
            this.showError('删除失败');
        }
    }

    async searchPlans() {
        const keyword = document.getElementById('searchInput').value.trim();
        
        if (!keyword) {
            this.loadPlans();
            return;
        }

        try {
            const response = await fetch(`/api/plans/search?q=${encodeURIComponent(keyword)}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.plans = data.plans;
                this.renderPlans();
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showError('搜索失败');
        }
    }

    viewPlanDetail(planId) {
        const plan = this.plans.find(p => p.id === planId);
        if (!plan) return;

        const modalBody = document.getElementById('modalBody');
        const date = new Date(plan.created_at).toLocaleString('zh-CN');
        
        modalBody.innerHTML = `
            <h2>${plan.stock_symbol} - ${plan.stock_name || ''}</h2>
            <p style="color: #999; margin: 10px 0;">${date}</p>
            <div style="white-space: pre-wrap; line-height: 1.8; margin-top: 20px;">
                ${plan.plan_content}
            </div>
        `;
        
        this.modal.style.display = 'block';
    }

    async viewVersions(stockSymbol) {
        try {
            const response = await fetch(`/api/plans/versions/${stockSymbol}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.versions.length > 0) {
                const modalBody = document.getElementById('modalBody');
                const versions = data.versions;
                
                let html = `
                    <h2>${stockSymbol} - 历史版本 (${data.total} 个版本)</h2>
                    <div style="margin-top: 20px;">
                `;
                
                versions.forEach((version, index) => {
                    const date = new Date(version.created_at).toLocaleString('zh-CN');
                    const isLatest = index === 0;
                    html += `
                        <div style="
                            padding: 15px; 
                            margin-bottom: 15px; 
                            border: 2px solid ${isLatest ? '#667eea' : '#e5e7eb'};
                            border-radius: 8px;
                            background: ${isLatest ? '#f0f4ff' : 'white'};
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <strong style="color: #667eea;">v${version.version} ${isLatest ? '(最新)' : ''}</strong>
                                <span style="color: #999; font-size: 13px;">${date}</span>
                            </div>
                            <div style="
                                white-space: pre-wrap; 
                                line-height: 1.6; 
                                font-size: 13px;
                                max-height: 200px;
                                overflow-y: auto;
                                color: #555;
                            ">${version.plan_content}</div>
                        </div>
                    `;
                });
                
                html += '</div>';
                modalBody.innerHTML = html;
                this.modal.style.display = 'block';
            }
        } catch (error) {
            console.error('Failed to load versions:', error);
            this.showError('加载版本失败');
        }
    }

    closeModal() {
        this.modal.style.display = 'none';
    }

    unlock() {
        const password = document.getElementById('passwordInput').value.trim();
        
        if (!password) {
            this.showError('请输入密码');
            return;
        }
        
        // 存储密码，后端会验证
        this.password = password;
        
        // 显示保存表单
        document.getElementById('unlockSection').style.display = 'none';
        document.getElementById('saveForm').style.display = 'block';
        document.getElementById('passwordInput').value = '';
        
        this.showSuccess('解锁成功');
    }
    
    lock() {
        this.password = null;
        document.getElementById('unlockSection').style.display = 'block';
        document.getElementById('saveForm').style.display = 'none';
        document.getElementById('planInput').value = '';
        this.showSuccess('已锁定');
    }

    savePlanFromTextarea() {
        const content = document.getElementById('planInput').value.trim();
        
        if (!content) {
            this.showError('请输入交易计划内容');
            return;
        }

        const saveBtn = document.getElementById('savePlanBtn');
        saveBtn.disabled = true;
        saveBtn.textContent = '保存中...';

        this.savePlan(content).then(success => {
            if (success) {
                document.getElementById('planInput').value = '';
                saveBtn.textContent = '✓ 已保存';
                setTimeout(() => {
                    saveBtn.textContent = '💾 保存交易计划';
                    saveBtn.disabled = false;
                }, 2000);
            } else {
                saveBtn.textContent = '💾 保存交易计划';
                saveBtn.disabled = false;
            }
        });
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
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
document.head.appendChild(style);

// Initialize the manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tradingPlanManager = new TradingPlanManager();
});
