import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  Play,
  Pause,
  Square,
  Plus,
  Eye,
  BarChart3,
  Wallet,
  Target,
  Settings,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Filter,
  Clock,
  User,
  Building,
  ArrowUpRight,
  ArrowDownRight,
  Check
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';

const API_BASE = 'http://localhost:8000';

// 市场颜色配置
const MARKET_COLORS = {
  HK: {
    primary: '#9333ea', // 紫色
    light: '#f3e8ff',
    text: 'text-purple-600',
    bg: 'bg-purple-100',
    gradient: 'from-purple-500 to-purple-600'
  },
  US: {
    primary: '#ea580c', // 橙色
    light: '#fff7ed', 
    text: 'text-orange-600',
    bg: 'bg-orange-100',
    gradient: 'from-orange-500 to-orange-600'
  }
};

// 自定义下拉选择器组件
const CustomSelect = ({ value, onChange, options, placeholder = "请选择", className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
      >
        <span className={selectedOption ? "text-gray-900" : "text-gray-500"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute z-10 w-full mt-2 bg-white/95 backdrop-blur-md border border-gray-200 rounded-xl shadow-lg overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className="w-full px-4 py-3 text-left hover:bg-blue-50/80 transition-colors duration-150 flex items-center justify-between focus:outline-none focus:bg-blue-50/80"
            >
              <span className="text-gray-900">{option.label}</span>
              {value === option.value && <Check className="w-4 h-4 text-blue-500" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// 自定义输入框组件
const CustomInput = ({ type = "text", placeholder, value, onChange, className = "" }) => {
  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={`w-full px-4 py-3 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-sm hover:shadow-md focus:shadow-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 placeholder-gray-400 ${className}`}
    />
  );
};

// 通用的毛玻璃卡片组件
const GlassCard = ({ children, className = "" }) => (
  <div className={`bg-white/80 backdrop-blur-xl rounded-2xl border border-white/30 shadow-lg hover:shadow-xl transition-all duration-300 ${className}`}>
    {children}
  </div>
);

// 动画按钮组件
const AnimatedButton = ({ children, onClick, variant = "primary", className = "", disabled = false, size = "md" }) => {
  const sizes = {
    sm: "px-3 py-2 text-sm",
    md: "px-4 py-3",
    lg: "px-6 py-4 text-lg"
  };

  const baseClass = `${sizes[size]} rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-2 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`;
  
  const variants = {
    primary: "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white focus:ring-blue-500/50",
    secondary: "bg-white/90 hover:bg-white text-gray-700 border border-gray-200 hover:border-gray-300 focus:ring-gray-500/50",
    success: "bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white focus:ring-green-500/50",
    warning: "bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white focus:ring-yellow-500/50",
    danger: "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white focus:ring-red-500/50",
    purple: "bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white focus:ring-purple-500/50",
    orange: "bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white focus:ring-orange-500/50"
  };
  
  return (
    <button 
      onClick={onClick}
      disabled={disabled}
      className={`${baseClass} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

// Loading组件
const LoadingSpinner = () => (
  <div className="flex justify-center items-center p-12">
    <div className="relative">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      <div className="animate-ping absolute top-2 left-2 rounded-full h-8 w-8 bg-blue-400 opacity-20"></div>
    </div>
  </div>
);

// 指标卡片组件
const MetricCard = ({ title, value, change, changeType, icon: Icon, color = "blue", trend }) => {
  const colors = {
    blue: "from-blue-500 to-blue-600",
    green: "from-green-500 to-green-600", 
    purple: "from-purple-500 to-purple-600",
    orange: "from-orange-500 to-orange-600",
    red: "from-red-500 to-red-600",
    yellow: "from-yellow-500 to-yellow-600"
  };

  return (
    <GlassCard className="p-6 hover:scale-105 transition-all duration-300 cursor-pointer">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mb-2">{value}</p>
          {change && (
            <div className={`flex items-center text-sm ${changeType === 'positive' ? 'text-green-600' : 'text-red-600'}`}>
              {trend === 'up' ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
              {change}
            </div>
          )}
        </div>
        <div className={`p-4 bg-gradient-to-br ${colors[color]} rounded-2xl shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </GlassCard>
  );
};

// 状态徽章组件
const StatusBadge = ({ status, variant = "default" }) => {
  const variants = {
    running: "bg-green-100/80 text-green-800 border border-green-200",
    paused: "bg-yellow-100/80 text-yellow-800 border border-yellow-200",
    stopped: "bg-red-100/80 text-red-800 border border-red-200", 
    created: "bg-blue-100/80 text-blue-800 border border-blue-200",
    default: "bg-gray-100/80 text-gray-800 border border-gray-200"
  };

  const labels = {
    running: "运行中",
    paused: "已暂停",
    stopped: "已停止",
    created: "已创建"
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${variants[status] || variants.default}`}>
      {labels[status] || status}
    </span>
  );
};

// 市场标签组件
const MarketBadge = ({ market }) => {
  const config = MARKET_COLORS[market];
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text} border border-current/20`}>
      {market === 'HK' ? '港股' : '美股'}
    </span>
  );
};

// 账户信息页面
const AccountPage = () => {
  const [accountData, setAccountData] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState('paper');

  const accountOptions = [
    { value: 'paper', label: '模拟账户' },
    { value: 'live', label: '实盘账户' }
  ];

  useEffect(() => {
    fetchAccountData();
  }, [selectedAccount]);

  const fetchAccountData = async () => {
    setLoading(true);
    try {
      const [balanceRes, positionsRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE}/api/account/${selectedAccount}/balance`),
        fetch(`${API_BASE}/api/account/${selectedAccount}/positions`),
        fetch(`${API_BASE}/api/account/${selectedAccount}/summary`)
      ]);

      const balance = await balanceRes.json();
      const positions = await positionsRes.json();
      const summary = await summaryRes.json();

      setAccountData({ balance, positions, summary });
    } catch (error) {
      console.error('获取账户数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  const portfolioData = [
    { name: '港股', value: 65000, color: MARKET_COLORS.HK.primary },
    { name: '美股', value: 85000, color: MARKET_COLORS.US.primary },
    { name: '现金', value: 50000, color: '#10b981' }
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          账户概览
        </h1>
        <div className="flex flex-col sm:flex-row gap-3">
          <CustomSelect
            value={selectedAccount}
            onChange={setSelectedAccount}
            options={accountOptions}
            className="w-full sm:w-48"
          />
          <AnimatedButton onClick={fetchAccountData} variant="secondary">
            <RefreshCw className="w-4 h-4" />
            刷新数据
          </AnimatedButton>
        </div>
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="总资产"
          value="¥200,000"
          change="+5.2%"
          changeType="positive"
          trend="up"
          icon={Wallet}
          color="blue"
        />
        <MetricCard
          title="可用现金"
          value="¥50,000"
          change="25%"
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="今日盈亏"
          value="+¥2,500"
          change="+1.25%"
          changeType="positive"
          trend="up"
          icon={TrendingUp}
          color="green"
        />
        <MetricCard
          title="持仓数量"
          value="12"
          change="只股票"
          icon={Target}
          color="purple"
        />
      </div>

      {/* 资产分布和市场分析 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <BarChart3 className="w-6 h-6 mr-3 text-blue-600" />
            资产分布
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={portfolioData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={40}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {portfolioData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`¥${value.toLocaleString()}`, '金额']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <Building className="w-6 h-6 mr-3 text-purple-600" />
            市场分析
          </h3>
          <div className="space-y-6">
            <div className="p-6 bg-gradient-to-r from-purple-50 to-purple-100 rounded-2xl border border-purple-200">
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <MarketBadge market="HK" />
                    <span className="font-semibold text-purple-800">港股持仓</span>
                  </div>
                  <p className="text-sm text-purple-600">6只 • ¥65,000</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">+2.8%</p>
                  <p className="text-sm text-gray-500">今日收益</p>
                </div>
              </div>
            </div>
            
            <div className="p-6 bg-gradient-to-r from-orange-50 to-orange-100 rounded-2xl border border-orange-200">
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <MarketBadge market="US" />
                    <span className="font-semibold text-orange-800">美股持仓</span>
                  </div>
                  <p className="text-sm text-orange-600">6只 • ¥85,000</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-red-600">-0.5%</p>
                  <p className="text-sm text-gray-500">今日收益</p>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* 持仓详情表格 */}
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <Target className="w-6 h-6 mr-3 text-indigo-600" />
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
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50/80 transition-colors duration-200">
                  <td className="py-4 px-6 font-medium text-gray-900">{stock.symbol}</td>
                  <td className="py-4 px-6 text-gray-800">{stock.name}</td>
                  <td className="py-4 px-6"><MarketBadge market={stock.market} /></td>
                  <td className="py-4 px-6 text-gray-800">{stock.quantity}</td>
                  <td className="py-4 px-6 text-gray-800">¥{stock.cost}</td>
                  <td className="py-4 px-6 text-gray-800">¥{stock.price}</td>
                  <td className={`py-4 px-6 font-bold ${stock.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {stock.pnl >= 0 ? '+' : ''}¥{stock.pnl}
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

  useEffect(() => {
    fetchTasks();
    fetchStrategies();
    const interval = setInterval(fetchLogs, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [selectedTaskId]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks`);
      const data = await response.json();
      setTasks(data || []);
    } catch (error) {
      console.error('获取任务失败:', error);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/strategies`);
      const data = await response.json();
      setStrategies(data || ['均线策略', 'RSI策略', '突破策略']);
    } catch (error) {
      console.error('获取策略失败:', error);
    }
  };

  const fetchLogs = async () => {
    if (!selectedTaskId) return;
    try {
      const response = await fetch(`${API_BASE}/api/tasks/${selectedTaskId}/logs`);
      const data = await response.json();
      setLogs(data || []);
    } catch (error) {
      console.error('获取日志失败:', error);
    }
  };

  const createTask = async () => {
    try {
      const symbols = newTask.symbols.split(',').map(s => s.trim()).filter(s => s);
      const response = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newTask, symbols })
      });
      
      if (response.ok) {
        setShowCreateForm(false);
        setNewTask({ account: 'paper', market: 'HK', symbols: '', strategy: '', trading_sessions: [] });
        fetchTasks();
      }
    } catch (error) {
      console.error('创建任务失败:', error);
    }
  };

  const handleTaskAction = async (taskId, action) => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks/${taskId}/${action}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: action === 'start' ? JSON.stringify({ task_id: taskId }) : undefined
      });
      
      if (response.ok) {
        fetchTasks();
      }
    } catch (error) {
      console.error(`${action}任务失败:`, error);
    }
  };

  const strategyOptions = strategies.map(s => ({ value: s, label: s }));

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent">
          任务管理
        </h1>
        <AnimatedButton onClick={() => setShowCreateForm(true)} size="lg">
          <Plus className="w-5 h-5" />
          新建任务
        </AnimatedButton>
      </div>

      {/* 创建任务表单 */}
      {showCreateForm && (
        <GlassCard className="p-8 border-l-4 border-l-blue-500">
          <h3 className="text-2xl font-semibold mb-6 text-gray-900">创建新任务</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                placeholder="多个代码用逗号分隔，如：00700.HK,AAPL"
                value={newTask.symbols}
                onChange={(e) => setNewTask({ ...newTask, symbols: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">策略</label>
              <CustomSelect
                value={newTask.strategy}
                onChange={(value) => setNewTask({ ...newTask, strategy: value })}
                options={strategyOptions}
                placeholder="选择交易策略"
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
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <Activity className="w-6 h-6 mr-3 text-green-600" />
          任务列表
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
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
                <tr key={task.id} className="border-b border-gray-100 hover:bg-blue-50/50 transition-all duration-200">
                  <td className="py-4 px-6 font-medium text-gray-900">#{task.id}</td>
                  <td className="py-4 px-6 text-gray-800">{task.strategy}</td>
                  <td className="py-4 px-6"><MarketBadge market={task.market} /></td>
                  <td className="py-4 px-6">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedTaskId(selectedTaskId === task.id ? null : task.id)}
                        className="p-2 hover:bg-blue-100 rounded-xl text-blue-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        title="查看日志"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleTaskAction(task.id, 'start')}
                        className="p-2 hover:bg-green-100 rounded-xl text-green-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="开始"
                        disabled={task.status === 'running'}
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleTaskAction(task.id, 'pause')}
                        className="p-2 hover:bg-yellow-100 rounded-xl text-yellow-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="暂停"
                        disabled={task.status !== 'running'}
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleTaskAction(task.id, 'stop')}
                        className="p-2 hover:bg-red-100 rounded-xl text-red-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
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
        <GlassCard className="p-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-semibold flex items-center">
              <Clock className="w-6 h-6 mr-3 text-blue-600" />
              任务 #{selectedTaskId} 日志
            </h3>
            <AnimatedButton onClick={fetchLogs} variant="secondary" size="sm">
              <RefreshCw className="w-4 h-4" />
              刷新日志
            </AnimatedButton>
          </div>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 h-96 overflow-y-auto text-sm font-mono shadow-inner">
            {logs.length === 0 ? (
              <div className="text-gray-400 text-center py-12 text-base">暂无日志数据</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="text-green-300 mb-2 hover:bg-gray-700/30 px-2 py-1 rounded transition-colors">
                  <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
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
        { symbol: 'TSLA', profit: 8900, trades: 15, win_rate: 0.80, market: 'US' },
        { symbol: '01810.HK', profit: 2800, trades: 9, win_rate: 0.67, market: 'HK' },
        { symbol: 'MSFT', profit: -800, trades: 5, win_rate: 0.40, market: 'US' }
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
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 bg-clip-text text-transparent">
          策略分析
        </h1>
        <AnimatedButton onClick={fetchStrategyData} variant="secondary">
          <RefreshCw className="w-4 h-4" />
          刷新数据
        </AnimatedButton>
      </div>

      {/* 策略概览表格 */}
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <BarChart3 className="w-6 h-6 mr-3 text-purple-600" />
          策略表现总览
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
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
                <tr key={index} className="border-b border-gray-100 hover:bg-purple-50/50 transition-all duration-200">
                  <td className="py-4 px-6 font-semibold text-gray-900">{strategy.name}</td>
                  <td className={`py-4 px-6 font-bold ${strategy.hk_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {strategy.hk_profit >= 0 ? '+' : ''}¥{strategy.hk_profit.toLocaleString()}
                  </td>
                  <td className={`py-4 px-6 font-bold ${strategy.us_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {strategy.us_profit >= 0 ? '+' : ''}¥{strategy.us_profit.toLocaleString()}
                  </td>
                  <td className={`py-4 px-6 font-bold text-lg ${(strategy.hk_profit + strategy.us_profit) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {(strategy.hk_profit + strategy.us_profit) >= 0 ? '+' : ''}¥{(strategy.hk_profit + strategy.us_profit).toLocaleString()}
                  </td>
                  <td className="py-4 px-6 text-gray-800">{strategy.total_trades}</td>
                  <td className="py-4 px-6">
                    <span className={`px-3 py-2 rounded-xl text-sm font-semibold ${
                      strategy.win_rate >= 0.6 ? 'bg-green-100 text-green-800 border border-green-200' : 
                      strategy.win_rate >= 0.4 ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' : 'bg-red-100 text-red-800 border border-red-200'
                    }`}>
                      {(strategy.win_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-4 px-6 font-semibold text-gray-800">{strategy.sharpe_ratio.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* 收益图表 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <TrendingUp className="w-6 h-6 mr-3 text-green-600" />
            策略收益对比
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
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
                  formatter={(value) => [`¥${value.toLocaleString()}`, '收益']} 
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar dataKey="港股收益" fill={MARKET_COLORS.HK.primary} radius={[4, 4, 0, 0]} />
                <Bar dataKey="美股收益" fill={MARKET_COLORS.US.primary} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <Target className="w-6 h-6 mr-3 text-blue-600" />
            收益分布
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    { name: '盈利策略', value: strategyData.filter(s => s.hk_profit + s.us_profit > 0).length, color: '#10b981' },
                    { name: '亏损策略', value: strategyData.filter(s => s.hk_profit + s.us_profit < 0).length, color: '#ef4444' }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={40}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {[
                    { name: '盈利策略', value: strategyData.filter(s => s.hk_profit + s.us_profit > 0).length, color: '#10b981' },
                    { name: '亏损策略', value: strategyData.filter(s => s.hk_profit + s.us_profit < 0).length, color: '#ef4444' }
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* 个股详情表格 */}
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <Activity className="w-6 h-6 mr-3 text-orange-600" />
          个股收益详情
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
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
                <tr key={index} className="border-b border-gray-100 hover:bg-orange-50/50 transition-all duration-200">
                  <td className="py-4 px-6 font-semibold text-gray-900">{symbol.symbol}</td>
                  <td className="py-4 px-6"><MarketBadge market={symbol.market} /></td>
                  <td className={`py-4 px-6 font-bold text-lg ${symbol.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {symbol.profit >= 0 ? '+' : ''}¥{symbol.profit.toLocaleString()}
                  </td>
                  <td className="py-4 px-6 text-gray-800">{symbol.trades}</td>
                  <td className="py-4 px-6 text-gray-800 font-medium">{(symbol.win_rate * 100).toFixed(1)}%</td>
                  <td className="py-4 px-6">
                    <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-xl ${
                      symbol.profit >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {symbol.profit >= 0 ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      <span className="text-sm font-medium">
                        {symbol.profit >= 0 ? '盈利' : '亏损'}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* 个股收益图表 */}
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <BarChart3 className="w-6 h-6 mr-3 text-indigo-600" />
          个股收益图表
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
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
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: 'none',
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Bar dataKey="profit" radius={[4, 4, 0, 0]}>
                {symbolData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.profit >= 0 ? '#10b981' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </div>
  );
};

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

  const performanceData = [
    { time: '10:00', cpu: 35, memory: 45 },
    { time: '11:00', cpu: 42, memory: 52 },
    { time: '12:00', cpu: 38, memory: 48 },
    { time: '13:00', cpu: 45, memory: 68 },
    { time: '14:00', cpu: 41, memory: 65 },
    { time: '15:00', cpu: 39, memory: 58 },
    { time: '16:00', cpu: 47, memory: 62 }
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
          系统状态
        </h1>
        <AnimatedButton onClick={fetchSystemStatus} variant="secondary">
          <RefreshCw className="w-4 h-4" />
          刷新状态
        </AnimatedButton>
      </div>

      {/* 系统概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="系统运行时间"
          value={mockSystemData.uptime}
          icon={Clock}
          color="blue"
        />
        <MetricCard
          title="CPU使用率"
          value={`${mockSystemData.cpu_usage}%`}
          change="正常范围"
          icon={Activity}
          color="green"
        />
        <MetricCard
          title="内存使用率"
          value={`${mockSystemData.memory_usage}%`}
          change="较高使用"
          icon={Settings}
          color="yellow"
        />
        <MetricCard
          title="活跃任务"
          value={mockSystemData.active_tasks.toString()}
          change="个任务运行中"
          icon={Target}
          color="purple"
        />
      </div>

      {/* API健康状态 */}
      <GlassCard className="p-8">
        <h3 className="text-2xl font-semibold mb-6 flex items-center">
          <Activity className="w-6 h-6 mr-3 text-green-600" />
          API服务状态
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-200">
            <div>
              <p className="font-semibold text-green-800 text-lg">交易服务</p>
              <p className="text-sm text-green-600 mt-1">正常运行</p>
            </div>
            <div className="relative">
              <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              <div className="absolute inset-0 w-4 h-4 bg-green-500 rounded-full animate-ping opacity-20"></div>
            </div>
          </div>
          <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-200">
            <div>
              <p className="font-semibold text-green-800 text-lg">数据服务</p>
              <p className="text-sm text-green-600 mt-1">正常运行</p>
            </div>
            <div className="relative">
              <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              <div className="absolute inset-0 w-4 h-4 bg-green-500 rounded-full animate-ping opacity-20"></div>
            </div>
          </div>
          <div className="flex items-center justify-between p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-200">
            <div>
              <p className="font-semibold text-green-800 text-lg">风控服务</p>
              <p className="text-sm text-green-600 mt-1">正常运行</p>
            </div>
            <div className="relative">
              <div className="w-4 h-4 bg-green-500 rounded-full"></div>
              <div className="absolute inset-0 w-4 h-4 bg-green-500 rounded-full animate-ping opacity-20"></div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* 系统性能图表和今日统计 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <BarChart3 className="w-6 h-6 mr-3 text-blue-600" />
            系统负载监控
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
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
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="cpu" 
                  stroke="#3b82f6" 
                  strokeWidth={3} 
                  name="CPU使用率"
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#3b82f6' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="memory" 
                  stroke="#10b981" 
                  strokeWidth={3} 
                  name="内存使用率"
                  dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#10b981' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard className="p-8">
          <h3 className="text-2xl font-semibold mb-6 flex items-center">
            <TrendingUp className="w-6 h-6 mr-3 text-green-600" />
            今日交易统计
          </h3>
          <div className="space-y-6">
            <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-200">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-blue-600 mb-1">总交易次数</p>
                  <p className="text-3xl font-bold text-blue-800">{mockSystemData.total_trades_today}</p>
                </div>
                <div className="p-3 bg-blue-500 rounded-2xl">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
              </div>
            </div>
            <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-200">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-green-600 mb-1">成功交易</p>
                  <p className="text-3xl font-bold text-green-800">98</p>
                </div>
                <div className="text-right">
                  <div className="text-green-600 text-lg font-semibold">77.2%</div>
                  <div className="text-sm text-green-500">成功率</div>
                </div>
              </div>
            </div>
            <div className="p-6 bg-gradient-to-r from-red-50 to-rose-50 rounded-2xl border border-red-200">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-medium text-red-600 mb-1">失败交易</p>
                  <p className="text-3xl font-bold text-red-800">29</p>
                </div>
                <div className="text-right">
                  <div className="text-red-600 text-lg font-semibold">22.8%</div>
                  <div className="text-sm text-red-500">失败率</div>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

// 主应用组件
const App = () => {
  const [currentPage, setCurrentPage] = useState('account');

  const pages = [
    { id: 'account', name: '账户信息', icon: User, component: AccountPage },
    { id: 'tasks', name: '任务管理', icon: Activity, component: TaskPage },
    { id: 'strategy', name: '策略分析', icon: BarChart3, component: StrategyPage },
    { id: 'status', name: '系统状态', icon: Settings, component: StatusPage }
  ];

  const CurrentPageComponent = pages.find(p => p.id === currentPage)?.component || AccountPage;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/80 via-white to-purple-50/80">
      {/* 顶部导航栏 */}
      <nav className="bg-white/90 backdrop-blur-xl border-b border-white/30 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-18">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                  LongPort 量化交易系统
                </h1>
              </div>
            </div>
            <div className="flex space-x-2">
              {pages.map(page => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.id}
                    onClick={() => setCurrentPage(page.id)}
                    className={`px-5 py-3 rounded-xl font-semibold transition-all duration-200 flex items-center gap-2 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      currentPage === page.id
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg focus:ring-blue-500/50'
                        : 'text-gray-600 hover:bg-gray-100/80 hover:text-gray-800 focus:ring-gray-500/50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="hidden sm:inline">{page.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          <CurrentPageComponent />
        </div>
      </main>

      {/* 页脚 */}
      <footer className="bg-white/80 backdrop-blur-xl border-t border-white/30 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-500">
              © 2025 LongPort 量化交易系统. 专业的量化投资解决方案.
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                系统正常运行
              </span>
              <span>版本 v1.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;