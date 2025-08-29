import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, BarChart3, Wallet, Target, RefreshCw, Building, ArrowUpRight } from 'lucide-react';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell, ZAxis } from 'recharts';
import { CustomSelect, AnimatedButton, GlassCard, LoadingSpinner, ValueDisplay, StatusBadge } from '../components/basic';
import { api } from '../BackendAPI';

// 账户信息页面
const AccountPage = () => {
    const [summary, setSummary] = useState({});
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedAccount, setSelectedAccount] = useState('paper');
    const [selectedCurrency, setSelectedCurrency] = useState('USD');
    const [tradeSession, setTradeSession] = useState('regular');
    const [marketPnl, setmarketPnl] = useState({ US: 0, HK: 0 });

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
        'US': '$',
        'HK': 'HK$',
    };

    const stockNameMap = {
        'SMIC': '中芯国际',
    }

    const sessionMap = {
        regular: '盘中',
        pre_market: '盘前',
        post_market: '盘后',
        overnight: '夜盘'
    }

    // 根据当前时间，设置当前交易session
    const refreshTradeSession = () => {
        // 这里获取美国东部时间ET，要显式地获取
        const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/New_York" }));


        const hours = now.getHours();
        const minutes = now.getMinutes();
        const timeInMinutes = hours * 60 + minutes;

        // 美股交易时间 (ET): 9:30 - 16:00, 16:00 - 20:00 (盘后), 20:00 - 04:00 (夜盘), 04:00 - 9:30 (盘前)
        if (timeInMinutes >= 570 && timeInMinutes < 960) {
            setTradeSession('regular'); // 正常交易时间
            return 'current'
        } else if (timeInMinutes >= 960 && timeInMinutes < 1200) {
            setTradeSession('post_market'); // 盘后
            return 'post_market'
        } else if (timeInMinutes >= 1200 || timeInMinutes < 240) {
            setTradeSession('post_market'); // 夜盘, 但是没有开通夜盘api时，获取不到这个信息，用盘后充数
            return 'post_market'
        } else {
            setTradeSession('pre_market'); // 盘前
            return 'pre_market'
        }

    };

    useEffect(() => {
        fetchAccountData();
    }, [selectedAccount]);

    // 调用api.getQuotePrice刷新position里面的last done价格
    const refreshQuote = async (pos = null) => {
        pos = pos || positions
        if (pos.length === 0) return;
        const ts = refreshTradeSession()
        const mpnl = { US: 0, HK: 0 };
        const symbols = pos.map(p => p.symbol);
        try {
            const priceMap = await api.getQuotePrice(selectedAccount, symbols);
            const updatedPositions = pos.map(p => {
                const price = priceMap[p.symbol][ts + "_price"] || priceMap[p.symbol]["regular_price"];
                const pnl = (price - p.cost_price) * p.quantity
                mpnl[p.market] += pnl;
                return {
                    ...p,
                    cost_price: p.cost_price,
                    price: price,
                    pnl: pnl,
                }
            });
            setmarketPnl(mpnl);
            console.log(updatedPositions)
            setPositions(updatedPositions);
        } catch (error) {
            console.error('获取最新价格失败:', error);
        }
    }

    // 每隔一段时间 自动调用refreshquote刷新行情
    useEffect(() => {
        // refreshQuote();
        const interval = setInterval(() => {
            refreshQuote();
        }, 5000); // 每60秒刷新一次
        return () => clearInterval(interval);
    }, [positions]);

    const fetchAccountData = async () => {
        setLoading(true);
        setmarketPnl({ US: 0, HK: 0 });
        setPositions([]);
        try {
            const [positionsResp, summaryResp] = await Promise.all([
                api.getAccountPostions(selectedAccount),
                api.getAccountSummary(selectedAccount)
            ]);
            const summary = summaryResp || {};
            setSummary(summary);

            const pos = positionsResp.positions.channels[0].positions || {};
            const positions = pos.map(p => {
                return {
                    ...p,
                    market: p.symbol.includes('.') ? p.symbol.split('.')[1] : 'US'

                }
            })
            setPositions(positions);
            refreshQuote(positions)
        } catch (error) {
            console.error('获取账户数据失败:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner />;

    const asset_ratio = [
        { name: '港股', value: summary.asset_ratio?.HK || 0, color: '#9333ea' },
        { name: '美股', value: summary.asset_ratio?.US || 0, color: '#ea580c' },
        { name: '现金', value: summary.asset_ratio?.cash || 0, color: '#2ea46bff' }
    ];


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
                            <p className="text-3xl font-bold text-blue-600 mb-2">{currencySymbols[selectedCurrency]}{summary.balances ? summary.balances[selectedCurrency]?.net_assets : "-"}</p>
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
                            <p className="text-3xl font-bold text-emerald-600 mb-2">{currencySymbols[selectedCurrency]}{summary.balances ? summary.balances[selectedCurrency]?.total_cash : "-"}</p>
                            <div className="flex items-center text-sm">
                                <span className="text-gray-500">{(summary.stock_ratio * 100).toFixed(1)}% 仓位</span>
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
                            <p className="text-3xl font-bold text-purple-600 mb-2">{summary.total_positions}</p>
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
                                <p className="text-sm text-purple-700 mt-1">{summary.positions?.HK.length}只 • {currencySymbols.HK}{summary.assets?.HK.stock}</p>
                            </div>
                            <div className="text-right">
                                <ValueDisplay value={marketPnl.HK} prefix={currencySymbols.HK} showSign className="text-lg" />
                                {/* <p className="text-sm text-gray-500 mt-1">null% 今日</p> */}
                            </div>
                        </div>
                        <div className="flex justify-between items-center p-4 bg-gradient-to-r from-orange-50 to-orange-100 rounded-2xl border border-orange-200">
                            <div>
                                <p className="font-semibold text-orange-900">美股持仓</p>
                                <p className="text-sm text-orange-700 mt-1">{summary.positions?.US.length}只 • {currencySymbols.US}{summary.assets?.US.stock}</p>
                            </div>
                            <div className="text-right">
                                <ValueDisplay value={marketPnl.US} prefix={currencySymbols.US} showSign className="text-lg" />
                                {/* <p className="text-sm text-gray-500 mt-1">null% 今日</p> */}
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
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">可用持仓</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">成本价</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">现价</th>
                                <th className="text-left py-4 px-6 font-semibold text-gray-700">盈亏</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.map((stock, index) => (
                                <tr key={index} className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                                    <td className="py-4 px-6 font-mono font-medium text-gray-900">{stock.symbol}</td>
                                    <td className="py-4 px-6 font-medium text-gray-900">{stockNameMap[stock.symbol_name] || stock.symbol_name}</td>
                                    <td className="py-4 px-6">
                                        <StatusBadge status={stock.market} type="market" />
                                    </td>
                                    <td className="py-4 px-6 text-gray-700">{stock.quantity}</td>
                                    <td className="py-4 px-6 text-gray-700">{stock.available_quantity}</td>
                                    <td className="py-4 px-6 text-gray-700">{currencySymbols[stock.market]}{stock.cost_price}</td>
                                    <td className="py-4 px-6 text-gray-700">{currencySymbols[stock.market]}{stock.price}{stock.market === "US" && <span className='text-sm px-1 py-[2px] ml-1 bg-blue-200 text-blue-600 rounded-md'>{sessionMap[tradeSession]}</span>}</td>
                                    <td className="py-4 px-6">
                                        <ValueDisplay value={stock.pnl} prefix={currencySymbols[stock.market]} showSign />
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