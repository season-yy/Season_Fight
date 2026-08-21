/* ==========================================
 * 任务管理 - 新版 UI 适配
 * ========================================== */

const Tasks = {
    currentTab: 'today',     // 'today' | 'plans'
    editingId: null,
    deletingId: null,

    init() {
        this.bindEvents();
        this.renderToday();

        // 日期选择器默认值
        const dateInput = document.getElementById('planned-date');
        if (dateInput) {
            dateInput.min = todayStr();
            dateInput.max = dateOffset(window.APP_CONFIG.maxPlanDays);
            dateInput.value = dateOffset(1);
        }
    },

    bindEvents() {
        // 添加任务（弹窗内按钮）
        const addBtn = document.getElementById('btn-add-task');
        if (addBtn) addBtn.addEventListener('click', () => this.handleAdd());

        // 任务名回车提交
        const nameInput = document.getElementById('task-name');
        if (nameInput) {
            nameInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.handleAdd();
            });
        }

        // 规划未来勾选框
        const planCheck = document.getElementById('is-planned');
        if (planCheck) {
            planCheck.addEventListener('change', (e) => {
                const dateInput = document.getElementById('planned-date');
                if (dateInput) dateInput.disabled = !e.target.checked;
            });
        }

        // Tab 切换
        document.querySelectorAll('.task-tabs .task-tab').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // 编辑保存
        const saveBtn = document.getElementById('btn-save-edit');
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveEdit());

        // 删除确认
        const delBtn = document.getElementById('btn-confirm-delete');
        if (delBtn) delBtn.addEventListener('click', () => this.confirmDelete());
    },

    switchTab(tab) {
        this.currentTab = tab;
        document.querySelectorAll('.task-tabs .task-tab').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tab);
        });
        if (tab === 'today') this.renderToday();
        else this.renderPlans();
    },

    async renderToday() {
        const container = document.getElementById('task-list-container');
        container.innerHTML = '<div class="loading-tip">加载中...</div>';
        try {
            const data = await api(`/api/tasks?date=${todayStr()}`);
            this.renderTaskList(data.tasks || [], container, 'today');
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">加载失败</div></div>`;
        }
    },

    async renderPlans() {
        const container = document.getElementById('task-list-container');
        container.innerHTML = '<div class="loading-tip">加载中...</div>';
        try {
            const data = await api('/api/plans/range');
            const allTasks = [];
            (data.plans || []).forEach(p => {
                p.tasks.forEach(t => allTasks.push({...t, planned_date: p.date}));
            });
            this.renderTaskList(allTasks, container, 'plans');
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">加载失败</div></div>`;
        }
    },

    renderTaskList(tasks, container, mode) {
        if (!tasks || tasks.length === 0) {
            const emptyMsg = mode === 'today'
                ? '还没有任务，点击右下角 + 添加吧！'
                : '还没有未来计划，规划一些吧～';
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">${mode === 'today' ? '📝' : '📅'}</div>
                    <div class="empty-state-text">${emptyMsg}</div>
                </div>`;
            return;
        }
        container.innerHTML = tasks.map(task => this.renderTaskItem(task, mode)).join('');
    },

    renderTaskItem(task, mode) {
        const statusClass = `task-${task.status}`;
        const modifiedClass = task.is_modified ? 'is-modified' : '';
        const plannedClass = task.is_planned || mode === 'plans' ? 'is-planned' : '';

        let actions = '';
        if (mode === 'today') {
            actions = `
                <button class="task-btn btn-start" onclick="Tasks.startTask('${task.id}')" title="开始计时" ${task.status === 'running' || task.status === 'completed' ? 'disabled' : ''}>▶ 开始</button>
                <button class="task-btn btn-complete" onclick="Tasks.completeTask('${task.id}')" title="完成" ${task.status === 'completed' ? 'disabled' : ''}>✔ 完成</button>
                <button class="task-btn btn-edit" onclick="Tasks.editTask('${task.id}')" title="编辑">✏️</button>
                <button class="task-btn btn-delete" onclick="Tasks.deleteTask('${task.id}')" title="删除">🗑️</button>
            `;
        } else {
            actions = `
                <button class="task-btn btn-edit" onclick="Tasks.editTask('${task.id}')" title="编辑">✏️</button>
                <button class="task-btn btn-delete" onclick="Tasks.deleteTask('${task.id}')" title="删除">🗑️</button>
            `;
        }

        const plannedInfo = mode === 'plans'
            ? `<span class="task-duration">📅 ${formatDateShort(task.planned_date)}</span>`
            : '';

        return `
            <div class="task-card ${statusClass} ${modifiedClass} ${plannedClass}" data-id="${task.id}">
                <div class="task-header">
                    <div class="task-name">${escapeHtml(task.name)}</div>
                </div>
                <div class="task-meta">
                    <span class="task-category">${escapeHtml(task.category)}</span>
                    <span class="task-duration">⏱️ ${formatDuration(task.duration_seconds)}</span>
                    ${this.statusBadge(task.status)}
                    ${plannedInfo}
                </div>
                ${task.history && task.history.length > 0 ? `
                    <div class="task-history">
                        📝 修改 ${task.history.length} 次 · 最近：${escapeHtml(task.history[task.history.length - 1].reason)}
                    </div>
                ` : ''}
                <div class="task-actions">${actions}</div>
            </div>
        `;
    },

    statusBadge(status) {
        const map = {
            'pending': '<span class="task-badge">待开始</span>',
            'running': '<span class="task-badge" style="background:#4facfe">进行中</span>',
            'paused': '<span class="task-badge paused">已暂停</span>',
            'completed': '<span class="task-badge completed">已完成</span>',
            'uncompleted': '<span class="task-badge uncompleted">未完成</span>',
        };
        return map[status] || '';
    },

    async handleAdd() {
        const name = document.getElementById('task-name').value.trim();
        const category = document.getElementById('task-category').value;
        const isPlanned = document.getElementById('is-planned').checked;
        const plannedDate = document.getElementById('planned-date').value;

        if (!name) {
            showToast('请填写任务名', 'warning');
            return;
        }

        try {
            const payload = { name, category };
            if (isPlanned && plannedDate) {
                payload.planned_date = plannedDate;
            }
            await api('/api/tasks', { method: 'POST', body: payload });
            showToast(isPlanned ? `已规划到 ${formatDateShort(plannedDate)}` : '任务已添加', 'success');
            closeModal('modal-add-task');
            if (this.currentTab === 'today') this.renderToday();
            else this.renderPlans();
            App.refreshOverview();
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async startTask(taskId) {
        try {
            const data = await api(`/api/timer/start/${taskId}`, { method: 'POST' });
            showToast('计时开始 ⏱️', 'success');
            this.renderToday();
            App.refreshOverview();
            Timer.start(data.task);
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async completeTask(taskId) {
        try {
            const data = await api(`/api/timer/complete/${taskId}`, { method: 'POST' });
            showToast('任务已完成 🎉', 'success');
            Timer.stop();
            this.renderToday();
            App.refreshOverview();
            this.checkAllComplete();
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async checkAllComplete() {
        try {
            const data = await api(`/api/tasks?date=${todayStr()}`);
            const tasks = data.tasks || [];
            const hasIncomplete = tasks.some(t =>
                t.status === 'pending' || t.status === 'running' || t.status === 'paused'
            );
            if (!hasIncomplete && tasks.length > 0) {
                setTimeout(() => App.showCelebrate(), 300);
            }
        } catch (e) {}
    },

    async editTask(taskId) {
        this.editingId = taskId;
        try {
            const data = await api(`/api/tasks?date=${todayStr()}`);
            const task = data.tasks.find(t => t.id === taskId);
            if (task) {
                document.getElementById('edit-name').value = task.name;
                document.getElementById('edit-category').value = task.category;
                document.getElementById('edit-reason').value = '';
                openModal('modal-edit');
            }
        } catch (e) {
            showToast('加载任务失败', 'error');
        }
    },

    async saveEdit() {
        const name = document.getElementById('edit-name').value.trim();
        const category = document.getElementById('edit-category').value;
        const reason = document.getElementById('edit-reason').value.trim();

        if (!name) {
            showToast('请填写任务名', 'warning');
            return;
        }
        if (!reason || reason.length < 2) {
            showToast('请填写修改理由（至少 2 个字）', 'warning');
            return;
        }

        try {
            await api(`/api/tasks/${this.editingId}`, {
                method: 'PATCH',
                body: { name, category, reason },
            });
            showToast('修改已保存 ✏️', 'success');
            closeModal('modal-edit');
            this.editingId = null;
            if (this.currentTab === 'today') this.renderToday();
            else this.renderPlans();
            App.refreshOverview();
        } catch (e) {
            showToast(e.message, 'error');
        }
    },

    async deleteTask(taskId) {
        this.deletingId = taskId;
        try {
            const data = await api(`/api/tasks?date=${todayStr()}`);
            const task = data.tasks.find(t => t.id === taskId);
            if (task) {
                document.getElementById('delete-task-info').innerHTML = `
                    <strong>任务：</strong>${escapeHtml(task.name)}<br>
                    <strong>分类：</strong>${escapeHtml(task.category)}<br>
                    <strong>已用时：</strong>${formatDuration(task.duration_seconds)}
                `;
                document.getElementById('delete-reason').value = '';
                openModal('modal-delete');
            }
        } catch (e) {
            showToast('加载任务失败', 'error');
        }
    },

    async confirmDelete() {
        const reason = document.getElementById('delete-reason').value.trim();
        if (!reason || reason.length < 2) {
            showToast('请填写删除理由（至少 2 个字）', 'warning');
            return;
        }
        try {
            await api(`/api/tasks/${this.deletingId}?reason=${encodeURIComponent(reason)}`, {
                method: 'DELETE',
            });
            showToast('任务已删除 🗑️', 'success');
            closeModal('modal-delete');
            this.deletingId = null;
            if (this.currentTab === 'today') this.renderToday();
            else this.renderPlans();
            App.refreshOverview();
        } catch (e) {
            showToast(e.message, 'error');
        }
    },
};