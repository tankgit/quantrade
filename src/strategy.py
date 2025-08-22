"""
策略模块 - 提供策略基类和各种交易策略实现
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging


class SignalType(Enum):
    """信号类型"""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradingSignal:
    """交易信号"""

    symbol: str
    signal_type: SignalType
    strength: float  # 信号强度 0-1
    price: Optional[float] = None
    quantity: Optional[int] = None
    reason: Optional[str] = None
    timestamp: Optional[str] = None


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params = params or {}
        self.logger = logging.getLogger(f"strategy.{name}")
        self._is_active = False

        # 策略统计
        self.total_signals = 0
        self.buy_signals = 0
        self.sell_signals = 0

    @abstractmethod
    def calculate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """计算交易信号"""
        pass

    @abstractmethod
    def get_required_data(self) -> List[str]:
        """获取策略所需的数据字段"""
        pass

    def validate_params(self) -> bool:
        """验证参数有效性"""
        return True

    def on_signal_generated(self, signal: TradingSignal) -> None:
        """信号生成时的回调"""
        self.total_signals += 1
        if signal.signal_type == SignalType.BUY:
            self.buy_signals += 1
        elif signal.signal_type == SignalType.SELL:
            self.sell_signals += 1

    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "name": self.name,
            "params": self.params,
            "is_active": self._is_active,
            "total_signals": self.total_signals,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
        }

    def start(self) -> None:
        """启动策略"""
        self._is_active = True
        self.logger.info(f"策略 {self.name} 已启动")

    def stop(self) -> None:
        """停止策略"""
        self._is_active = False
        self.logger.info(f"策略 {self.name} 已停止")

    def is_active(self) -> bool:
        """是否激活"""
        return self._is_active


class SimpleMAStrategy(BaseStrategy):
    """简单移动平均策略"""

    def __init__(
        self,
        short_period: int = 5,
        long_period: int = 20,
        symbols: Optional[List[str]] = None,
    ):
        params = {
            "short_period": short_period,
            "long_period": long_period,
            "symbols": symbols or [],
        }
        super().__init__("SimpleMA", params)

        self.short_period = short_period
        self.long_period = long_period
        self.symbols = symbols or []
        self._price_history: Dict[str, List[float]] = {}

    def get_required_data(self) -> List[str]:
        """获取所需数据字段"""
        return ["close", "symbol", "timestamp"]

    def validate_params(self) -> bool:
        """验证参数"""
        if self.short_period >= self.long_period:
            self.logger.error("短期均线周期必须小于长期均线周期")
            return False
        if self.short_period < 1 or self.long_period < 2:
            self.logger.error("均线周期必须大于0")
            return False
        return True

    def _update_price_history(self, symbol: str, price: float) -> None:
        """更新价格历史"""
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        self._price_history[symbol].append(price)

        # 保留足够的历史数据
        max_len = self.long_period * 2
        if len(self._price_history[symbol]) > max_len:
            self._price_history[symbol] = self._price_history[symbol][-max_len:]

    def _calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """计算移动平均"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def calculate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """计算交易信号"""
        signals = []

        symbol = market_data.get("symbol")
        close_price = market_data.get("close")
        timestamp = market_data.get("timestamp")

        if not all([symbol, close_price]):
            return signals

        # 如果指定了特定股票，只处理这些股票
        if self.symbols and symbol not in self.symbols:
            return signals

        # 更新价格历史
        self._update_price_history(symbol, close_price)

        prices = self._price_history[symbol]
        if len(prices) < self.long_period:
            return signals

        # 计算短期和长期移动平均
        short_ma = self._calculate_ma(prices, self.short_period)
        long_ma = self._calculate_ma(prices, self.long_period)

        if short_ma is None or long_ma is None:
            return signals

        # 计算前一期的移动平均（用于判断交叉）
        prev_short_ma = (
            self._calculate_ma(prices[:-1], self.short_period)
            if len(prices) > self.short_period
            else None
        )
        prev_long_ma = (
            self._calculate_ma(prices[:-1], self.long_period)
            if len(prices) > self.long_period
            else None
        )

        if prev_short_ma is None or prev_long_ma is None:
            return signals

        # 生成信号
        signal_strength = abs(short_ma - long_ma) / long_ma  # 信号强度

        # 金叉：短期均线向上穿越长期均线
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=min(signal_strength, 1.0),
                price=close_price,
                reason=f"金叉：短期MA({short_ma:.2f}) > 长期MA({long_ma:.2f})",
                timestamp=timestamp,
            )
            signals.append(signal)
            self.on_signal_generated(signal)

        # 死叉：短期均线向下穿越长期均线
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=min(signal_strength, 1.0),
                price=close_price,
                reason=f"死叉：短期MA({short_ma:.2f}) < 长期MA({long_ma:.2f})",
                timestamp=timestamp,
            )
            signals.append(signal)
            self.on_signal_generated(signal)

        return signals


class StrategyManager:
    """策略管理器"""

    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
        self.logger = logging.getLogger("strategy_manager")

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """添加策略"""
        if not strategy.validate_params():
            raise ValueError(f"策略 {strategy.name} 参数验证失败")

        self._strategies[strategy.name] = strategy
        self.logger.info(f"添加策略: {strategy.name}")

    def remove_strategy(self, name: str) -> None:
        """移除策略"""
        if name in self._strategies:
            self._strategies[name].stop()
            del self._strategies[name]
            self.logger.info(f"移除策略: {name}")

    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self._strategies.get(name)

    def get_all_strategies(self) -> Dict[str, BaseStrategy]:
        """获取所有策略"""
        return self._strategies.copy()

    def start_strategy(self, name: str) -> None:
        """启动策略"""
        strategy = self._strategies.get(name)
        if strategy:
            strategy.start()
        else:
            self.logger.warning(f"策略 {name} 不存在")

    def stop_strategy(self, name: str) -> None:
        """停止策略"""
        strategy = self._strategies.get(name)
        if strategy:
            strategy.stop()
        else:
            self.logger.warning(f"策略 {name} 不存在")

    def calculate_all_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """计算所有策略的信号"""
        all_signals = []
        for strategy in self._strategies.values():
            if strategy.is_active():
                try:
                    signals = strategy.calculate_signals(market_data)
                    all_signals.extend(signals)
                except Exception as e:
                    self.logger.error(f"策略 {strategy.name} 计算信号时出错: {e}")

        return all_signals

    def get_strategies_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略信息"""
        return {
            name: strategy.get_strategy_info()
            for name, strategy in self._strategies.items()
        }
