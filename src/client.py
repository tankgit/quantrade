"""
命令行模块 - 提供简易的命令行工具
"""
import asyncio
import argparse
import sys
import json
from typing import List, Optional
import logging

from .config import TradingConfig, ConfigManager
from .strategy import SimpleMAStrategy, StrategyManager
from .trade import TradeEngine
from .account import AccountManager
from .task import TaskManager, TaskConfig


class QuantCLI:
    """量化交易命令行工具"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.task_manager: Optional[TaskManager] = None
        self.account_manager: Optional[AccountManager] = None
        self.trade_engine: Optional[TradeEngine] = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("quant_cli")
    
    async def initialize(self) -> bool:
        """初始化CLI"""
        try:
            # 加载配置
            config = self.config_manager.load_config()
            
            # 初始化各个管理器
            self.task_manager = TaskManager(config)
            self.account_manager = AccountManager(config)
            self.trade_engine = TradeEngine(config)
            
            # 初始化组件
            if not await self.task_manager.initialize():
                self.logger.error("任务管理器初始化失败")
                return False
            
            self.logger.info("CLI初始化成功")
            return True
        
        except Exception as e:
            self.logger.error(f"CLI初始化失败: {e}")
            return False
    
    async def cmd_account_balance(self, args) -> None:
        """查询账户余额"""
        if not self.account_manager:
            print("账户管理器未初始化")
            return
        
        balance = await self.account_manager.get_account_balance(force_refresh=args.refresh)
        if balance:
            print("\n=== 账户余额 ===")
            print(f"总现金: {balance['total_cash']:,.2f} {balance['currency']}")
            print(f"可用现金: {balance['available_cash']:,.2f} {balance['currency']}")
            print(f"冻结资金: {balance['frozen_cash']:,.2f} {balance['currency']}")
            print(f"总购买力: {balance['total_power']:,.2f} {balance['currency']}")
            print(f"净资产: {balance['net_assets']:,.2f} {balance['currency']}")
        else:
            print("无法获取账户余额")
    
    async def cmd_account_positions(self, args) -> None:
        """查询持仓信息"""
        if not self.account_manager:
            print("账户管理器未初始化")
            return
        
        positions = await self.account_manager.get_positions(force_refresh=args.refresh)
        if positions:
            print(f"\n=== 持仓信息 ({len(positions)}个) ===")
            print(f"{'股票代码':<12} {'股票名称':<12} {'持仓':<8} {'成本价':<10} {'市价':<10} {'市值':<12} {'盈亏':<12} {'盈亏%':<8}")
            print("-" * 100)
            
            for pos in positions:
                pnl_color = "+" if pos['unrealized_pnl'] >= 0 else ""
                print(f"{pos['symbol']:<12} {pos['symbol_name']:<12} {pos['quantity']:<8} "
                      f"{pos['cost_price']:<10.2f} {pos['market_price']:<10.2f} "
                      f"{pos['market_value']:<12.2f} {pnl_color}{pos['unrealized_pnl']:<12.2f} "
                      f"{pnl_color}{pos['unrealized_pnl_percent']:<8.2f}%")
        else:
            print("暂无持仓")
    
    async def cmd_account_orders(self, args) -> None:
        """查询历史订单"""
        if not self.account_manager:
            print("账户管理器未初始化")
            return
        
        if args.today:
            orders = await self.account_manager.get_today_orders()
            print("\n=== 今日订单 ===")
        else:
            orders = await self.account_manager.get_history_orders()
            print("\n=== 历史订单 (近30天) ===")
        
        if orders:
            print(f"{'订单号':<12} {'股票代码':<12} {'方向':<6} {'数量':<8} {'价格':<10} {'状态':<10} {'提交时间':<20}")
            print("-" * 100)
            
            for order in orders:
                submit_time = order['submitted_at'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{order['order_id']:<12} {order['symbol']:<12} {order['side']:<6} "
                      f"{order['quantity']:<8} {order['price']:<10.2f} {order['status']:<10} {submit_time:<20}")
        else:
            print("暂无订单记录")
    
    async def cmd_portfolio_summary(self, args) -> None:
        """查询投资组合摘要"""
        if not self.account_manager:
            print("账户管理器未初始化")
            return
        
        summary = await self.account_manager.get_portfolio_summary()
        if summary:
            print("\n=== 投资组合摘要 ===")
            print(f"持仓数量: {summary['total_positions']}")
            print(f"总市值: {summary['total_market_value']:,.2f}")
            print(f"总成本: {summary['total_cost']:,.2f}")
            print(f"总盈亏: {summary['total_unrealized_pnl']:,.2f} ({summary['total_unrealized_pnl_percent']:.2f}%)")
            print(f"现金比例: {summary['cash_ratio']:.2%}")
            print(f"股票比例: {summary['stock_ratio']:.2%}")
        else:
            print("无法获取投资组合摘要")
    
    async def cmd_strategy_list(self, args) -> None:
        """列出所有策略"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        strategies = self.task_manager.strategy_manager.get_strategies_info()
        if strategies:
            print(f"\n=== 策略列表 ({len(strategies)}个) ===")
            print(f"{'策略名称':<15} {'状态':<8} {'总信号':<8} {'买入信号':<8} {'卖出信号':<8}")
            print("-" * 60)
            
            for name, info in strategies.items():
                status = "运行中" if info['is_active'] else "已停止"
                print(f"{name:<15} {status:<8} {info['total_signals']:<8} "
                      f"{info['buy_signals']:<8} {info['sell_signals']:<8}")
        else:
            print("暂无策略")
    
    async def cmd_strategy_create(self, args) -> None:
        """创建策略"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        try:
            # 创建简单移动平均策略
            strategy = SimpleMAStrategy(
                short_period=args.short_period,
                long_period=args.long_period,
                symbols=args.symbols.split(',') if args.symbols else []
            )
            
            # 创建任务配置
            task_config = TaskConfig(
                interval=args.interval,
                max_runs=args.max_runs,
                auto_restart=args.auto_restart
            )
            
            # 创建策略任务
            task_id = self.task_manager.create_strategy_task(
                name=args.name,
                strategy=strategy,
                symbols=args.symbols.split(',') if args.symbols else [],
                config=task_config
            )
            
            print(f"策略任务创建成功，任务ID: {task_id}")
        
        except Exception as e:
            print(f"策略创建失败: {e}")
    
    async def cmd_task_list(self, args) -> None:
        """列出所有任务"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        tasks = self.task_manager.get_all_tasks()
        if tasks:
            print(f"\n=== 任务列表 ({len(tasks)}个) ===")
            print(f"{'任务ID':<12} {'任务名称':<15} {'类型':<10} {'状态':<8} {'运行次数':<8} {'错误次数':<8}")
            print("-" * 80)
            
            for task_id, task in tasks.items():
                print(f"{task_id:<12} {task.name:<15} {task.task_type.value:<10} "
                      f"{task.status.value:<8} {task.run_count:<8} {task.error_count:<8}")
        else:
            print("暂无任务")
    
    async def cmd_task_start(self, args) -> None:
        """启动任务"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        success = self.task_manager.start_task(args.task_id)
        if success:
            print(f"任务 {args.task_id} 启动成功")
        else:
            print(f"任务 {args.task_id} 启动失败")
    
    async def cmd_task_stop(self, args) -> None:
        """停止任务"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        success = self.task_manager.stop_task(args.task_id)
        if success:
            print(f"任务 {args.task_id} 停止成功")
        else:
            print(f"任务 {args.task_id} 停止失败")
    
    async def cmd_task_delete(self, args) -> None:
        """删除任务"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        success = self.task_manager.delete_task(args.task_id)
        if success:
            print(f"任务 {args.task_id} 删除成功")
        else:
            print(f"任务 {args.task_id} 删除失败")
    
    async def cmd_task_info(self, args) -> None:
        """查看任务详情"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        task_info = self.task_manager.get_task_details(args.task_id)
        if task_info:
            print(f"\n=== 任务详情: {args.task_id} ===")
            print(json.dumps(task_info, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"任务 {args.task_id} 不存在")
    
    async def cmd_monitor_start(self, args) -> None:
        """启动监控"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        self.task_manager.start_monitoring()
        print("监控已启动")
    
    async def cmd_monitor_stop(self, args) -> None:
        """停止监控"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        self.task_manager.stop_monitoring()
        print("监控已停止")
    
    async def cmd_monitor_status(self, args) -> None:
        """查看监控状态"""
        if not self.task_manager:
            print("任务管理器未初始化")
            return
        
        stats = self.task_manager.get_task_statistics()
        print("\n=== 监控状态 ===")
        print(f"监控状态: {'运行中' if stats['is_monitoring'] else '已停止'}")
        print(f"总任务数: {stats['total_tasks']}")
        print(f"运行中任务: {stats['running_tasks']}")
        print(f"暂停任务: {stats['paused_tasks']}")
        print(f"错误任务: {stats['error_tasks']}")
        print(f"总执行次数: {stats['total_runs']}")
        print(f"总错误次数: {stats['total_errors']}")
        print(f"错误率: {stats['error_rate']:.2%}")


def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(description='量化交易系统命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 账户相关命令
    account_parser = subparsers.add_parser('account', help='账户相关命令')
    account_subparsers = account_parser.add_subparsers(dest='account_action')
    
    # 账户余额
    balance_parser = account_subparsers.add_parser('balance', help='查询账户余额')
    balance_parser.add_argument('--refresh', action='store_true', help='强制刷新')
    
    # 持仓信息
    positions_parser = account_subparsers.add_parser('positions', help='查询持仓信息')
    positions_parser.add_argument('--refresh', action='store_true', help='强制刷新')
    
    # 历史订单
    orders_parser = account_subparsers.add_parser('orders', help='查询历史订单')
    orders_parser.add_argument('--today', action='store_true', help='只查询今日订单')
    
    # 投资组合摘要
    portfolio_parser = account_subparsers.add_parser('portfolio', help='查询投资组合摘要')
    
    # 策略相关命令
    strategy_parser = subparsers.add_parser('strategy', help='策略相关命令')
    strategy_subparsers = strategy_parser.add_subparsers(dest='strategy_action')
    
    # 策略列表
    strategy_list_parser = strategy_subparsers.add_parser('list', help='列出所有策略')
    
    # 创建策略
    strategy_create_parser = strategy_subparsers.add_parser('create', help='创建策略')
    strategy_create_parser.add_argument('name', help='策略名称')
    strategy_create_parser.add_argument('--short-period', type=int, default=5, help='短期均线周期')
    strategy_create_parser.add_argument('--long-period', type=int, default=20, help='长期均线周期')
    strategy_create_parser.add_argument('--symbols', help='股票代码列表，逗号分隔')
    strategy_create_parser.add_argument('--interval', type=float, default=10.0, help='执行间隔（秒）')
    strategy_create_parser.add_argument('--max-runs', type=int, help='最大执行次数')
    strategy_create_parser.add_argument('--auto-restart', action='store_true', help='自动重启')
    
    # 任务相关命令
    task_parser = subparsers.add_parser('task', help='任务相关命令')
    task_subparsers = task_parser.add_subparsers(dest='task_action')
    
    # 任务列表
    task_list_parser = task_subparsers.add_parser('list', help='列出所有任务')
    
    # 启动任务
    task_start_parser = task_subparsers.add_parser('start', help='启动任务')
    task_start_parser.add_argument('task_id', help='任务ID')
    
    # 停止任务
    task_stop_parser = task_subparsers.add_parser('stop', help='停止任务')
    task_stop_parser.add_argument('task_id', help='任务ID')
    
    # 删除任务
    task_delete_parser = task_subparsers.add_parser('delete', help='删除任务')
    task_delete_parser.add_argument('task_id', help='任务ID')
    
    # 任务详情
    task_info_parser = task_subparsers.add_parser('info', help='查看任务详情')
    task_info_parser.add_argument('task_id', help='任务ID')
    
    # 监控相关命令
    monitor_parser = subparsers.add_parser('monitor', help='监控相关命令')
    monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action')
    
    # 启动监控
    monitor_start_parser = monitor_subparsers.add_parser('start', help='启动监控')
    
    # 停止监控
    monitor_stop_parser = monitor_subparsers.add_parser('stop', help='停止监控')
    
    # 监控状态
    monitor_status_parser = monitor_subparsers.add_parser('status', help='查看监控状态')
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = QuantCLI()
    if not await cli.initialize():
        print("CLI初始化失败")
        sys.exit(1)
    
    try:
        # 账户相关命令
        if args.command == 'account':
            if args.account_action == 'balance':
                await cli.cmd_account_balance(args)
            elif args.account_action == 'positions':
                await cli.cmd_account_positions(args)
            elif args.account_action == 'orders':
                await cli.cmd_account_orders(args)
            elif args.account_action == 'portfolio':
                await cli.cmd_portfolio_summary(args)
        
        # 策略相关命令
        elif args.command == 'strategy':
            if args.strategy_action == 'list':
                await cli.cmd_strategy_list(args)
            elif args.strategy_action == 'create':
                await cli.cmd_strategy_create(args)
        
        # 任务相关命令
        elif args.command == 'task':
            if args.task_action == 'list':
                await cli.cmd_task_list(args)
            elif args.task_action == 'start':
                await cli.cmd_task_start(args)
            elif args.task_action == 'stop':
                await cli.cmd_task_stop(args)
            elif args.task_action == 'delete':
                await cli.cmd_task_delete(args)
            elif args.task_action == 'info':
                await cli.cmd_task_info(args)
        
        # 监控相关命令
        elif args.command == 'monitor':
            if args.monitor_action == 'start':
                await cli.cmd_monitor_start(args)
            elif args.monitor_action == 'stop':
                await cli.cmd_monitor_stop(args)
            elif args.monitor_action == 'status':
                await cli.cmd_monitor_status(args)
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"执行命令时出错: {e}")


if __name__ == '__main__':
    asyncio.run(main())