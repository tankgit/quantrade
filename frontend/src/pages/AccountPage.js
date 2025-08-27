import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, BarChart3, Wallet, Target, RefreshCw, Building, ArrowUpRight } from 'lucide-react';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { CustomSelect, AnimatedButton, GlassCard, LoadingSpinner, ValueDisplay, StatusBadge } from '../components/basic';
import { api } from '../BackendAPI';

// 账户信息页面
const AccountPage = () => {
    const [accountData, setAccountData] = useState({});
    const [loading, setLoading] = useState(true);
    const [selectedAccount, setSelectedAccount] = useState('paper');
    const [selectedCurrency, setSelectedCurrency] = useState('USD');

    const accountOptions = [
        { value: 'paper', label: '模拟账户' },
        { value: 'live', label: '实盘账户' }
    ];

    const currencyOptions = [
        { value: 'USD', label: 'USD' },
        { value: 'HKD', label: 'HKD' },
    ];

    const currencySymbols = {
        'USD': '$',
        'HKD': 'HK$',
    };

    // useEffect(() => {
    //     fetchAccountData();
    // }, [selectedAccount, selectedCurrency]);

    useEffect(() => {
        fetchAccountData();
    }, []);

    const fetchAccountData = async () => {
        setLoading(true);
        try {
            const [balanceResp, positionsResp, summaryResp] = await Promise.all([
                api.getAccountBalance(selectedAccount, selectedCurrency),
                api.getAccountPostions(selectedAccount),
                api.getAccountSummary(selectedAccount)
            ]);
            const balance = balanceResp.balances[0] || {};
            const positions = positionsResp.positions.channels[0].positions || {};
            const summary = summaryResp || {};

            setAccountData({ balance, positions, summary });
        } catch (error) {
            console.error('获取账户数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner />;

    const asset_ratio = [
        { name: '港股', value: accountData.summary.asset_ratio.HK, color: '#9333ea' },
        { name: '美股', value: accountData.summary.asset_ratio.US, color: '#ea580c' },
        { name: '现金', value: accountData.summary.asset_ratio.cash, color: '#3b82f6' }
    ];

    console.log(accountData.positions)

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-500 to-gray-600 bg-clip-text text-transparent">
                    账户概览
                </h1>
                <div className="flex gap-4">
                    <CustomSelect
                        value={selectedAccount}
                        onChange={setSelectedAccount}
                        options={accountOptions}
                        className="w-40"
                    />
                    <CustomSelect
                        value={selectedCurrency}
                        onChange={setSelectedCurrency}
                        options={currencyOptions}
                        className="w-40"
                    />
                    <AnimatedButton onClick={fetchAccountData} variant="secondary">
                        <RefreshCw className="w-4 h-4" />
                        刷新
                    </AnimatedButton>
                </div>
            </div>

            {/* 核心指标卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">总资产({selectedCurrency})</p>
                            <p className="text-3xl font-bold text-blue-600 mb-2">{currencySymbols[selectedCurrency]}{accountData.summary.balances[selectedCurrency].net_assets}</p>
                            {/* <div className="flex items-center text-sm">
                                <ArrowUpRight className="w-3 h-3 mr-1 text-red-500" />
                                <span className="text-red-500 font-medium">+5.2%</span>
                            </div> */}
                        </div>
                        <div className="p-4 bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl shadow-lg">
                            <Wallet className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-emerald-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">可用现金({selectedCurrency})</p>
                            <p className="text-3xl font-bold text-emerald-600 mb-2">{currencySymbols[selectedCurrency]}{accountData.balance.total_cash}</p>
                            <div className="flex items-center text-sm">
                                <span className="text-gray-500">{(accountData.summary.stock_ratio * 100).toFixed(1)}% 仓位</span>
                            </div>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-2xl shadow-lg">
                            <DollarSign className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>

                {/* <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-red-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">今日盈亏</p>
                            <p className="text-3xl font-bold text-red-600 mb-2">+¥2,500</p>
                            <div className="flex items-center text-sm">
                                <TrendingUp className="w-3 h-3 mr-1 text-red-500" />
                                <span className="text-red-500 font-medium">+1.25%</span>
                            </div>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-red-500 to-red-600 rounded-2xl shadow-lg">
                            <TrendingUp className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard> */}

                <GlassCard className="hover:scale-105 transition-transform duration-300 border-l-4 border-l-purple-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 mb-1">持仓数量</p>
                            <p className="text-3xl font-bold text-purple-600 mb-2">{accountData.positions.length}</p>
                            <div className="flex items-center text-sm">
                                <span className="text-gray-500">只股票</span>
                            </div>
                        </div>
                        <div className="p-4 bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl shadow-lg">
                            <Target className="w-8 h-8 text-white" />
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* 资产分布和市场分析 */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <BarChart3 className="w-6 h-6 mr-3 text-blue-600" />
                        资产分布
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie
                                data={asset_ratio}
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                labelLine={false}
                            >
                                {asset_ratio.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                formatter={(value) => [`¥${value.toLocaleString()}`, '金额']}
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

                <GlassCard>
                    <h3 className="text-2xl font-semibold mb-6 flex items-center">
                        <Building className="w-6 h-6 mr-3 text-purple-600" />
                        市场分析
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-2xl border border-purple-200">
                            <div>
                                <p className="font-semibold text-purple-900">港股持仓</p>
                                <p className="text-sm text-purple-700 mt-1">{accountData.summary.positions.HK.length}只 • {currencySymbols[selectedCurrency]}{accountData.summary.assets.HK.stock}</p>
                            </div>
                            <div className="text-right">
                                <ValueDisplay value={1820} showSign className="text-lg" />
                                <p className="text-sm text-red-500 mt-1">null% 今日</p>
                            </div>
                        </div>
                        <div className="flex justify-between items-center p-4 bg-gradient-to-r from-orange-50 to-orange-100 rounded-2xl border border-orange-200">
                            <div>
                                <p className="font-semibold text-orange-900">美股持仓</p>
                                <p className="text-sm text-orange-700 mt-1">{accountData.summary.positions.US.length}只 • {currencySymbols[selectedCurrency]}{accountData.summary.assets.US.stock}</p>
                            </div>
                            <div className="text-right">
                                <ValueDisplay value={-425} showSign className="text-lg" />
                                <p className="text-sm text-green-500 mt-1">null% 今日</p>
                            </div>
                        </div>
                    </div>
                </GlassCard>
            </div>

            {/* 持仓详情表格 */}
            <GlassCard>
                <h3 className="text-2xl font-semibold mb-6 flex items-center">
                    <Target className="w-6 h-6 mr-3 text-purple-600" />
                    持仓明细
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">股票代码</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">名称</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">市场</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">持仓</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">成本价</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">现价</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">盈亏</th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                { symbol: '00700.HK', name: '腾讯控股', market: 'HK', quantity: 100, cost: 425.5, price: 432.8, pnl: 730 },
                                { symbol: '09988.HK', name: '阿里巴巴', market: 'HK', quantity: 200, cost: 102.3, price: 98.7, pnl: -720 },
                                { symbol: 'AAPL', name: '苹果', market: 'US', quantity: 50, cost: 180.2, price: 185.4, pnl: 260 },
                                { symbol: 'TSLA', name: '特斯拉', market: 'US', quantity: 30, cost: 245.8, price: 238.2, pnl: -228 }
                            ].map((stock, index) => (
                                <tr key={index} className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                                    <td className="py-4 px-6 font-mono font-medium text-gray-900">{stock.symbol}</td>
                                    <td className="py-4 px-6 font-medium text-gray-900">{stock.name}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={stock.market} type="market" />
                                    </td>
                                    <td className="py-4 px-6 text-gray-700">{stock.quantity}</td>
                                    <td className="py-4 px-6 text-gray-700">¥{stock.cost}</td>
                                    <td className="py-4 px-6 text-gray-700">¥{stock.price}</td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={stock.pnl} showSign />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassCard>
        </div>
    );
};

export default AccountPage;