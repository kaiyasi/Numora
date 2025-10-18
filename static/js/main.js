// ==================== 主題切換功能 ====================
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    const icon = themeToggle?.querySelector('i');

    // 檢查本地儲存的主題偏好
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        if (icon) icon.classList.replace('fa-moon', 'fa-sun');
    }

    // 主題切換事件
    themeToggle?.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');

        if (icon) {
            icon.classList.toggle('fa-moon');
            icon.classList.toggle('fa-sun');
        }

        localStorage.setItem('theme', isDark ? 'dark' : 'light');

        // 添加切換動畫
        themeToggle.style.transform = 'scale(0.9) rotate(180deg)';
        setTimeout(() => {
            themeToggle.style.transform = 'scale(1) rotate(0deg)';
        }, 300);
    });
}

// ==================== 數字動畫效果 ====================
function animateNumber(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = Math.round(target).toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current).toLocaleString();
        }
    }, 16);
}

// ==================== 觀察器：元素進入視窗時觸發動畫 ====================
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';

                // 如果是統計數字，觸發數字動畫
                if (entry.target.classList.contains('stat-value')) {
                    const target = parseInt(entry.target.dataset.value);
                    if (!isNaN(target)) {
                        animateNumber(entry.target, target);
                    }
                }
            }
        });
    }, {
        threshold: 0.1
    });

    // 觀察所有需要動畫的元素
    document.querySelectorAll('.glass-card, .stat-card, .feature-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// ==================== 載入動畫 ====================
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="d-flex justify-content-center align-items-center" style="height: 300px;"><div class="loading"></div></div>';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

// ==================== API 請求輔助函數 ====================
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return { error: error.message };
    }
}

// ==================== 圖表主題配置 ====================
function getChartTheme() {
    const isDark = document.body.classList.contains('dark-mode');
    return {
        paper_bgcolor: isDark ? 'rgba(22, 33, 62, 0.9)' : 'rgba(255, 255, 255, 0.9)',
        plot_bgcolor: isDark ? 'rgba(22, 33, 62, 0.5)' : 'rgba(248, 249, 250, 0.5)',
        font: {
            color: isDark ? '#ffffff' : '#333333',
            family: 'Segoe UI, Noto Sans TC, sans-serif'
        },
        xaxis: {
            gridcolor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
            linecolor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'
        },
        yaxis: {
            gridcolor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
            linecolor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'
        }
    };
}

// ==================== 載入圖表 ====================
async function loadChart(chartType, containerId, params = {}) {
    showLoading(containerId);

    const queryString = new URLSearchParams(params).toString();
    const url = `/api/charts/${chartType}${queryString ? '?' + queryString : ''}`;

    try {
        const data = await fetchData(url);

        if (data.error) {
            document.getElementById(containerId).innerHTML =
                `<div class="alert alert-warning">${data.error}</div>`;
            return;
        }

        // 解析圖表數據
        const chartData = JSON.parse(data);

        // 應用主題
        const theme = getChartTheme();
        if (chartData.layout) {
            Object.assign(chartData.layout, theme);
        }

        // 渲染圖表
        Plotly.newPlot(containerId, chartData.data, chartData.layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        });

    } catch (error) {
        console.error('Load chart error:', error);
        document.getElementById(containerId).innerHTML =
            `<div class="alert alert-danger">載入圖表時發生錯誤: ${error.message}</div>`;
    }
}

// ==================== 主題變更時重新載入圖表 ====================
function reloadChartsOnThemeChange() {
    const themeToggle = document.getElementById('themeToggle');
    themeToggle?.addEventListener('click', () => {
        setTimeout(() => {
            // 重新載入所有圖表
            document.querySelectorAll('[id$="Chart"]').forEach(chartContainer => {
                const chartId = chartContainer.id;
                const chartType = chartId.replace('Chart', '').replace(/([A-Z])/g, '_$1').toLowerCase().substring(1);

                if (Plotly) {
                    Plotly.relayout(chartId, getChartTheme());
                }
            });
        }, 300);
    });
}

// ==================== 頁面載入動畫 ====================
function initPageTransitions() {
    // 為導航連結添加過渡效果
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href').startsWith('/')) {
                e.preventDefault();
                document.body.style.opacity = '0';
                setTimeout(() => {
                    window.location.href = link.getAttribute('href');
                }, 300);
            }
        });
    });

    // 頁面載入時淡入
    window.addEventListener('load', () => {
        document.body.style.opacity = '1';
    });
}

// ==================== 工具提示 ====================
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ==================== 卡片懸停效果增強 ====================
function enhanceCardEffects() {
    document.querySelectorAll('.glass-card, .feature-card, .stat-card').forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
}

// ==================== 平滑滾動 ====================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==================== 搜尋功能 ====================
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.toLowerCase();
                performSearch(query);
            }, 300);
        });
    }
}

function performSearch(query) {
    // 搜尋實現邏輯
    console.log('Searching for:', query);
}

// ==================== 通知系統 ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== 圖表導出功能 ====================
function exportChart(chartId, filename = 'chart') {
    Plotly.downloadImage(chartId, {
        format: 'png',
        width: 1920,
        height: 1080,
        filename: filename
    });
}

// ==================== 初始化所有功能 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 基本功能初始化
    initThemeToggle();
    initScrollAnimations();
    initPageTransitions();
    initSmoothScroll();
    initSearch();
    enhanceCardEffects();
    reloadChartsOnThemeChange();

    // Bootstrap 組件初始化
    if (typeof bootstrap !== 'undefined') {
        initTooltips();
    }

    // 頁面載入完成
    console.log('Numora Web Interface Initialized ✨');
});

// ==================== 導出函數供其他腳本使用 ====================
window.NumoraApp = {
    showLoading,
    hideLoading,
    fetchData,
    loadChart,
    showNotification,
    exportChart,
    getChartTheme
};
