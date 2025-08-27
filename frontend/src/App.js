import './styles/App.css';
import React, { useState } from 'react';
import { Activity, BarChart3, Settings, User } from 'lucide-react';
import AccountPage from './pages/AccountPage';
import TaskPage from './pages/TaskPage';
import StrategyPage from './pages/StrategyPage';
import StatusPage from './pages/StatusPage';


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
    <div className="min-h-screen bg-gradient-to-br from-blue-100 via-white to-purple-100">
      {/* 顶部导航栏 */}
      <nav className="bg-white/90 backdrop-blur-md border-b border-white/30 sticky top-0 z-50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-500 to-gray-600 bg-clip-text text-transparent">
                  PawQuote Trade
                </h1>
              </div>
            </div>
            <div className="flex space-x-4">
              {pages.map(page => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.id}
                    onClick={() => setCurrentPage(page.id)}
                    className={`px-6 py-3 rounded-2xl font-semibold transition-all duration-300 flex items-center gap-3 transform hover:scale-105 focus:outline-none shadow-lg ${currentPage === page.id
                      ? 'bg-gradient-to-r from-gray-500 to-gray-600 text-white shadow-xl focus:ring-blue-500'
                      : 'text-gray-600 hover:bg-white/80 backdrop-blur-sm border border-white/30 hover:text-gray-900 focus:ring-gray-500'
                      }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="hidden sm:block">{page.name}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-in slide-in-from-bottom-5 duration-500">
          <CurrentPageComponent />
        </div>
      </main>

      {/* 页脚 */}
      <footer className="bg-white/80 backdrop-blur-md border-t border-white/30 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">
              © 2025 PawQuote Trade
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;