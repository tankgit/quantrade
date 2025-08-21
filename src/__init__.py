"""
量化交易系统包初始化文件
"""

from .config import TradingConfig, ConfigManager
from .strategy import (
    BaseStrategy,
    SimpleMAStrategy,
    StrategyManager,
    TradingSignal,
    SignalType,
)
from .trade import TradeEngine, TradeOrder, TradeStatus
from .account import AccountManager
from .task import TaskManager, Task, TaskConfig, TaskStatus, TaskType
from .client import QuantCLI


__version__ = "1.0.0"
__author__ = "Quant Trading System"

__all__ = [
    # Config
    "TradingConfig",
    "ConfigManager",
    # Strategy
    "BaseStrategy",
    "SimpleMAStrategy",
    "StrategyManager",
    "TradingSignal",
    "SignalType",
    # Trade
    "TradeEngine",
    "TradeOrder",
    "TradeStatus",
    # Account
    "AccountManager",
    # Task
    "TaskManager",
    "Task",
    "TaskConfig",
    "TaskStatus",
    "TaskType",
    # CMD
    "QuantCLI",
]
