"""
任务模块 - 管理策略运行任务
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

from .config import TradingConfig
from .strategy import BaseStrategy, StrategyManager
from .trade import TradeEngine
from .account import AccountManager


class TaskStatus(Enum):
    """任务状态"""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class TaskType(Enum):
    """任务类型"""

    STRATEGY = "STRATEGY"  # 策略执行任务
    MONITOR = "MONITOR"  # 监控任务
    SCHEDULE = "SCHEDULE"  # 定时任务


@dataclass
class TaskConfig:
    """任务配置"""

    interval: float = 10.0  # 执行间隔（秒）
    max_runs: Optional[int] = None  # 最大执行次数
    start_time: Optional[datetime] = None  # 开始时间
    end_time: Optional[datetime] = None  # 结束时间
    auto_restart: bool = False  # 是否自动重启
    error_threshold: int = 5  # 错误阈值


@dataclass
class Task:
    """任务对象"""

    task_id: str
    name: str
    task_type: TaskType
    config: TaskConfig
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

    # 关联的策略或处理函数
    strategy: Optional[BaseStrategy] = None
    handler: Optional[Callable] = None

    def should_run(self) -> bool:
        """检查是否应该执行"""
        now = datetime.now()

        # 检查时间范围
        if self.config.start_time and now < self.config.start_time:
            return False
        if self.config.end_time and now > self.config.end_time:
            return False

        # 检查最大执行次数
        if self.config.max_runs and self.run_count >= self.config.max_runs:
            return False

        # 检查错误次数
        if self.error_count >= self.config.error_threshold:
            return False

        return self.status == TaskStatus.RUNNING

    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]


class StrategyTask(Task):
    """策略执行任务"""

    def __init__(
        self,
        task_id: str,
        name: str,
        strategy: BaseStrategy,
        config: TaskConfig,
        symbols: List[str],
    ):
        super().__init__(task_id, name, TaskType.STRATEGY, config)
        self.strategy = strategy
        self.symbols = symbols
        self.last_execution: Optional[datetime] = None


class TaskManager:
    """任务管理器"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger("task_manager")

        # 核心组件
        self.strategy_manager = StrategyManager()
        self.trade_engine = TradeEngine(config)
        self.account_manager = AccountManager(config)

        # 任务管理
        self._tasks: Dict[str, Task] = {}
        self._task_counter = 0
        self._running = False
        self._executor_thread: Optional[threading.Thread] = None

        # 监控数据
        self._market_data_cache: Dict[str, Any] = {}

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        self._task_counter += 1
        return f"TASK_{self._task_counter:06d}"

    async def initialize(self) -> bool:
        """初始化任务管理器"""
        try:
            # 初始化交易引擎
            if not await self.trade_engine.initialize():
                return False

            # 初始化账户管理器
            if not await self.account_manager.initialize():
                return False

            self.logger.info("任务管理器初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"任务管理器初始化失败: {e}")
            return False

    def create_strategy_task(
        self, name: str, strategy: BaseStrategy, symbols: List[str], config: TaskConfig
    ) -> str:
        """创建策略任务"""
        task_id = self._generate_task_id()

        # 添加策略到策略管理器
        self.strategy_manager.add_strategy(strategy)

        # 创建任务
        task = StrategyTask(task_id, name, strategy, config, symbols)
        self._tasks[task_id] = task

        self.logger.info(f"创建策略任务: {task_id} - {name}")
        return task_id

    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        task = self._tasks.get(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        if task.status == TaskStatus.RUNNING:
            self.logger.warning(f"任务已在运行: {task_id}")
            return True

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        # 启动关联的策略
        if task.strategy:
            self.strategy_manager.start_strategy(task.strategy.name)

        self.logger.info(f"任务已启动: {task_id}")
        return True

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        task = self._tasks.get(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        if task.status != TaskStatus.RUNNING:
            self.logger.warning(f"任务未在运行: {task_id}")
            return False

        task.status = TaskStatus.PAUSED

        # 停止关联的策略
        if task.strategy:
            self.strategy_manager.stop_strategy(task.strategy.name)

        self.logger.info(f"任务已暂停: {task_id}")
        return True

    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        task = self._tasks.get(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        task.status = TaskStatus.STOPPED
        task.stopped_at = datetime.now()

        # 停止关联的策略
        if task.strategy:
            self.strategy_manager.stop_strategy(task.strategy.name)

        self.logger.info(f"任务已停止: {task_id}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task = self._tasks.get(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return False

        # 先停止任务
        if task.is_active():
            self.stop_task(task_id)

        # 移除策略
        if task.strategy:
            self.strategy_manager.remove_strategy(task.strategy.name)

        # 删除任务
        del self._tasks[task_id]
        self.logger.info(f"任务已删除: {task_id}")
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Task]:
        """获取所有任务"""
        return self._tasks.copy()

    def get_running_tasks(self) -> Dict[str, Task]:
        """获取运行中的任务"""
        return {
            task_id: task
            for task_id, task in self._tasks.items()
            if task.status == TaskStatus.RUNNING
        }

    def start_monitoring(self) -> None:
        """启动监控"""
        if self._running:
            self.logger.warning("监控已在运行中")
            return

        self._running = True
        self._executor_thread = threading.Thread(target=self._run_monitor_loop)
        self._executor_thread.daemon = True
        self._executor_thread.start()

        self.logger.info("监控已启动")

    def stop_monitoring(self) -> None:
        """停止监控"""
        self._running = False
        if self._executor_thread and self._executor_thread.is_alive():
            self._executor_thread.join(timeout=5)

        self.logger.info("监控已停止")

    def _run_monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                # 执行所有运行中的任务
                asyncio.run(self._execute_tasks())
                time.sleep(1)  # 基础睡眠间隔
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                time.sleep(5)

    async def _execute_tasks(self) -> None:
        """执行任务"""
        running_tasks = self.get_running_tasks()

        for task_id, task in running_tasks.items():
            try:
                if not task.should_run():
                    continue

                # 检查执行间隔
                now = datetime.now()
                if task.last_execution and now - task.last_execution < timedelta(
                    seconds=task.config.interval
                ):
                    continue

                # 执行任务
                await self._execute_single_task(task)
                task.last_execution = now
                task.run_count += 1

            except Exception as e:
                task.error_count += 1
                task.last_error = str(e)
                self.logger.error(f"任务执行失败 {task_id}: {e}")

                # 检查是否需要停止任务
                if task.error_count >= task.config.error_threshold:
                    task.status = TaskStatus.ERROR
                    self.logger.error(f"任务错误次数过多，已停止: {task_id}")

    async def _execute_single_task(self, task: Task) -> None:
        """执行单个任务"""
        if task.task_type == TaskType.STRATEGY:
            await self._execute_strategy_task(task)
        else:
            self.logger.warning(f"不支持的任务类型: {task.task_type}")

    async def _execute_strategy_task(self, task: StrategyTask) -> None:
        """执行策略任务"""
        if not task.strategy or not task.strategy.is_active():
            return

        # 获取账户信息
        account_info = await self.account_manager.get_account_balance()
        positions = await self.account_manager.get_positions()

        if not account_info:
            self.logger.warning("无法获取账户信息")
            return

        # 为每个股票生成市场数据并计算信号
        for symbol in task.symbols:
            # 这里应该获取实际的市场数据
            # market_data = await self._get_market_data(symbol)

            # 模拟市场数据
            market_data = {
                "symbol": symbol,
                "close": 100.0 + task.run_count * 0.1,  # 模拟价格变化
                "timestamp": datetime.now().isoformat(),
            }

            # 计算信号
            signals = task.strategy.calculate_signals(market_data)

            # 执行信号
            if signals:
                account_value = account_info.get("total_power", 0)
                position_dict = {pos["symbol"]: pos["quantity"] for pos in positions}

                orders = await self.trade_engine.batch_execute_signals(
                    signals, account_value, position_dict
                )

                if orders:
                    self.logger.info(
                        f"策略 {task.strategy.name} 执行了 {len(orders)} 个订单"
                    )

    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = len(self._tasks)
        running_tasks = len(
            [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
        )
        paused_tasks = len(
            [t for t in self._tasks.values() if t.status == TaskStatus.PAUSED]
        )
        error_tasks = len(
            [t for t in self._tasks.values() if t.status == TaskStatus.ERROR]
        )

        total_runs = sum(task.run_count for task in self._tasks.values())
        total_errors = sum(task.error_count for task in self._tasks.values())

        return {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "paused_tasks": paused_tasks,
            "error_tasks": error_tasks,
            "total_runs": total_runs,
            "total_errors": total_errors,
            "error_rate": total_errors / total_runs if total_runs > 0 else 0,
            "is_monitoring": self._running,
        }

    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """获取任务详细信息"""
        task = self._tasks.get(task_id)
        if not task:
            return {}

        return {
            "task_id": task.task_id,
            "name": task.name,
            "type": task.task_type.value,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "stopped_at": task.stopped_at.isoformat() if task.stopped_at else None,
            "run_count": task.run_count,
            "error_count": task.error_count,
            "last_error": task.last_error,
            "config": {
                "interval": task.config.interval,
                "max_runs": task.config.max_runs,
                "auto_restart": task.config.auto_restart,
                "error_threshold": task.config.error_threshold,
            },
            "strategy_info": (
                task.strategy.get_strategy_info() if task.strategy else None
            ),
        }
