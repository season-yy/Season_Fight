/* ==========================================
 * Season_Fight 主控制器 - 新版 UI 适配
 * ========================================== */

const App = {
    currentMainTab: 'home',  // 'home' | 'calendar' | 'stats' | 'history'

    /** 应用初始化 */
    init() {
        this.startClock();
        this.bindBottomNav();
        this.bindFabButton();
        this.bindInfoButton();

        // 初始化子模块
        Tasks.init();
        Timer.init();
        Calendar.init();
        History.init();

        // 加载概览
        this.refreshOverview();

        // 定时刷新
        setInterval(() => {
            this.refreshOverview();
        }, 30000);
    },

    /** 顶部时钟 */
    startClock() {
        const update = () => {
            const now = new Date();
            const h = String(now.getHours()).padStart(2, '0');
            const m = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('live-clock').textContent = `${h}:${m}`;
            document.getElementById('live-date').textContent = formatDate(now);
        };
        update();
        setInterval(update, 30000);  // 30秒更新一次（分钟级）
    },

    /** 底部 Tab 切换 */
    bindBottomNav() {
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                this.switchTab(tab);
            });
        });
    },

    /** 切换主 Tab */
    switchTab(tab) {
        this.currentMainTab = tab;
        // 切换 nav 按钮
        document.querySelectorAll('.nav-item').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tab);
        });
        // 切换内容
        const taskSection = document.querySelector('.task-section');
        const tabs = ['calendar', 'stats', 'history'];

        if (tab === 'home') {
            // 主页：显示任务区，隐藏所有 tab-content
            if (taskSection) taskSection.style.display = '';
            tabs.forEach(t => {
                const el = document.getElementById(`tab-content-${t}`);
                if (el) el.style.display = 'none';
            });
        } else {
            // 其他 Tab：隐藏任务区，显示对应 tab-content
            if (taskSection) taskSection.style.display = 'none';
            tabs.forEach(t => {
                const el = document.getElementById(`tab-content-${t}`);
                if (el) el.style.display = (t === tab) ? 'block' : 'none';
            });
            // 首次激活时加载数据
            if (tab === 'stats' && !Stats.charts.keywords) {
                Stats.renderAll();
            }
            if (tab === 'history') {
                History.render();
            }
            if (tab === 'calendar') {
                Calendar.render();
            }
        }
    },

    /** FAB 添加任务按钮 */
    bindFabButton() {
        const fab = document.getElementById('btn-open-add-task');
        if (fab) {
            fab.addEventListener('click', () => {
                // 重置 + 打开弹窗
                document.getElementById('task-name').value = '';
                document.getElementById('is-planned').checked = false;
                document.getElementById('planned-date').disabled = true;
                document.getElementById('planned-date').value = dateOffset(1);
                openModal('modal-add-task');
                setTimeout(() => document.getElementById('task-name').focus(), 300);
            });
        }
    },

    /** 访问信息按钮 */
    bindInfoButton() {
        document.getElementById('btn-info').addEventListener('click', async () => {
            openModal('modal-info');
            try {
                const data = await api('/api/server/info');
                const lanUrl = `http://${data.local_ip}:${data.port}`;
                document.getElementById('info-lan').textContent = lanUrl;
                document.getElementById('btn-copy-lan').onclick = () => copyText(lanUrl);
            } catch (e) {
                document.getElementById('info-lan').textContent = '获取失败';
            }
        });
    },

    /** 刷新今日概览 */
    async refreshOverview() {
        try {
            const data = await api('/api/stats/today');
            const stats = data.stats || {};

            document.getElementById('stat-completed').textContent = stats.completed || 0;
            document.getElementById('stat-uncompleted').textContent = stats.uncompleted || 0;
            document.getElementById('stat-modified').textContent = stats.modified || 0;
            document.getElementById('stat-rate').textContent =
                Math.round((stats.completion_rate || 0) * 100) + '%';

            // 更新激励语
            const rate = stats.completion_rate || 0;
            const completed = stats.completed || 0;
            const total = stats.total || 0;
            let motivation;
            if (total === 0) {
                motivation = '开始添加你的第一个任务吧 ✨';
            } else if (rate >= 1) {
                motivation = '完美！今日任务全部完成 🎉';
            } else if (rate >= 0.8) {
                motivation = '快完成了，再坚持一下 🏆';
            } else if (rate >= 0.5) {
                motivation = '已经过半，继续加油 💪';
            } else if (completed > 0) {
                motivation = '别放弃，一步步来 🚀';
            } else {
                motivation = '万事开头难，迈出第一步 ✨';
            }
            document.getElementById('motivation-text').textContent = motivation;
        } catch (e) {
            console.error('刷新概览失败:', e);
        }
    },

    /** 显示庆祝弹窗 */
    async showCelebrate() {
        openModal('modal-celebrate');
        try {
            const data = await api(`/api/stats/pie/${todayStr()}`);
            const canvas = document.getElementById('celebrate-pie-chart');
            if (!canvas) return;

            if (window.celebratePieChart) window.celebratePieChart.destroy();

            if (!data.items || data.items.length === 0) {
                canvas.parentNode.innerHTML = '<p style="text-align:center; color:#7f8c8d; padding:20px;">今天还没有计时数据</p>';
                return;
            }

            window.celebratePieChart = new Chart(canvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: data.items.map(i => i.name),
                    datasets: [{
                        data: data.items.map(i => i.seconds),
                        backgroundColor: generateColors(data.items.length),
                        borderColor: '#fff',
                        borderWidth: 3,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' },
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
        } catch (e) {
            console.error('庆祝弹窗饼图渲染失败:', e);
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});