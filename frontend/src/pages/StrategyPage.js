import React, { useState, useEffect, useRef } from 'react';
import { Activity, TrendingUp, TrendingDown, BarChart3, Target, RefreshCw } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { AnimatedButton, GlassCard, LoadingSpinner, ValueDisplay, StatusBadge } from '../components/basic';

// 策略分析页面
const StrategyPage = () => {
    const [strategyData, setStrategyData] = useState([]);
    const [symbolData, setSymbolData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStrategyData();
    }, []);

    const fetchStrategyData = async () => {
        setLoading(true);
        try {
            // 模拟数据，实际应该从API获取
            const mockStrategyData = [
                {
                    name: '均线策略',
                    hk_profit: 12500,
                    us_profit: -3200,
                    total_trades: 45,
                    win_rate: 0.62,
                    sharpe_ratio: 1.35
                },
                {
                    name: 'RSI策略',
                    hk_profit: 8900,
                    us_profit: 15600,
                    total_trades: 32,
                    win_rate: 0.68,
                    sharpe_ratio: 1.52
                },
                {
                    name: '突破策略',
                    hk_profit: -2100,
                    us_profit: 9800,
                    total_trades: 28,
                    win_rate: 0.57,
                    sharpe_ratio: 0.89
                }
            ];

            const mockSymbolData = [
                { symbol: '00700.HK', profit: 5600, trades: 12, win_rate: 0.75, market: 'HK' },
                { symbol: 'AAPL', profit: 3200, trades: 8, win_rate: 0.62, market: 'US' },
                { symbol: '09988.HK', profit: -1200, trades: 6, win_rate: 0.33, market: 'HK' },
                { symbol: 'TSLA', profit: 8900, trades: 15, win_rate: 0.80, market: 'US' }
            ];

            setStrategyData(mockStrategyData);
            setSymbolData(mockSymbolData);
        } catch (error) {
            console.error('获取策略数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner />;

    const chartData = strategyData.map(strategy => ({
        name: strategy.name,
        港股收益: strategy.hk_profit,
        美股收益: strategy.us_profit,
        总收益: strategy.hk_profit + strategy.us_profit
    }));

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    策略分析
                </h1>
                <AnimatedButton onClick={fetchStrategyData} variant="secondary">
                    <RefreshCw className="w-4 h-4" />
                    刷新数据
                </AnimatedButton>
            </div>

            {/* 策略概览表格 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <BarChart3 className="w-6 h-6 mr-3 text-purple-600" />
                    策略表现总览
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">策略名称</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">港股收益</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">美股收益</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">总收益</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">交易次数</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">胜率</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">夏普比率</th>
                            </tr>
                        </thead>
                        <tbody>
                            {strategyData.map((strategy, index) => (
                                <tr key={index} className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 transition-all duration-200">
                                    <td className="py-4 px-6 font-semibold text-gray-900">{strategy.name}</td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={strategy.hk_profit} showSign />
                                    </td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={strategy.us_profit} showSign />
                                    </td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={strategy.hk_profit + strategy.us_profit} showSign className="text-lg font-bold" />
                                    </td>
                                    <td className="py-4 px-6 text-gray-700 font-medium">{strategy.total_trades}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={(strategy.win_rate * 100).toFixed(1)} type="winRate" />
                                    </td>
                                    <td className="py-4 px-6 font-semibold text-gray-900">{strategy.sharpe_ratio.toFixed(2)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>

            {/* 收益图表 */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <TrendingUp className="w-6 h-6 mr-3 text-red-600" />
                        策略收益对比
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis
                                dataKey="name"
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
                                formatter={(value, name) => [`¥${value.toLocaleString()}`, name]}
                                contentStyle={{
                                    background: 'rgba(255, 255, 255, 0.95)',
                                    backdropFilter: 'blur(10px)',
                                    border: 'none',
                                    borderRadius: '12px',
                                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)'
                                }}
                            />
                            <Bar dataKey="港股收益" fill="#9333ea" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="美股收益" fill="#ea580c" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </GlassCard>

                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <Target className="w-6 h-6 mr-3 text-blue-600" />
                        收益分布
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={[
                                    { name: '盈利策略', value: strategyData.filter(s => s.hk_profit + s.us_profit > 0).length, color: '#dc2626' },
                                    { name: '亏损策略', value: strategyData.filter(s => s.hk_profit + s.us_profit < 0).length, color: '#16a34a' }
                                ]}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                dataKey="value"
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                labelLine={false}
                            >
                                {[
                                    { name: '盈利策略', value: strategyData.filter(s => s.hk_profit + s.us_profit > 0).length, color: '#dc2626' },
                                    { name: '亏损策略', value: strategyData.filter(s => s.hk_profit + s.us_profit < 0).length, color: '#16a34a' }
                                ].map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(255, 255, 255, 0.95)',
                                    backdropFilter: 'blur(10px)',
                                    border: 'none',
                                    borderRadius: '12px',
                                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)'
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </GlassCard>
            </div>

            {/* 个股详情表格 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <Activity className="w-6 h-6 mr-3 text-orange-600" />
                    个股收益详情
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">股票代码</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">市场</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">收益</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">交易次数</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">胜率</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">表现</th>
                            </tr>
                        </thead>
                        <tbody>
                            {symbolData.map((symbol, index) => (
                                <tr key={index} className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-orange-50 hover:to-yellow-50 transition-all duration-200">
                                    <td className="py-4 px-6 font-mono font-semibold text-gray-900">{symbol.symbol}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={symbol.market} type="market" />
                                    </td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={symbol.profit} showSign className="text-lg" />
                                    </td>
                                    <td className="py-4 px-6 text-gray-700 font-medium">{symbol.trades}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={(symbol.win_rate * 100).toFixed(1)} type="winRate" />
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex items-center">
                                            {symbol.profit >= 0 ? (
                                                <div className="p-2 bg-red-100 rounded-xl">
                                                    <TrendingUp className="w-5 h-5 text-red-600" />
                                                </div>
                                            ) : (
                                                <div className="p-2 bg-green-100 rounded-xl">
                                                    <TrendingDown className="w-5 h-5 text-green-600" />
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>

            {/* 个股收益图表 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <BarChart3 className="w-6 h-6 mr-3 text-indigo-600" />
                    个股收益图表
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={symbolData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis
                            dataKey="symbol"
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
                            formatter={(value) => [`¥${value.toLocaleString()}`, '收益']}
                            contentStyle={{
                                background: 'rgba(255, 255, 255, 0.95)',
                                backdropFilter: 'blur(10px)',
                                border: 'none',
                                borderRadius: '12px',
                                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)'
                            }}
                        />
                        <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
                            {symbolData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.profit >= 0 ? '#dc2626' : '#16a34a'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </GlassCard>
        </div>
    );
};

export default StrategyPage;