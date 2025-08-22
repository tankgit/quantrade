"""
量化交易系统主程序示例
"""

import asyncio
import logging
import os
from datetime import datetime
from symtable import Symbol

# 导入模块
from src.config import TradingConfig, ConfigManager
from src.strategy import SimpleMAStrategy, StrategyManager
from src.account import AccountManager
from src.task import TaskManager, TaskConfig


async def main():
    """主函数示例"""

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("main")

    print("=== 量化交易系统启动 ===")

    try:
        # 1. 配置系统
        print("\n1. 初始化配置...")

        # 方法1: 从环境变量加载配置
        # config = TradingConfig.from_env()

        # 方法2: 手动创建配置
        config = TradingConfig.from_env()

        # 加载配置
        config_manager = ConfigManager()
        config_manager.load_config(config)

        print(f"配置加载完成 - 环境: {'模拟盘' if config.is_sandbox else '实盘'}")

        # 2. 初始化各个管理器
        print("\n2. 初始化系统组件...")

        # 创建任务管理器
        task_manager = TaskManager(config)
        if not await task_manager.initialize():
            print("任务管理器初始化失败")
            return

        account_manager = task_manager.account_manager

        print("系统组件初始化完成")

        # 3. 查询账户信息
        print("\n3. 查询账户信息...")

        # 获取投资组合摘要
        portfolio = await account_manager.get_portfolio_summary()
        if portfolio:
            balance = portfolio["account_info"]
            if balance:
                print("【账户资产】")
                for ci in balance.cash_infos:
                    print(f"- {ci.currency}: {ci.available_cash:,.2f}")
                print(f"- 总购买力 {balance.buy_power:,.2f} {balance.currency}")

            print()
            print("【持仓】")
            print(f"- 总市值: {portfolio['total_market_value']:,.2f}")
            print(
                f"- 总盈亏: {portfolio['total_unrealized_pnl']:,.2f} ({portfolio['total_unrealized_pnl_percent']:.2f}%)"
            )
            positions = portfolio.get("positions")
            positions_latest_price = portfolio.get("positions_latest_price")
            if positions and positions_latest_price:
                for pos in positions:
                    symbol = pos.symbol
                    cost_price = pos.cost_price
                    latest_price = positions_latest_price.get(symbol, 0.0)
                    quantity = pos.quantity
                    pnl = (latest_price - cost_price) * quantity
                    pnl_percent = (
                        (pnl / (cost_price * quantity)) * 100 if cost_price else 0.0
                    )
                    print(
                        f"- {symbol}: QTY[{quantity}], MP/Cost[{latest_price:.2f}/{cost_price:.2f}], P/L[{pnl:,.2f}, {pnl_percent:.2f}%]"
                    )

        # 4. 创建交易策略
        print("\n4. 创建交易策略...")

        # 创建简单移动平均策略
        ma_strategy = SimpleMAStrategy(
            short_period=5, long_period=20, symbols=["00981.HK"]
        )

        print(f"创建策略: {ma_strategy.name}")
        print(f"监控股票: {ma_strategy.symbols}")

        # 5. 创建策略任务
        print("\n5. 创建策略任务...")

        # 配置任务参数
        task_config = TaskConfig(
            interval=10.0,  # 每10秒执行一次
            max_runs=5000,  # 最多执行100次
            auto_restart=False,
        )

        # 创建策略任务
        task_id = task_manager.create_strategy_task(
            name="MA策略-港股",
            strategy=ma_strategy,
            symbols=ma_strategy.symbols,
            config=task_config,
        )

        print(f"策略任务创建成功: {task_id}")

        # 6. 启动任务和监控
        print("\n6. 启动任务和监控...")

        # 启动策略任务
        success = task_manager.start_task(task_id)
        if success:
            print(f"任务 {task_id} 启动成功")

        # 启动监控
        task_manager.start_monitoring()
        print("监控已启动")

        # 7. 运行一段时间
        print("\n7. 运行系统...")
        print("系统将运行60秒，按 Ctrl+C 可提前停止")

        try:
            # await asyncio.sleep(60)  # 运行60秒
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n收到中断信号...")

        # 8. 查看运行结果
        print("\n8. 查看运行结果...")

        # 获取任务统计
        stats = task_manager.get_task_statistics()
        print(f"任务统计:")
        print(f"- 总任务数: {stats['total_tasks']}")
        print(f"- 运行中任务: {stats['running_tasks']}")
        print(f"- 总执行次数: {stats['total_runs']}")
        print(f"- 总错误次数: {stats['total_errors']}")

        # 获取策略信息
        strategies_info = task_manager.strategy_manager.get_strategies_info()
        for name, info in strategies_info.items():
            print(f"策略 {name}:")
            print(f"- 总信号数: {info['total_signals']}")
            print(f"- 买入信号: {info['buy_signals']}")
            print(f"- 卖出信号: {info['sell_signals']}")

        # 获取交易统计
        trade_stats = task_manager.trade_engine.get_trading_stats()
        print(f"交易统计:")
        print(f"- 总订单数: {trade_stats['total_orders']}")
        print(f"- 成交订单: {trade_stats['filled_orders']}")
        print(f"- 待处理订单: {trade_stats['pending_orders']}")
        print(f"- 成功率: {trade_stats['success_rate']:.2%}")

        # 9. 停止系统
        print("\n9. 停止系统...")

        # 停止任务
        task_manager.stop_task(task_id)
        print(f"任务 {task_id} 已停止")

        # 停止监控
        task_manager.stop_monitoring()
        print("监控已停止")

        print("\n=== 系统已安全退出 ===")

    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"程序执行出错: {e}")


async def simple_demo():
    """简单演示"""
    print("=== 简单演示 ===")

    # 创建配置
    config = TradingConfig.from_env()

    # 创建账户管理器
    account_manager = AccountManager(config)
    await account_manager.initialize()

    # 查询账户信息
    balance = await account_manager.get_account_balance()
    positions = await account_manager.get_positions()

    print(f"账户信息: {balance}")
    print(f"持仓数量: {len(positions)}")
    print(f"持仓: {positions}")

    # 创建简单策略
    strategy = SimpleMAStrategy(short_period=5, long_period=10)

    # 模拟市场数据测试策略
    market_data = {
        "symbol": "00700.HK",
        "close": 450.0,
        "timestamp": datetime.now().isoformat(),
    }

    # 生成多个价格点来测试策略
    for i in range(25):
        market_data["close"] = 450.0 + i * 0.5  # 价格逐渐上涨
        signals = strategy.calculate_signals(market_data)

        if signals:
            for signal in signals:
                print(
                    f"生成信号: {signal.symbol} - {signal.signal_type.value} - 强度: {signal.strength:.3f} - 原因: {signal.reason}"
                )

    print("简单演示完成")


if __name__ == "__main__":
    """
    运行方式:
    1. 完整演示: python main.py
    2. 简单演示: 修改下面的函数调用
    3. 命令行工具: python -m src.cmd --help
    """

    # 可以选择运行完整演示或简单演示
    asyncio.run(main())  # 完整演示
    # asyncio.run(simple_demo())  # 简单演示
