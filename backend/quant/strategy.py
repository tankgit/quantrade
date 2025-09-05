from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from .utils.context import get_quote_context, get_trade_context
from .trade import TradingTimeManager
from .utils.logger import base_logger

logger = base_logger.getChild("Strategy")


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, task_id: int = None, is_paper: bool = False):
        self.name = name
        self.is_paper = is_paper
        self.quote_context = None
        self.trade_context = None
        self.cache_data = {}
        self.positions = {}  # 持仓信息缓存
        self.task_id = task_id

    def initialize_contexts(self, cache_data: dict = None):
        """初始化交易和报价上下文"""
        try:
            self.quote_context = get_quote_context(self.is_paper)
            self.trade_context = get_trade_context(self.is_paper)
            self.cache_data = cache_data or {}
        except Exception as e:
            logger.error(f"初始化上下文失败: {e}")
            raise

    def get_quotes(self, symbol_list: List[str]) -> Dict[str, Dict]:
        quote_list = self.quote_context.quote(symbol_list)
        price = {}
        for quote in quote_list:
            symbol = quote.symbol
            price[symbol] = {
                "regular_price": quote.last_done,
                "pre_market_price": (
                    quote.pre_market_quote.last_done if quote.pre_market_quote else None
                ),
                "post_market_price": (
                    quote.post_market_quote.last_done
                    if quote.post_market_quote
                    else None
                ),
                "overnight_price": (
                    quote.overnight_quote.last_done if quote.overnight_quote else None
                ),
            }
        return price

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """获取当前股票价格，根据不同时段返回相应价格"""
        try:
            quotes = self.get_quotes([symbol])
            if not quotes:
                return None

            quote = quotes[symbol]
            curr_session = TradingTimeManager.get_us_trading_session()
            if not curr_session:
                return None

            current_price = quote[curr_session + "_price"]
            return current_price

        except Exception as e:
            logger.error(f"获取股票 {symbol} 价格失败: {e}")
            return None

    def get_lot_size(self, symbol: str) -> int:
        """获取股票的最小交易单位"""
        try:
            static_info = self.quote_context.static_info([symbol])
            if static_info:
                return static_info[0].lot_size
            return 1  # 默认最小单位为1
        except Exception as e:
            logger.error(f"获取股票 {symbol} 最小交易单位失败: {e}")
            return 1

    def calculate_position_size(self, symbol: str, target_amount: Decimal) -> int:
        """根据目标金额和lot_size计算实际交易数量"""
        current_price = self.get_current_price(symbol)
        if not current_price:
            return 0

        lot_size = self.get_lot_size(symbol)

        # 计算基础数量
        base_quantity = int(target_amount / current_price)

        # 调整到lot_size的倍数
        adjusted_quantity = (base_quantity // lot_size) * lot_size

        return max(adjusted_quantity, lot_size if adjusted_quantity > 0 else 0)

    @abstractmethod
    def refresh_cache_data(self, data: Dict) -> Dict:
        """
        更新策略相关数据并缓存
        """
        pass

    @abstractmethod
    def should_buy(self, symbol: str, data: Dict) -> Tuple[bool, Decimal]:
        """
        判断是否应该买入
        返回: (是否买入, 买入金额)
        """
        pass

    @abstractmethod
    def should_sell(self, symbol: str, data: Dict) -> Tuple[bool, int]:
        """
        判断是否应该卖出
        返回: (是否卖出, 卖出数量)
        """
        pass

    def process_symbol(self, symbol: str) -> List[Dict]:
        """
        处理单个股票的策略逻辑
        返回操作列表: [{'action': 'buy/sell', 'symbol': str, 'quantity': int, 'price': Decimal}]
        """
        operations = []

        try:
            # 获取当前价格和数据
            current_price = self.get_current_price(symbol)
            if not current_price:
                logger.warning(f"无法获取当前时段股票的价格: {symbol}")
                return operations

            data = {"current_price": current_price}

            success = self.refresh_cache_data(symbol, data)
            if not success:
                return

            # 检查买入信号
            should_buy, buy_amount = self.should_buy(symbol)
            if should_buy and buy_amount > 0:
                quantity = self.calculate_position_size(symbol, buy_amount)
                if quantity > 0:
                    operations.append(
                        {
                            "action": "buy",
                            "symbol": symbol,
                            "quantity": quantity,
                            "price": current_price,
                        }
                    )

            # 检查卖出信号
            should_sell, sell_quantity = self.should_sell(symbol)
            if should_sell and sell_quantity > 0:
                operations.append(
                    {
                        "action": "sell",
                        "symbol": symbol,
                        "quantity": sell_quantity,
                        "price": current_price,
                    }
                )

        except Exception as e:
            logger.error(f"处理股票 {symbol} 策略时出错: {e}")

        return operations


class SimpleMAStrategy(BaseStrategy):
    """简单移动平均线策略"""

    def __init__(
        self,
        task_id: int = None,
        is_paper: bool = False,
        short_period: int = 5,
        long_period: int = 20,
        buy_amount: Decimal = Decimal("10"),
        max_price_history: int = None,
        max_ma_history: int = 10,
    ):
        super().__init__("SimpleMA", task_id, is_paper)
        self.short_period = short_period
        self.long_period = long_period
        self.buy_amount = buy_amount  # 每次买入金额
        self.max_price_history = max(
            max_price_history or self.long_period * 2, self.long_period
        )
        self.max_ma_history = max(max_ma_history, 1)

    def update_price_history(self, symbol: str, price: Decimal):
        """更新价格历史"""
        price_history = self.cache_data.get("price_history", {})
        if symbol not in price_history:
            price_history[symbol] = []

        price_history[symbol].append(float(price))

        # 保持历史记录不超过长期周期的2倍
        price_history[symbol] = price_history[symbol][-self.max_price_history :]
        self.cache_data["price_history"] = price_history

    def update_ma_history(self, symbol: str, short_ma: float, long_ma: float):
        """更新移动平均线历史"""
        short_ma_history = self.cache_data.get("short_ma_history", {})
        long_ma_history = self.cache_data.get("long_ma_history", {})
        if symbol not in short_ma_history:
            short_ma_history[symbol] = []
        if symbol not in long_ma_history:
            long_ma_history[symbol] = []

        short_ma_history[symbol].append(short_ma)
        long_ma_history[symbol].append(long_ma)

        short_ma_history[symbol] = short_ma_history[symbol][-self.max_ma_history :]
        long_ma_history[symbol] = long_ma_history[symbol][-self.max_ma_history :]

        self.cache_data["short_ma_history"] = short_ma_history
        self.cache_data["long_ma_history"] = long_ma_history

    def calculate_ma(self, symbol: str, period: int) -> Optional[float]:
        """计算移动平均线"""
        prices = self.cache_data.get("price_history", {}).get(symbol, [])
        if len(prices) < period:
            return None

        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    def refresh_cache_data(self, symbol, data: Dict) -> bool:
        current_price = data.get("current_price")
        if not current_price:
            return False
        self.update_price_history(symbol, current_price)

        # 计算MA
        short_ma = self.calculate_ma(symbol, self.short_period)
        long_ma = self.calculate_ma(symbol, self.long_period)
        if not short_ma or not long_ma:
            return False
        self.update_ma_history(symbol, short_ma, long_ma)

        return True

    def should_buy(
        self, symbol: str, short_ma: float = None, long_ma: float = None
    ) -> Tuple[bool, Decimal]:
        """买入信号：短期MA上穿长期MA"""
        try:
            short_ma = (
                short_ma
                or self.cache_data.get("short_ma_history", {}).get(symbol, [])[-1]
            )
            long_ma = (
                long_ma
                or self.cache_data.get("long_ma_history", {}).get(symbol, [])[-1]
            )
        except:
            return False, Decimal("0")

        # 如果当前短期MA > 长期MA，且之前短期MA <= 长期MA，则产生买入信号
        price_history = self.cache_data.get("price_history", {}).get(symbol, [])
        print(
            ">>>",
            f"[short {short_ma}]",
            f"[long {long_ma}]",
            f"[short>long? {short_ma > long_ma}]",
            f"[price_history_len {len(price_history)}]",
            f"[long_period {self.long_period}]",
        )
        if short_ma > long_ma and len(price_history) > self.long_period:
            # 简单的金叉判断
            prev_prices = price_history[:-1]
            if len(prev_prices) >= self.long_period:
                prev_short = sum(prev_prices[-self.short_period :]) / self.short_period
                prev_long = sum(prev_prices[-self.long_period :]) / self.long_period

                print(
                    ">>>>",
                    f"[prev_short {prev_short}]",
                    f"[prev_long {prev_long}]",
                    f"[prev_short <= prev_long? {prev_short <= prev_long}]",
                )
                if prev_short <= prev_long:  # 之前短期MA不大于长期MA
                    return True, self.buy_amount

        return False, Decimal("0")

    def should_sell(
        self, symbol: str, short_ma: float = None, long_ma: float = None
    ) -> Tuple[bool, int]:
        """卖出信号：短期MA下穿长期MA"""
        try:
            short_ma = (
                short_ma
                or self.cache_data.get("short_ma_history", {}).get(symbol, [])[-1]
            )
            long_ma = (
                long_ma
                or self.cache_data.get("long_ma_history", {}).get(symbol, [])[-1]
            )
        except:
            return False, Decimal("0")

        # 检查是否有足够的历史数据
        price_history = self.cache_data.get("price_history", {}).get(symbol, [])
        print(
            "<<<",
            f"[short {short_ma}]",
            f"[long {long_ma}]",
            f"[short<long? {short_ma < long_ma}]",
            f"[price_history_len {len(price_history)}]",
            f"[long_period {self.long_period}]",
        )
        if len(price_history) < self.long_period + 1:
            return False, 0

        # 如果当前短期MA < 长期MA，且之前短期MA >= 长期MA，则产生卖出信号
        if short_ma < long_ma:
            prev_prices = price_history[:-1]
            if len(prev_prices) >= self.long_period:
                prev_short = sum(prev_prices[-self.short_period :]) / self.short_period
                prev_long = sum(prev_prices[-self.long_period :]) / self.long_period

                print(
                    "<<<<",
                    f"[prev_short {prev_short}]",
                    f"[prev_long {prev_long}]",
                    f"[prev_short >= prev_long? {prev_short >= prev_long}]",
                )
                if prev_short >= prev_long:  # 之前短期MA不小于长期MA
                    # 获取当前持仓数量，简化处理返回一个固定数量，但不能可交易持仓
                    return True, min(self.get_current_position(symbol), 5)

        return False, 0

    def get_current_position(self, symbol: str) -> int:
        """获取当前持仓数量（简化实现）"""
        try:
            if self.trade_context:
                positions = self.trade_context.stock_positions([symbol])
                if positions.channels:
                    for channel in positions.channels:
                        for position in channel.positions:
                            if position.symbol == symbol:
                                return int(position.available_quantity)
            return 0
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return 0


# 策略注册表
AVAILABLE_STRATEGIES = {
    "SimpleMA": SimpleMAStrategy,
}


def get_strategy(
    strategy_name: str, is_paper: bool = False, **kwargs
) -> Optional[BaseStrategy]:
    """获取策略实例"""
    if strategy_name in AVAILABLE_STRATEGIES:
        strategy_class = AVAILABLE_STRATEGIES[strategy_name]
        return strategy_class(is_paper=is_paper, **kwargs)
    return None


def list_available_strategies() -> List[str]:
    """列出所有可用策略"""
    return list(AVAILABLE_STRATEGIES.keys())
