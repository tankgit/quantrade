import { API_BASE } from "./config/config";

export const api = {

    async getAccountBalance(accountType, currency = 'USD') {
        try {
            const response = await fetch(`${API_BASE}/api/account/${accountType}/balance?currency=${currency}`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取余额失败');
            }
        } catch (error) {
            console.error('获取余额失败:', error);
        }
    },

    async getAccountPostions(accountType) {
        try {
            const response = await fetch(`${API_BASE}/api/account/${accountType}/positions`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取持仓失败');
            }
        } catch (error) {
            console.error('获取持仓失败:', error);
        }
    },

    async getAccountSummary(accountType) {
        try {
            const response = await fetch(`${API_BASE}/api/account/${accountType}/summary`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取账户信息失败');
            }
        } catch (error) {
            console.error('获取账户信息失败:', error);
        }
    },

    async fetchTasks() {
        try {
            const response = await fetch(`${API_BASE}/api/tasks`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取任务失败');
            }
        } catch (error) {
            console.error('获取任务失败:', error);
        }
    },

    async fetchStrategies() {
        try {
            const response = await fetch(`${API_BASE}/api/strategies`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取策略失败');
            }
        } catch (error) {
            console.error('获取策略失败:', error);
        }
    },

    async fetchLogs(selectedTaskId) {
        try {
            const response = await fetch(`${API_BASE}/api/tasks/${selectedTaskId}/logs`);
            const data = await response.json();
            if (data.success) {
                return data.data;
            } else {
                throw new Error(data || '获取日志失败');
            }
        } catch (error) {
            console.error('获取日志失败:', error);
        }
    },

    async createTask(newTask) {
        try {
            const symbols = newTask.symbols.split(',').map(s => s.trim()).filter(s => s);
            const response = await fetch(`${API_BASE}/api/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...newTask, symbols })
            });
            const data = await response.json();
            return data.success
        } catch (error) {
            console.error('创建任务失败:', error);
        }
    },

    async handleTaskAction(taskId, action) {
        try {
            const response = await fetch(`${API_BASE}/api/tasks/${taskId}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: action === 'start' ? JSON.stringify({ task_id: taskId }) : undefined
            });
            const data = await response.json();
            return data.success
        } catch (error) {
            console.error(`${action}任务失败:`, error);
        }
    }

}