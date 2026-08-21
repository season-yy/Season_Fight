/* ==========================================
 * 计时器引擎 - 新版 UI 适配
 * ========================================== */

const Timer = {
    intervalId: null,
    currentTask: null,
    baseSeconds: 0,
    startTimestamp: null,
    isPaused: false,

    /** 初始化 */
    init() {
        this.bindEvents();
        this.setStatus('idle');  // 初始显式设置状态（避免 HTML 默认文本被遗漏）
        this.checkRunningTask();
    },

    /** 绑定事件 */
    bindEvents() {
        // 完成按钮
        const completeBtn = document.getElementById('btn-complete-timer');
        if (completeBtn) {
            completeBtn.addEventListener('click', () => {
                if (this.currentTask) Tasks.completeTask(this.currentTask.id);
            });
        }

        // 暂停/继续按钮
        const pauseBtn = document.getElementById('btn-pause-timer');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                if (!this.currentTask) return;
                if (this.isPaused) this.resume();
                else this.pause();
            });
        }
    },

    /** 检查是否有正在运行的任务 */
    async checkRunningTask() {
        try {
            const data = await api(`/api/tasks?date=${todayStr()}`);
            const running = (data.tasks || []).find(t => t.status === 'running');
            if (running) this.start(running);
            else this.reset();
        } catch (e) {
            console.error('检查运行任务失败:', e);
        }
    },

    /** 启动计时器 */
    start(task) {
        if (!task || task.status !== 'running') return;

        this.currentTask = task;
        this.baseSeconds = task.duration_seconds || 0;
        this.startTimestamp = new Date(task.started_at).getTime();
        this.isPaused = false;

        // 更新显示
        this.updateDisplay(this.baseSeconds);
        this.setStatus('running');

        const card = document.querySelector('.timer-card');
        if (card) {
            card.classList.add('is-running');
            card.classList.remove('is-paused');
        }

        // 启用按钮
        const completeBtn = document.getElementById('btn-complete-timer');
        const pauseBtn = document.getElementById('btn-pause-timer');
        if (completeBtn) completeBtn.disabled = false;
        if (pauseBtn) {
            pauseBtn.disabled = false;
            pauseBtn.querySelector('.action-icon').textContent = '⏸';
            pauseBtn.querySelector('span:last-child').textContent = '暂停';
        }

        // 启动轮询
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = setInterval(() => this.tick(), 1000);
    },

    /** 每秒更新 */
    tick() {
        if (!this.currentTask || !this.startTimestamp) return;
        const now = Date.now();
        const elapsed = Math.floor((now - this.startTimestamp) / 1000) + this.baseSeconds;
        this.updateDisplay(elapsed);
    },

    /** 更新显示 */
    updateDisplay(seconds) {
        const display = document.getElementById('timer-display');
        const duration = document.getElementById('timer-duration');
        if (display) display.textContent = formatTime(seconds);
        if (duration) duration.textContent = formatDuration(seconds);
    },

    /** 设置状态文本 */
    setStatus(status) {
        const dot = document.querySelector('#timer-status .status-dot');
        const text = document.querySelector('#timer-status .status-text');
        if (!dot || !text) return;

        if (status === 'running') {
            dot.className = 'status-dot running';
            text.textContent = '🔥 认真专注集中中';
        } else if (status === 'paused') {
            dot.className = 'status-dot paused';
            text.textContent = '⏸ 已暂停';
        } else {
            dot.className = 'status-dot idle';
            text.textContent = '待机中';
        }
    },

    /** 暂停 */
    pause() {
        if (!this.currentTask || this.isPaused) return;

        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = null;

        const now = Date.now();
        const elapsed = Math.floor((now - this.startTimestamp) / 1000) + this.baseSeconds;
        this.baseSeconds = elapsed;
        this.startTimestamp = null;
        this.isPaused = true;

        // 视觉提示
        const card = document.querySelector('.timer-card');
        if (card) {
            card.classList.remove('is-running');
            card.classList.add('is-paused');
        }
        this.setStatus('paused');
        this.updateDisplay(this.baseSeconds);

        const pauseBtn = document.getElementById('btn-pause-timer');
        if (pauseBtn) {
            pauseBtn.querySelector('.action-icon').textContent = '▶';
            pauseBtn.querySelector('span:last-child').textContent = '继续';
        }

        // 调用后端
        api(`/api/timer/pause/${this.currentTask.id}`, { method: 'POST' })
            .then(() => showToast('已暂停 ⏸', 'info'))
            .catch(err => {
                console.error('暂停失败:', err);
                showToast('暂停失败', 'error');
            });
    },

    /** 恢复 */
    async resume() {
        if (!this.currentTask || !this.isPaused) return;
        try {
            const data = await api(`/api/timer/start/${this.currentTask.id}`, { method: 'POST' });
            this.start(data.task);
            showToast('继续计时 ▶', 'info');
            if (typeof Tasks !== 'undefined') Tasks.renderToday();
        } catch (e) {
            showToast('继续失败', 'error');
        }
    },

    /** 停止（任务完成后） */
    stop() {
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = null;
        this.currentTask = null;
        this.baseSeconds = 0;
        this.startTimestamp = null;
        this.isPaused = false;

        const display = document.getElementById('timer-display');
        if (display) display.textContent = '00:00:00';

        const taskName = document.getElementById('timer-task-name');
        if (taskName) {
            taskName.textContent = '选择下方任务开始计时';
            taskName.classList.add('empty');
        }

        const duration = document.getElementById('timer-duration');
        if (duration) duration.textContent = '0 分钟';

        const card = document.querySelector('.timer-card');
        if (card) {
            card.classList.remove('is-running', 'is-paused');
        }
        this.setStatus('idle');

        const completeBtn = document.getElementById('btn-complete-timer');
        const pauseBtn = document.getElementById('btn-pause-timer');
        if (completeBtn) completeBtn.disabled = true;
        if (pauseBtn) {
            pauseBtn.disabled = true;
            pauseBtn.querySelector('.action-icon').textContent = '⏸';
            pauseBtn.querySelector('span:last-child').textContent = '暂停';
        }
    },

    /** 重置 */
    reset() {
        this.stop();
    },
};