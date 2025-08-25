from typing import Dict, List, Optional, Set
from datetime import datetime, time
from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time as time_module
import logging

from .db import db_manager, AccountType, MarketType, TaskStatus
from .strategy import get_strategy, list_available_strategies
from .trade import get_trade_manager

logger = logging.getLogger(__name__)


class TradingTimeManager:
    """交易时间管理器"""

    # 美股交易时间 (ET)
    US_PREMARKET_START = time(4, 0)  # 04:00 ET
    US_PREMARKET_END = time(9, 30)  # 09:30 ET
    US_MARKET_START = time(9, 30)  # 09:30 ET
    US_MARKET_END = time(16, 0)  # 16:00 ET
    US_POSTMARKET_START = time(16, 0)  # 16:00 ET
    US_POSTMARKET_END = time(20, 0)  # 20:00 ET
    US_OVERNIGHT_START = time(20, 0)  # 20:00 ET
    US_OVERNIGHT_END = time(4, 0)  # 04:00 ET (next day)

    # 港股交易时间 (HKT)
    HK_MORNING_START = time(9, 30)  # 09:30 HKT
    HK_MORNING_END = time(12, 0)  # 12:00 HKT
    HK_AFTERNOON_START = time(13, 0)  # 13:00 HKT
    HK_AFTERNOON_END = time(16, 0)  # 16:00 HKT

    @classmethod
    def is_us_trading_time(cls, current_time: time, trading_sessions: Set[str]) -> bool:
        """检查是否在美股交易时间内"""
        if "premarket" in trading_sessions:
            if cls.US_PREMARKET_START <= current_time < cls.US_PREMARKET_END:
                return True

        if "market" in trading_sessions:
            if cls.US_MARKET_START <= current_time < cls.US_MARKET_END:
                return True

        if "postmarket" in trading_sessions:
            if cls.US_POSTMARKET_START <= current_time < cls.US_POSTMARKET_END:
                return True

        if "overnight" in trading_sessions:
            if (
                current_time >= cls.US_OVERNIGHT_START
                or current_time < cls.US_OVERNIGHT_END
            ):
                return True

        return False

    @classmethod
    def is_hk_trading_time(cls, current_time: time) -> bool:
        """检查是否在港股交易时间内"""
        return (cls.HK_MORNING_START <= current_time < cls.HK_MORNING_END) or (
            cls.HK_AFTERNOON_START <= current_time < cls.HK_AFTERNOON_END
        )


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running_tasks = {}  # task_id -> {'thread': Thread, 'stop_event': Event}
        self.scheduler.start()
        logger.info("任务管理器初始化完成")

    def create_task(
        self,
        account: str,
        market: str,
        symbols: List[str],
        strategy: str,
        trading_sessions: Optional[List[str]] = None,
    ) -> int:
        """
        创建新任务

        Args:
            account: 账户类型 ('实盘' 或 '模拟盘')
            market: 市场类型 ('美股' 或 '港股')
            symbols: 股票代码列表
            strategy: 策略名称
            trading_sessions: 交易时段 ['premarket', 'market', 'postmarket', 'overnight']

        Returns:
            任务ID
        """
        try:
            if db_manager is None:
                raise Exception("数据库未初始化")

            account_type = AccountType.LIVE if account == "实盘" else AccountType.PAPER
            market_type = MarketType.US if market == "美股" else MarketType.HK

            task_id = db_manager.create_task(
                account=account_type,
                market=market_type,
                symbols=symbols,
                strategy=strategy,
            )

            logger.info(
                f"任务创建成功: ID={task_id}, 账户={account}, 市场={market}, 策略={strategy}"
            )
            return task_id

        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise

    def start_task(
        self, task_id: int, trading_sessions: Optional[List[str]] = None
    ) -> bool:
        """启动任务"""
        try:
            if db_manager is None:
                logger.error("数据库未初始化")
                return False

            task = db_manager.get_task(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return False

            if task_id in self.running_tasks:
                logger.warning(f"任务已在运行: {task_id}")
                return True

            # 更新任务状态
            db_manager.update_task_status(task_id, TaskStatus.RUNNING)

            # 创建停止事件
            stop_event = Event()

            # 创建并启动任务线程
            if trading_sessions and task.market == MarketType.US:
                # 美股按时段运行
                thread = Thread(
                    target=self._run_scheduled_task,
                    args=(task_id, stop_event, set(trading_sessions)),
                )
            else:
                # 持续运行
                thread = Thread(
                    target=self._run_continuous_task, args=(task_id, stop_event)
                )

            thread.daemon = True
            thread.start()

            self.running_tasks[task_id] = {
                "thread": thread,
                "stop_event": stop_event,
                "trading_sessions": trading_sessions or [],
            }

            logger.info(f"任务启动成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"启动任务失败: {task_id}, 错误: {e}")
            return False

    def pause_task(self, task_id: int) -> bool:
        """暂停任务"""
        try:
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["stop_event"].set()
                self.running_tasks[task_id]["thread"].join(timeout=5.0)
                del self.running_tasks[task_id]

            db_manager.update_task_status(task_id, TaskStatus.PAUSED)
            logger.info(f"任务暂停成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"暂停任务失败: {task_id}, 错误: {e}")
            return False

    def stop_task(self, task_id: int) -> bool:
        """停止任务"""
        try:
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["stop_event"].set()
                self.running_tasks[task_id]["thread"].join(timeout=5.0)
                del self.running_tasks[task_id]

            db_manager.update_task_status(task_id, TaskStatus.STOPPED)
            logger.info(f"任务停止成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"停止任务失败: {task_id}, 错误: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        try:
            # 先停止任务
            if task_id in self.running_tasks:
                self.stop_task(task_id)

            # 删除数据库记录
            result = db_manager.delete_task(task_id)
            if result:
                logger.info(f"任务删除成功: {task_id}")

            return result

        except Exception as e:
            logger.error(f"删除任务失败: {task_id}, 错误: {e}")
            return False

    def get_task_info(self, task_id: int) -> Optional[Dict]:
        """获取任务信息"""
        try:
            task = db_manager.get_task(task_id)
            if not task:
                return None

            return {
                "task_id": task.task_id,
                "account": task.account.value,
                "market": task.market.value,
                "symbols": task.get_symbols_list(),
                "strategy": task.strategy,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "is_running": task_id in self.running_tasks,
                "trading_sessions": self.running_tasks.get(task_id, {}).get(
                    "trading_sessions", []
                ),
            }

        except Exception as e:
            logger.error(f"获取任务信息失败: {task_id}, 错误: {e}")
            return None

    def list_all_tasks(self) -> List[Dict]:
        """列出所有任务"""
        try:
            tasks = db_manager.get_all_tasks()
            result = []

            for task in tasks:
                task_info = {
                    "task_id": task.task_id,
                    "account": task.account.value,
                    "market": task.market.value,
                    "symbols": task.get_symbols_list(),
                    "strategy": task.strategy,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "is_running": task.task_id in self.running_tasks,
                }
                result.append(task_info)

            return result

        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return []

    def get_task_logs(self, task_id: int) -> List[Dict]:
        """获取任务操作日志"""
        try:
            logs = db_manager.get_task_logs(task_id)
            result = []

            for log in logs:
                log_info = {
                    "log_id": log.log_id,
                    "task_id": log.task_id,
                    "symbol": log.symbol,
                    "operation": log.op.value,
                    "price": log.price,
                    "quantity": log.qty,
                    "created_at": log.created_at.isoformat(),
                }
                result.append(log_info)

            return result

        except Exception as e:
            logger.error(f"获取任务日志失败: {task_id}, 错误: {e}")
            return []

    def _run_continuous_task(self, task_id: int, stop_event: Event):
        """运行持续任务"""
        try:
            task = db_manager.get_task(task_id)
            if not task:
                return

            # 获取策略实例
            is_paper = task.account == AccountType.PAPER
            strategy = get_strategy(task.strategy, is_paper=is_paper)
            if not strategy:
                logger.error(f"策略不存在: {task.strategy}")
                return

            strategy.initialize_contexts()

            # 获取交易管理器
            trade_manager = get_trade_manager(is_paper=is_paper)

            symbols = task.get_symbols_list()

            while not stop_event.is_set():
                try:
                    # 处理每个股票
                    for symbol in symbols:
                        if stop_event.is_set():
                            break

                        operations = strategy.process_symbol(symbol)
                        if operations:
                            results = trade_manager.execute_strategy_operations(
                                task_id, operations
                            )
                            logger.info(f"任务 {task_id} 执行操作: {results}")

                    # 等待一段时间再进行下次检查
                    stop_event.wait(60)  # 等待60秒

                except Exception as e:
                    logger.error(f"任务执行出错: {task_id}, 错误: {e}")
                    stop_event.wait(60)

        except Exception as e:
            logger.error(f"任务运行失败: {task_id}, 错误: {e}")
        finally:
            logger.info(f"任务停止运行: {task_id}")

    def _run_scheduled_task(
        self, task_id: int, stop_event: Event, trading_sessions: Set[str]
    ):
        """运行定时任务（美股按时段）"""
        try:
            task = db_manager.get_task(task_id)
            if not task:
                return

            # 获取策略实例
            is_paper = task.account == AccountType.PAPER
            strategy = get_strategy(task.strategy, is_paper=is_paper)
            if not strategy:
                logger.error(f"策略不存在: {task.strategy}")
                return

            strategy.initialize_contexts()

            # 获取交易管理器
            trade_manager = get_trade_manager(is_paper=is_paper)

            symbols = task.get_symbols_list()

            while not stop_event.is_set():
                try:
                    current_time = datetime.now().time()

                    # 检查是否在交易时间内
                    if TradingTimeManager.is_us_trading_time(
                        current_time, trading_sessions
                    ):
                        # 处理每个股票
                        for symbol in symbols:
                            if stop_event.is_set():
                                break

                            operations = strategy.process_symbol(symbol)
                            if operations:
                                results = trade_manager.execute_strategy_operations(
                                    task_id, operations
                                )
                                logger.info(f"任务 {task_id} 执行操作: {results}")

                        # 交易时间内，每分钟检查一次
                        stop_event.wait(60)
                    else:
                        # 非交易时间，每10分钟检查一次
                        stop_event.wait(600)

                except Exception as e:
                    logger.error(f"定时任务执行出错: {task_id}, 错误: {e}")
                    stop_event.wait(60)

        except Exception as e:
            logger.error(f"定时任务运行失败: {task_id}, 错误: {e}")
        finally:
            logger.info(f"定时任务停止运行: {task_id}")

    def get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        return list_available_strategies()

    def get_running_tasks_count(self) -> int:
        """获取正在运行的任务数量"""
        return len(self.running_tasks)

    def shutdown(self):
        """关闭任务管理器"""
        try:
            # 停止所有运行中的任务
            for task_id in list(self.running_tasks.keys()):
                self.stop_task(task_id)

            # 关闭调度器
            self.scheduler.shutdown()
            logger.info("任务管理器已关闭")

        except Exception as e:
            logger.error(f"关闭任务管理器失败: {e}")


# 全局任务管理器实例
task_manager = TaskManager()
