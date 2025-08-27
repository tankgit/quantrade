import React, { useState, useEffect, useRef } from 'react';
import { Activity, TrendingUp, BarChart3, Target, Settings, RefreshCw, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE } from "../config/config";
import { AnimatedButton, GlassCard, LoadingSpinner } from '../components/basic';

// 系统状态页面
const StatusPage = () => {
    const [systemStatus, setSystemStatus] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchSystemStatus();
        const interval = setInterval(fetchSystemStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchSystemStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/status`);
            const data = await response.json();
            setSystemStatus(data || {});
        } catch (error) {
            console.error('获取系统状态失败:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner />;

    const mockSystemData = {
        uptime: '12天 5小时 32分钟',
        cpu_usage: 45.2,
        memory_usage: 68.7,
        active_tasks: 5,
        total_trades_today: 127,
        api_health: 'healthy'
    };

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    系统状态
                </h1>
                <AnimatedButton onClick={fetchSystemStatus} variant="secondary">
                    <RefreshCw className="w-4 h-4" />
                    刷新状态
                </AnimatedButton>
            </div>

            {/* 系统概览 */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">系统运行时间</p>
                            <p className="text-2xl font-bold text-blue-600 mb-2">{mockSystemData.uptime}</p>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl shadow-lg">
                            <Clock className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-emerald-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">CPU使用率</p>
                            <p className="text-2xl font-bold text-emerald-600 mb-2">{mockSystemData.cpu_usage}%</p>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-2xl shadow-lg">
                            <Activity className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-yellow-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">内存使用率</p>
                            <p className="text-2xl font-bold text-yellow-600 mb-2">{mockSystemData.memory_usage}%</p>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-2xl shadow-lg">
                            <Settings className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-purple-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">活跃任务</p>
                            <p className="text-2xl font-bold text-purple-600 mb-2">{mockSystemData.active_tasks}</p>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl shadow-lg">
                            <Target className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* API健康状态 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <Activity className="w-6 h-6 mr-3 text-red-600" />
                    API服务状态
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-green-100 rounded-2xl border border-green-200">
                        <div>
                            <p className="font-semibold text-green-900 text-lg">交易服务</p>
                            <p className="text-sm text-green-700 mt-1">正常运行</p>
                        </div>
                        <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse shadow-lg"></div>
                    </div>
                    <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-green-100 rounded-2xl border border-green-200">
                        <div>
                            <p className="font-semibold text-green-900 text-lg">数据服务</p>
                            <p className="text-sm text-green-700 mt-1">正常运行</p>
                        </div>
                        <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse shadow-lg"></div>
                    </div>
                    <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-green-100 rounded-2xl border border-green-200">
                        <div>
                            <p className="font-semibold text-green-900 text-lg">风控服务</p>
                            <p className="text-sm text-green-700 mt-1">正常运行</p>
                        </div>
                        <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse shadow-lg"></div>
                    </div>
                </div>
            </GlassCard>

            {/* 系统性能图表 */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <BarChart3 className="w-6 h-6 mr-3 text-blue-600" />
                        系统负载监控
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <LineChart data={[
                            { time: '10:00', cpu: 35, memory: 45 },
                            { time: '11:00', cpu: 42, memory: 52 },
                            { time: '12:00', cpu: 38, memory: 48 },
                            { time: '13:00', cpu: 45, memory: 68 },
                            { time: '14:00', cpu: 41, memory: 65 },
                            { time: '15:00', cpu: 39, memory: 58 }
                        ]} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis
                                dataKey="time"
                                tick={{ fontSize: 12 }}
                                axisLine={{ stroke: '#e5e7eb' }}
                                tickLine={{ stroke: '#e5e7eb' }}
                            />
                            <YAxis
                                tick={{ fontSize: 12 }}
                                axisLine={{ stroke: '#e5e7eb' }}
                                tickLine={{ stroke: '#e5e7eb' }}
                            />
                            <Tooltip
                                formatter={(value, name) => [`${value}%`, name]}
                                contentStyle={{
                                    background: 'rgba(255, 255, 255, 0.95)',
                                    backdropFilter: 'blur(10px)',
                                    border: 'none',
                                    borderRadius: '12px',
                                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)'
                                }}
                            />
                            <Line
                                type="monotone"
                                dataKey="cpu"
                                stroke="#3b82f6"
                                strokeWidth={3}
                                name="CPU使用率"
                                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                                activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="memory"
                                stroke="#16a34a"
                                strokeWidth={3}
                                name="内存使用率"
                                dot={{ fill: '#16a34a', strokeWidth: 2, r: 4 }}
                                activeDot={{ r: 6, stroke: '#16a34a', strokeWidth: 2 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </GlassCard>

                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <TrendingUp className="w-6 h-6 mr-3 text-red-600" />
                        今日交易统计
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-6 bg-gradient-to-r from-blue-50 to-blue-100 rounded-2xl border border-blue-200">
                            <div>
                                <p className="text-sm text-blue-700 mb-1">总交易次数</p>
                                <p className="text-3xl font-bold text-blue-600">{mockSystemData.total_trades_today}</p>
                            </div>
                            <div className="p-4 bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl shadow-lg">
                                <TrendingUp className="w-8 h-8 text-white" />
                            </div>
                        </div>
                        <div className="flex justify-between items-center p-6 bg-gradient-to-r from-red-50 to-red-100 rounded-2xl border border-red-200">
                            <div>
                                <p className="text-sm text-red-700 mb-1">成功交易</p>
                                <p className="text-3xl font-bold text-red-600">98</p>
                            </div>
                            <div className="text-right">
                                <div className="text-red-600 text-lg font-semibold">77.2%</div>
                                <div className="text-sm text-red-500">成功率</div>
                            </div>
                        </div>
                        <div className="flex justify-between items-center p-6 bg-gradient-to-r from-green-50 to-green-100 rounded-2xl border border-green-200">
                            <div>
                                <p className="text-sm text-green-700 mb-1">失败交易</p>
                                <p className="text-3xl font-bold text-green-600">29</p>
                            </div>
                            <div className="text-right">
                                <div className="text-green-600 text-lg font-semibold">22.8%</div>
                                <div className="text-sm text-green-500">失败率</div>
                            </div>
                        </div>
                    </div>
                </GlassCard>
            </div>
        </div>
    );
};

export default StatusPage;