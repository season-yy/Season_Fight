/* ==========================================
 * 日历视图 + 历史记录 - 新版 UI 适配
 * ========================================== */

const Calendar = {
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,

    /** 初始化 */
    init() {
        this.bindEvents();
    },

    /** 绑定事件 */
    bindEvents() {
        const prevBtn = document.getElementById('btn-prev-month');
        const nextBtn = document.getElementById('btn-next-month');
        if (prevBtn) prevBtn.addEventListener('click', () => this.changeMonth(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.changeMonth(1));
    },

    /** 切换月份 */
    changeMonth(offset) {
        this.currentMonth += offset;
        if (this.currentMonth > 12) {
            this.currentMonth = 1;
            this.currentYear++;
        } else if (this.currentMonth < 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        this.render();
    },

    /** 渲染日历 */
    async render() {
        const titleEl = document.getElementById('calendar-title');
        if (titleEl) titleEl.textContent = `${this.currentYear} 年 ${this.currentMonth} 月`;

        const container = document.getElementById('calendar-container');
        if (!container) return;
        container.innerHTML = '<div class="loading-tip">加载中...</div>';

        try {
            const data = await api(`/api/calendar?year=${this.currentYear}&month=${this.currentMonth}`);
            container.innerHTML = this.buildCalendarHTML(data);
        } catch (e) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📅</div><div class="empty-state-text">加载失败</div></div>';
        }
    },

    /** 构建日历 HTML */
    buildCalendarHTML(data) {
        const year = this.currentYear;
        const month = this.currentMonth;
        const firstDay = new Date(year, month - 1, 1).getDay();
        const daysInMonth = new Date(year, month, 0).getDate();
        const todayKey = todayStr();

        let html = '<div class="calendar-grid">';
        ['日', '一', '二', '三', '四', '五', '六'].forEach(d => {
            html += `<div class="calendar-header">${d}</div>`;
        });

        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-cell empty"></div>';
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const dateKey = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayInfo = data.days && data.days[dateKey];
            let rateClass = 'no-data';
            let rateText = '';
            let tooltip = dateKey;

            if (dayInfo) {
                rateClass = `rate-${dayInfo.status}`;
                const pct = Math.round(dayInfo.completion_rate * 100);
                rateText = `${pct}%`;
                tooltip = `${dateKey}\n任务数：${dayInfo.total}\n已完成：${dayInfo.completed}\n完成率：${pct}%`;
                if (dayInfo.modified > 0) tooltip += `\n修改过：${dayInfo.modified}`;
            }

            const isToday = dateKey === todayKey;
            const todayClass = isToday ? 'today' : '';

            html += `
                <div class="calendar-cell ${rateClass} ${todayClass}"
                     onclick="Calendar.showDayDetail('${dateKey}')"
                     title="${tooltip}">
                    <div class="calendar-day-num">${day}${isToday ? ' 📍' : ''}</div>
                    ${rateText ? `<div class="calendar-rate">${rateText}</div>` : ''}
                </div>
            `;
        }

        html += '</div>';
        return html;
    },

    /** 显示某日详情 */
    async showDayDetail(dateStr) {
        const titleEl = document.getElementById('day-detail-title');
        if (titleEl) titleEl.textContent = `📅 ${formatDate(dateStr)}`;
        openModal('modal-day-detail');

        try {
            const data = await api(`/api/day/${dateStr}`);

            // 渲染统计
            const stats = data.stats || {};
            const statsEl = document.getElementById('day-detail-stats');
            if (statsEl) {
                statsEl.innerHTML = `
                    <div class="detail-stat">
                        <div class="detail-stat-value">${stats.total || 0}</div>
                        <div class="detail-stat-label">总任务</div>
                    </div>
                    <div class="detail-stat">
                        <div class="detail-stat-value" style="color:#2ecc71">${stats.completed || 0}</div>
                        <div class="detail-stat-label">已完成</div>
                    </div>
                    <div class="detail-stat">
                        <div class="detail-stat-value" style="color:#ff4757">${stats.uncompleted || 0}</div>
                        <div class="detail-stat-label">未完成</div>
                    </div>
                    <div class="detail-stat">
                        <div class="detail-stat-value">${Math.round((stats.completion_rate || 0) * 100)}%</div>
                        <div class="detail-stat-label">完成率</div>
                    </div>
                `;
            }

            // 渲染任务列表
            const tasksHtml = (data.tasks || []).map(task => {
                const statusClass = `task-${task.status}`;
                const modifiedClass = task.is_modified ? 'is-modified' : '';
                return `
                    <div class="task-card ${statusClass} ${modifiedClass}" style="font-size:13px; padding:10px;">
                        <div class="task-header">
                            <div class="task-name">${escapeHtml(task.name)}</div>
                        </div>
                        <div class="task-meta">
                            <span class="task-category">${escapeHtml(task.category)}</span>
                            <span class="task-duration">⏱️ ${formatDuration(task.duration_seconds)}</span>
                            ${Tasks.statusBadge(task.status)}
                        </div>
                    </div>
                `;
            }).join('') || '<div class="empty-tip">当天没有任务</div>';

            const tasksEl = document.getElementById('day-detail-tasks');
            if (tasksEl) tasksEl.innerHTML = tasksHtml;

            // 渲染饼图
            this.renderDayDetailPie(data.pie);
        } catch (e) {
            showToast('加载详情失败', 'error');
        }
    },

    /** 渲染详情饼图 */
    renderDayDetailPie(pieData) {
        const canvas = document.getElementById('day-detail-pie-chart');
        if (!canvas) return;

        if (window.dayDetailPieChart) window.dayDetailPieChart.destroy();

        if (!pieData || !pieData.items || pieData.items.length === 0) {
            const wrapper = canvas.parentNode;
            wrapper.innerHTML = '<div class="empty-tip">当天没有计时数据</div>';
            return;
        }

        window.dayDetailPieChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: pieData.items.map(i => i.name),
                datasets: [{
                    data: pieData.items.map(i => i.seconds),
                    backgroundColor: generateColors(pieData.items.length),
                    borderColor: '#fff',
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { font: { size: 12 } } },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const sec = ctx.parsed;
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? (sec / total * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${formatDuration(sec)} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    },
};


// ==========================================
// 历史记录列表
// ==========================================
const History = {
    async render() {
        const container = document.getElementById('history-list');
        if (!container) return;
        container.innerHTML = '<div class="loading-tip">加载中...</div>';

        try {
            const items = [];
            const today = new Date();
            // 并行请求所有日期（提高速度）
            const promises = [];
            for (let i = 0; i < 30; i++) {
                const d = new Date(today);
                d.setDate(d.getDate() - i);
                const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
                promises.push(
                    api(`/api/day/${dateStr}`)
                        .then(data => {
                            if (data.tasks && data.tasks.length > 0) {
                                items.push({ date: dateStr, stats: data.stats });
                            }
                        })
                        .catch(() => {})
                );
            }
            await Promise.all(promises);

            if (items.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📜</div>
                        <div class="empty-state-text">暂无历史记录</div>
                    </div>`;
                return;
            }

            // 按日期降序
            items.sort((a, b) => b.date.localeCompare(a.date));

            container.innerHTML = items.map(item => {
                const rate = item.stats.completion_rate || 0;
                let rateClass = 'rate-poor';
                if (rate >= 0.8) rateClass = 'rate-excellent';
                else if (rate >= 0.5) rateClass = 'rate-good';
                else if (rate === 0 && item.stats.total > 0) rateClass = 'rate-failed';

                return `
                    <div class="history-item" onclick="Calendar.showDayDetail('${item.date}')">
                        <div class="history-info">
                            <div class="history-date">${formatDate(item.date)}</div>
                            <div class="history-stats">
                                <span>📝 总：${item.stats.total}</span>
                                <span>✅ 完成：${item.stats.completed}</span>
                                <span>❌ 未完成：${item.stats.uncompleted || 0}</span>
                                ${item.stats.modified > 0 ? `<span>✏️ 修改：${item.stats.modified}</span>` : ''}
                            </div>
                        </div>
                        <div class="history-rate ${rateClass}">
                            ${Math.round(rate * 100)}%
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">加载失败</div></div>';
        }
    },
};