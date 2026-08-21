/* ==========================================
 * 统计分析图表 - Chart.js 集成
 * ========================================== */

const Stats = {
    charts: {},
    initialized: false,

    /** 初始化（仅首次进入统计 Tab 时调用） */
    async init() {
        if (this.initialized) return;
        await this.renderAll();
        this.initialized = true;
    },

    /** 渲染所有图表 */
    async renderAll() {
        await Promise.all([
            this.renderKeywordsChart(),
            this.renderCategoryChart(),
            this.renderMonthlyTrend(),
        ]);
    },

    /** 关键词 Top 10 */
    async renderKeywordsChart() {
        const canvas = document.getElementById('chart-keywords');
        if (!canvas) return;

        if (this.charts.keywords) this.charts.keywords.destroy();

        try {
            const data = await api('/api/stats/keywords?days=30&top_n=10');
            const keywords = data.keywords || [];

            if (keywords.length === 0) {
                canvas.parentNode.innerHTML = '<div class="empty-tip">还没有未完成任务数据<br><br>💡 完成任务后这里会显示你最常拖延的内容</div>';
                return;
            }

            this.charts.keywords = new Chart(canvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: keywords.map(k => k[0]),
                    datasets: [{
                        label: '未完成次数',
                        data: keywords.map(k => k[1]),
                        backgroundColor: 'rgba(255, 71, 87, 0.75)',
                        borderColor: '#ff4757',
                        borderWidth: 2,
                        borderRadius: 6,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: { label: ctx => ` ${ctx.parsed.x} 次未完成` }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true, ticks: { stepSize: 1 } }
                    }
                }
            });
        } catch (e) {
            console.error('关键词图渲染失败:', e);
        }
    },

    /** 任务分类饼图 */
    async renderCategoryChart() {
        const canvas = document.getElementById('chart-categories');
        if (!canvas) return;

        if (this.charts.categories) this.charts.categories.destroy();

        try {
            const data = await api('/api/stats/categories?days=30');
            const categories = data.categories || [];

            if (categories.length === 0) {
                canvas.parentNode.innerHTML = '<div class="empty-tip">还没有任务分类数据</div>';
                return;
            }

            this.charts.categories = new Chart(canvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: categories.map(c => c.name),
                    datasets: [{
                        data: categories.map(c => c.count),
                        backgroundColor: generateColors(categories.length),
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
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? (ctx.parsed / total * 100).toFixed(1) : 0;
                                    return ` ${ctx.label}: ${ctx.parsed} 个 (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (e) {
            console.error('分类图渲染失败:', e);
        }
    },

    /** 月度完成率趋势 */
    async renderMonthlyTrend() {
        const canvas = document.getElementById('chart-monthly');
        if (!canvas) return;

        if (this.charts.monthly) this.charts.monthly.destroy();

        try {
            const now = new Date();
            const data = await api(`/api/stats/month?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
            const days = data.days || [];

            const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
            const dayMap = {};
            days.forEach(d => { dayMap[d.date.slice(-2)] = d.completion_rate * 100; });

            const labels = [];
            const values = [];
            for (let i = 1; i <= daysInMonth; i++) {
                const day = String(i).padStart(2, '0');
                labels.push(i + '日');
                values.push(dayMap[day] || 0);
            }

            this.charts.monthly = new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '完成率(%)',
                        data: values,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.15)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#667eea',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: { label: ctx => ` 完成率：${ctx.parsed.y.toFixed(0)}%` }
                        }
                    },
                    scales: {
                        y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } }
                    }
                }
            });
        } catch (e) {
            console.error('趋势图渲染失败:', e);
        }
    },
};