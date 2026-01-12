// 多语言配置
const translations = {
    zh: {
        // 页面标题
        pageTitle: '股票交易计划管理 - Wicked Stock Trading',
        
        // 左侧面板
        tradingPlans: '📊 交易计划',
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
        
        // 右侧面板
        aiAssistant: '🤖 AI 交易助手',
        unlockTitle: '🔒 请输入密码',
        passwordPlaceholder: '请输入密码',
        unlockBtn: '解锁',
        lockBtn: '🔒 锁定',
        saveBtn: '💾 保存交易计划',
        
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
        language: '🌐 Language'
    },
    en: {
        // Page Title
        pageTitle: 'Stock Trading Plan Manager - Wicked Stock Trading',
        
        // Left Panel
        tradingPlans: '📊 Trading Plans',
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
        
        // Right Panel
        aiAssistant: '🤖 AI Trading Assistant',
        unlockTitle: '🔒 Enter Password',
        passwordPlaceholder: 'Enter password',
        unlockBtn: 'Unlock',
        lockBtn: '🔒 Lock',
        saveBtn: '💾 Save Plan',
        
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
        language: '🌐 中文'
    }
};

// 国际化管理类
class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'zh';
        this.translations = translations;
    }
    
    t(key) {
        return this.translations[this.currentLang][key] || key;
    }
    
    switchLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('language', lang);
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
        
        // 更新静态文本
        const textElements = {
            'tradingPlansTitle': 'tradingPlans',
            'searchInput': 'searchPlaceholder',
            'unlockTitle': 'unlockTitle',
            'passwordInput': 'passwordPlaceholder',
            'unlockBtn': 'unlockBtn',
            'lockBtn': 'lockBtn',
            'saveBtn': 'saveBtn',
            'aiAssistantTitle': 'aiAssistant',
            'langBtn': 'language'
        };
        
        Object.keys(textElements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                if (element.tagName === 'INPUT') {
                    element.placeholder = this.t(textElements[id]);
                } else {
                    element.textContent = this.t(textElements[id]);
                }
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
