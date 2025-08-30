import React, { useState, useEffect, useRef } from 'react';
import { Activity, Play, Pause, Square, Plus, Eye, RefreshCw, Clock, X } from 'lucide-react';
import { CustomSelect, CustomInput, AnimatedButton, GlassCard, StatusBadge } from '../components/basic';
import { api } from '../BackendAPI';

// 任务管理页面
const TaskPage = () => {
    const [tasks, setTasks] = useState([]);
    const [logs, setLogs] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [selectedTaskId, setSelectedTaskId] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newTask, setNewTask] = useState({
        account: 'paper',
        market: 'HK',
        symbols: '',
        strategy: '',
        trading_sessions: []
    });
    const logsEndRef = useRef(null);

    const accountOptions = [
        { value: 'paper', label: '模拟账户' },
        { value: 'live', label: '实盘账户' }
    ];

    const marketOptions = [
        { value: 'HK', label: '港股' },
        { value: 'US', label: '美股' }
    ];

    const fetchTasks = () => {
        api.fetchTasks().then(data => {
            console.log(data)
            setTasks(data.tasks || []);
        });
    };

    const fetchLogs = () => {
        if (!selectedTaskId) return;
        api.fetchLogs(selectedTaskId).then(data => {
            setLogs(data.logs || []);
        });
    };

    const createTask = () => {
        api.createTask(newTask).then(success => {
            if (success) {
                setShowCreateForm(false);
                setNewTask({ account: 'paper', market: 'HK', symbols: '', strategy: '', trading_sessions: [] });
                fetchTasks();
            }
        });
    };

    const handleTaskAction = (taskId, action) => {
        api.handleTaskAction(taskId, action).then(success => {
            if (success) {
                fetchTasks();
            }
        });
    };

    useEffect(() => {
        fetchTasks();
        api.fetchStrategies().then(data => {
            setStrategies(data?.strategies?.map(s => ({ value: s, label: s })) || []);
        });
        const interval = setInterval(fetchLogs, 60000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        fetchLogs();
    }, [selectedTaskId]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        console.log(logs)
    }, [logs]);


    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                    任务管理
                </h1>
                <AnimatedButton onClick={() => setShowCreateForm(true)}>
                    <Plus className="w-4 h-4" />
                    新建任务
                </AnimatedButton>
            </div>

            {/* 创建任务表单 */}
            {showCreateForm && (
                <GlassCard className="border-l-4 border-l-blue-500">
                    <h3 className="text-2xl font-semibold mb-6 text-gray-900">创建新任务</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">账户类型</label>
                            <CustomSelect
                                value={newTask.account}
                                onChange={(value) => setNewTask({ ...newTask, account: value })}
                                options={accountOptions}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">市场</label>
                            <CustomSelect
                                value={newTask.market}
                                onChange={(value) => setNewTask({ ...newTask, market: value })}
                                options={marketOptions}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">股票代码</label>
                            <CustomInput
                                placeholder="多个代码用逗号分隔"
                                value={newTask.symbols}
                                onChange={(e) => setNewTask({ ...newTask, symbols: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-3">策略</label>
                            <CustomSelect
                                value={newTask.strategy}
                                onChange={(value) => setNewTask({ ...newTask, strategy: value })}
                                options={strategies}
                                placeholder="选择策略"
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-4 mt-8">
                        <AnimatedButton onClick={() => setShowCreateForm(false)} variant="secondary">
                            取消
                        </AnimatedButton>
                        <AnimatedButton onClick={createTask} disabled={!newTask.strategy || !newTask.symbols}>
                            创建任务
                        </AnimatedButton>
                    </div>
                </GlassCard>
            )}

            {/* 任务列表 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <Activity className="w-6 h-6 mr-3 text-green-600" />
                    任务列表
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">ID</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">策略</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">市场</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">股票代码</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">状态</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map(task => (
                                <tr key={task.task_id} className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                                    <td className="py-4 px-6 font-mono font-bold text-blue-600">#{task.task_id}</td>
                                    <td className="py-4 px-6 font-medium text-gray-900">{task.strategy}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={task.market} type="market" />
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="max-w-xs">
                                            <span className="text-gray-700 font-mono text-sm">{task.symbols?.join(', ')}</span>
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={task.status} type="task" />
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setSelectedTaskId(selectedTaskId === task.task_id ? null : task.task_id)}
                                                className="p-2 hover:bg-blue-100 rounded-xl text-blue-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                                                title="查看日志"
                                            >
                                                <Eye className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleTaskAction(task.task_id, 'start')}
                                                className="p-2 hover:bg-red-100 rounded-xl text-red-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
                                                title="开始"
                                                disabled={task.status === 'running'}
                                            >
                                                <Play className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleTaskAction(task.task_id, 'pause')}
                                                className="p-2 hover:bg-yellow-100 rounded-xl text-yellow-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-1"
                                                title="暂停"
                                                disabled={task.status !== 'running'}
                                            >
                                                <Pause className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleTaskAction(task.task_id, 'stop')}
                                                className="p-2 hover:bg-green-100 rounded-xl text-green-600 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
                                                title="停止"
                                                disabled={task.status === 'stopped'}
                                            >
                                                <Square className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>

            {/* 任务日志 */}
            {selectedTaskId && (
                <GlassCard>
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-2xl font-semibold flex items-center">
                            <Clock className="w-6 h-6 mr-3 text-blue-600" />
                            任务 #{selectedTaskId} 日志
                        </h3>
                        <AnimatedButton onClick={fetchLogs} variant="secondary" size="small">
                            <RefreshCw className="w-4 h-4" />
                            刷新日志
                        </AnimatedButton>
                    </div>
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 h-80 overflow-y-auto text-sm font-mono shadow-inner">
                        {logs.length === 0 ? (
                            <div className="text-gray-400 text-center py-12 text-base">暂无日志数据</div>
                        ) : (
                            logs.map((log, index) => (
                                <div key={index} className="text-green-400 mb-2 hover:bg-gray-800/50 p-1 rounded transition-colors">
                                    <span className="text-gray-500">[{log.created_at}]</span><span className="text-orange-500">[{log.symbol}] </span><span className={`${log.operation == "buy" ? "text-red-500" : "text-green-500"}`}>{log.operation.toUpperCase()}</span>
                                    <span className="text-yellow-300 font-bold"> {log.quantity}</span> <span className="text-gray-500">x</span> <span className="text-blue-400 font-bold">{log.price}</span>
                                </div>
                            ))
                        )}
                        <div ref={logsEndRef} />
                    </div>
                </GlassCard>
            )}
        </div>
    );
};

export default TaskPage;