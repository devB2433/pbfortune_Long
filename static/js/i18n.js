// 多语言配置
const translations = {
    zh: {
        // 页面标题
        pageTitle: '股票交易计划管理 - Wicked Stock Trading',
        
        // Tab标签
        mockTrading: '📈 模拟交易',
        tradingPlans: '📊 交易计划',
        autoRunning: '自动运行中',
        running: '运行中',
        
        // 模拟交易面板
        totalEquity: '总权益',
        cash: '现金',
        marketValue: '市值',
        pnl: '盈亏',
        equityCurve: '📊 权益曲线',
        recentRange: '最近',
        allRange: '全部',
        positions: '📊 持仓',
        recentTrades: '📋 最近交易',
        
        // 左侧面板
        searchPlaceholder: '搜索股票代码或名称...',
        
        // 区域标题
        starredSection: '⭐ 重点关注',
        trackingSection: '📋 跟踪中',
        pausedSection: '⏸️ 暂停跟踪',
        
        // 空状态
        emptyState: '暂无交易计划',
        emptyHint: '使用右侧 AI 助手生成交易计划',
        
        // 按钮
        viewDetail: '查看详情',
        historyVersions: '历史版本',
        
        // 弹窗
        versionCount: '个版本',
        latest: '最新',
        stockName: '股票名称',
        recommendLevel: '交易推荐度',
        spotPlanTitle: '现货计划',
        target: '目标',
        buyPrice: '买入价',
        sellPrice: '止盈价',
        stopLoss: '止损价',
        profitRate: '预期收益率',
        
        // 错误消息
        loadVersionsFailed: '加载版本失败',
        enterPassword: '请输入密码',
        enterContent: '请输入交易计划内容',
        saving: '保存中...',
        
        // 右侧面板
        aiAssistant: '💬 AI 交易助手',
        unlockTitle: '🔒 授权访问',
        unlockHint: '请输入密码解锁 AI 交易助手',
        passwordPlaceholder: '请输入密码',
        unlockBtnText: '解锁',
        lockBtn: '锁定',
        saveBtn: '💾 保存交易计划',
        
        // Dify 输入提示
        difyInputPlaceholder: '从上方对话中复制 AI 生成的交易计划粘贴到这里...',
        
        // 计划标题
        spotPlan: '📈 现货计划：',
        optionPlan: '📊 期权计划：',
        
        // 提示信息
        loading: '加载中...',
        unlockSuccess: '解锁成功',
        locked: '已锁定',
        passwordError: '密码错误，已重新锁定',
        saved: '已保存',
        saveFailed: '保存失败',
        
        // 语言切换
        language: 'EN | 中'
    },
    en: {
        // Page Title
        pageTitle: 'Stock Trading Plan Manager - Wicked Stock Trading',
        
        // Tab Labels
        mockTrading: '📈 Mock Trading',
        tradingPlans: '📊 Trading Plans',
        autoRunning: 'Auto Running',
        running: 'Running',
        
        // Mock Trading Panel
        totalEquity: 'Total Equity',
        cash: 'Cash',
        marketValue: 'Market Value',
        pnl: 'P&L',
        equityCurve: '📊 Equity Curve',
        recentRange: 'Recent',
        allRange: 'All',
        positions: '📊 Positions',
        recentTrades: '📋 Recent Trades',
        
        // Left Panel
        searchPlaceholder: 'Search symbol or name...',
        
        // Section Headers
        starredSection: '⭐ Starred',
        trackingSection: '📋 Tracking',
        pausedSection: '⏸️ Paused',
        
        // Empty State
        emptyState: 'No Trading Plans',
        emptyHint: 'Use AI assistant on the right to generate plans',
        
        // Buttons
        viewDetail: 'View Details',
        historyVersions: 'History',
        
        // Modal
        versionCount: 'versions',
        latest: 'Latest',
        stockName: 'Stock Name',
        recommendLevel: 'Recommendation',
        spotPlanTitle: 'Spot Trading',
        target: 'Target',
        buyPrice: 'Buy Price',
        sellPrice: 'Take Profit',
        stopLoss: 'Stop Loss',
        profitRate: 'Expected Return',
        
        // Error Messages
        loadVersionsFailed: 'Failed to load versions',
        enterPassword: 'Please enter password',
        enterContent: 'Please enter trading plan content',
        saving: 'Saving...',
        
        // Right Panel
        aiAssistant: '💬 AI Trading Assistant',
        unlockTitle: '🔒 Enter Password',
        unlockHint: 'Enter password to unlock AI Trading Assistant',
        passwordPlaceholder: 'Enter password',
        unlockBtnText: 'Unlock',
        lockBtn: 'Lock',
        saveBtn: '💾 Save Plan',
        
        // Dify Input Placeholder
        difyInputPlaceholder: 'Copy AI-generated trading plan from the conversation above and paste here...',
        
        // Plan Titles
        spotPlan: '📈 Spot Trading:',
        optionPlan: '📊 Options Trading:',
        
        // Messages
        loading: 'Loading...',
        unlockSuccess: 'Unlocked successfully',
        locked: 'Locked',
        passwordError: 'Incorrect password, locked again',
        saved: 'Saved',
        saveFailed: 'Save failed',
        
        // Language Switcher
        language: '中 | EN'
    }
};

// 国际化管理类
class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'zh';
        this.translations = translations;
        this.initLangSwitch();
    }
    
    initLangSwitch() {
        // 等待 DOM 加载完成
        document.addEventListener('DOMContentLoaded', () => {
            const langSwitch = document.querySelector('.lang-switch');
            const langSlider = document.getElementById('langSlider');
            const langOptions = document.querySelectorAll('.lang-option');
            
            if (!langSwitch || !langSlider) return;
            
            // 初始化滑块位置
            this.updateSliderPosition();
            
            // 点击整个切换框
            langSwitch.addEventListener('click', (e) => {
                if (e.target.classList.contains('lang-option')) {
                    const targetLang = e.target.getAttribute('data-lang');
                    if (targetLang && targetLang !== this.currentLang) {
                        this.switchLanguage(targetLang);
                    }
                } else {
                    // 点击空白区域，切换到另一种语言
                    this.toggleLanguage();
                }
            });
        });
    }
    
    updateSliderPosition() {
        const langSlider = document.getElementById('langSlider');
        const langOptions = document.querySelectorAll('.lang-option');
        
        if (!langSlider) return;
        
        // 更新滑块位置
        if (this.currentLang === 'en') {
            langSlider.classList.add('en');
        } else {
            langSlider.classList.remove('en');
        }
        
        // 更新文字高亮
        langOptions.forEach(option => {
            const lang = option.getAttribute('data-lang');
            if (lang === this.currentLang) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    }
    
    t(key) {
        return this.translations[this.currentLang][key] || key;
    }
    
    switchLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('language', lang);
            this.updateSliderPosition();
            this.updateUI();
        }
    }
    
    toggleLanguage() {
        const newLang = this.currentLang === 'zh' ? 'en' : 'zh';
        this.switchLanguage(newLang);
    }
    
    updateUI() {
        // 更新页面标题
        document.title = this.t('pageTitle');
        document.documentElement.lang = this.currentLang === 'zh' ? 'zh-CN' : 'en';
        
        // 更新所有带 data-i18n 属性的元素
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // 触发重新渲染
        if (window.tradingPlanManager) {
            window.tradingPlanManager.renderPlans();
        }
    }
    
    getCurrentLang() {
        return this.currentLang;
    }
}

// 创建全局实例
window.i18n = new I18n();
