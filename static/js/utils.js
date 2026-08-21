/* ==========================================
 * Season_Fight 工具函数
 * ========================================== */

// ====== API 请求封装 ======
async function api(url, options = {}) {
    const opts = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };
    if (opts.body && typeof opts.body !== 'string') {
        opts.body = JSON.stringify(opts.body);
    }
    try {
        const res = await fetch(url, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || `请求失败 (${res.status})`);
        }
        return data;
    } catch (err) {
        console.error('[API错误]', url, err);
        showToast(err.message || '网络请求失败', 'error');
        throw err;
    }
}

// ====== Toast 提示 ======
let toastTimer = null;
function showToast(message, type = 'info', duration = 2500) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = 'toast show ' + type;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.className = 'toast ' + type;
    }, duration);
}

// ====== 时间格式化 ======
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0 分钟';
    seconds = Math.floor(seconds);
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h} 小时 ${m} 分`;
    if (m > 0) return `${m} 分 ${s} 秒`;
    return `${s} 秒`;
}

function formatTime(totalSeconds) {
    const h = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
    const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
    const s = String(Math.floor(totalSeconds % 60)).padStart(2, '0');
    return `${h}:${m}:${s}`;
}

function formatDate(date) {
    const d = new Date(date);
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`;
}

function formatDateShort(date) {
    const d = new Date(date);
    return `${d.getMonth() + 1}月${d.getDate()}日`;
}

function todayStr() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function dateOffset(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// ====== HTML 转义 ======
function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ====== 状态徽章 ======
function statusBadge(status) {
    const map = {
        'pending': '<span class="task-badge" style="background:#7f8c8d">待开始</span>',
        'running': '<span class="task-badge" style="background:#667eea">进行中</span>',
        'paused': '<span class="task-badge" style="background:#ffa502">已暂停</span>',
        'completed': '<span class="task-badge" style="background:#2ecc71">已完成</span>',
        'uncompleted': '<span class="task-badge" style="background:#ff4757">未完成</span>',
    };
    return map[status] || '';
}

// ====== 弹窗控制 ======
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'flex';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

// 绑定所有关闭按钮
document.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('[data-modal]');
    if (closeBtn) {
        closeModal(closeBtn.dataset.modal);
    }
    // 点击遮罩关闭
    if (e.target.classList && e.target.classList.contains('modal-mask')) {
        const modal = e.target.closest('.modal');
        if (modal) modal.style.display = 'none';
    }
});

// ====== 复制到剪贴板 ======
async function copyText(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('已复制：' + text, 'success');
    } catch (e) {
        // 兼容旧浏览器
        const input = document.createElement('input');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        try {
            document.execCommand('copy');
            showToast('已复制：' + text, 'success');
        } catch (err) {
            showToast('复制失败，请手动复制', 'error');
        }
        document.body.removeChild(input);
    }
}

// ====== 颜色生成 ======
function generateColors(n) {
    const palette = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe', '#fa709a',
        '#2ecc71', '#ffa502', '#ff4757', '#26de81', '#fc5c65',
        '#45aaf2', '#fd9644', '#a55eea', '#778ca3', '#20bf6b',
    ];
    const colors = [];
    for (let i = 0; i < n; i++) {
        colors.push(palette[i % palette.length]);
    }
    return colors;
}

// ====== 任务状态判断 ======
function isTaskActive(task) {
    return task.status === 'running';
}

function isTaskDone(task) {
    return task.status === 'completed';
}

function isTaskFailed(task) {
    return task.status === 'uncompleted';
}

// ====== 跨日兼容性：日期解析 ======
function parseDate(dateStr) {
    if (!dateStr) return null;
    const [y, m, d] = dateStr.split('-').map(Number);
    return new Date(y, m - 1, d);
}

// ====== 每日激励语 ======
const MOTIVATIONS = [
    '今天的你，比昨天更努力 💪',
    '坚持就是胜利 ✨',
    '专注当下，未来可期 🎯',
    '学习是最好的投资 💎',
    '一步一步，登上山顶 🏔️',
    '时间不等人，把握当下 ⏰',
    '坚持 21 天，养成好习惯 🌱',
    '今天的汗水，明天的荣耀 🏆',
    '不积跬步，无以至千里 🚀',
    '心无旁骛，万事可成 🧘',
];

function getRandomMotivation() {
    return MOTIVATIONS[Math.floor(Math.random() * MOTIVATIONS.length)];
}
