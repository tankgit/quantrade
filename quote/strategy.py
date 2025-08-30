from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from longport.openapi import QuoteContext, TradeContext, SecurityQuote
from .config import longport_config
from .trade import TradingTimeManager
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, is_paper: bool = False):
        self.name = name
        self.is_paper = is_paper
        self.config = longport_config.get_config(is_paper)
        self.quote_context = None
        self.trade_context = None
        self.positions = {}  # 持仓信息缓存
        self.price_history = {}  # 价格历史缓存

    def initialize_contexts(self):
        """初始化交易和报价上下文"""
        try:
            self.quote_context = QuoteContext(self.config)
            self.trade_context = TradeContext(self.config)
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
    @property
    def cache_data(self) -> Dict:
        """
        获取策略相关缓存数据
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
                return operations

            data = {"current_price": current_price}

            # 检查买入信号
            should_buy, buy_amount = self.should_buy(symbol, data)
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
            should_sell, sell_quantity = self.should_sell(symbol, data)
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
        is_paper: bool = False,
        short_period: int = 5,
        long_period: int = 20,
        buy_amount: Decimal = Decimal("1000"),
    ):
        super().__init__("SimpleMA", is_paper)
        self.short_period = short_period
        self.long_period = long_period
        self.buy_amount = buy_amount  # 每次买入金额
        self.price_history = {}  # 价格历史记录
        self.short_ma_history = {}
        self.long_ma_history = {}

    @property
    def cache_data(self) -> Dict:
        """
        获取策略相关缓存数据
        """
        return {
            "price_history": self.price_history,
            "short_ma_history": self.short_ma_history,
            "long_ma_history": self.long_ma_history,
        }

    def update_price_history(self, symbol: str, price: Decimal):
        """更新价格历史"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []

        self.price_history[symbol].append(float(price))

        # 保持历史记录不超过长期周期的2倍
        max_history = self.long_period * 2
        if len(self.price_history[symbol]) > max_history:
            self.price_history[symbol] = self.price_history[symbol][-max_history:]

    def update_ma_history(self, symbol: str, short_ma: float, long_ma: float):
        """更新移动平均线历史"""
        if symbol not in self.short_ma_history:
            self.short_ma_history[symbol] = []
        if symbol not in self.long_ma_history:
            self.long_ma_history[symbol] = []

        self.short_ma_history[symbol].append(short_ma)
        self.long_ma_history[symbol].append(long_ma)

    def calculate_ma(self, symbol: str, period: int) -> Optional[float]:
        """计算移动平均线"""
        if symbol not in self.price_history:
            return None

        prices = self.price_history[symbol]
        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    def should_buy(self, symbol: str, data: Dict) -> Tuple[bool, Decimal]:
        """买入信号：短期MA上穿长期MA"""
        current_price = data.get("current_price")
        if not current_price:
            return False, Decimal("0")

        # 更新价格历史
        self.update_price_history(symbol, current_price)

        # 计算移动平均线
        short_ma = self.calculate_ma(symbol, self.short_period)
        long_ma = self.calculate_ma(symbol, self.long_period)
        self.update_ma_history(symbol, short_ma, long_ma)

        if short_ma is None or long_ma is None:
            return False, Decimal("0")

        # 检查是否有足够的历史数据来判断趋势
        if len(self.price_history[symbol]) < self.long_period + 1:
            return False, Decimal("0")

        # 计算前一个周期的移动平均线
        prev_short_ma = self.calculate_ma(symbol, self.short_period)
        prev_long_ma = self.calculate_ma(symbol, self.long_period)

        # 如果当前短期MA > 长期MA，且之前短期MA <= 长期MA，则产生买入信号
        if short_ma > long_ma and len(self.price_history[symbol]) > self.long_period:
            # 简单的金叉判断
            prev_prices = self.price_history[symbol][:-1]
            if len(prev_prices) >= self.long_period:
                prev_short = sum(prev_prices[-self.short_period :]) / self.short_period
                prev_long = sum(prev_prices[-self.long_period :]) / self.long_period

                if prev_short <= prev_long:  # 之前短期MA不大于长期MA
                    return True, self.buy_amount

        return False, Decimal("0")

    def should_sell(self, symbol: str, data: Dict) -> Tuple[bool, int]:
        """卖出信号：短期MA下穿长期MA"""
        current_price = data.get("current_price")
        if not current_price:
            return False, 0

        # 计算移动平均线
        short_ma = self.calculate_ma(symbol, self.short_period)
        long_ma = self.calculate_ma(symbol, self.long_period)

        if short_ma is None or long_ma is None:
            return False, 0

        # 检查是否有足够的历史数据
        if len(self.price_history[symbol]) < self.long_period + 1:
            return False, 0

        # 如果当前短期MA < 长期MA，且之前短期MA >= 长期MA，则产生卖出信号
        if short_ma < long_ma:
            prev_prices = self.price_history[symbol][:-1]
            if len(prev_prices) >= self.long_period:
                prev_short = sum(prev_prices[-self.short_period :]) / self.short_period
                prev_long = sum(prev_prices[-self.long_period :]) / self.long_period

                if prev_short >= prev_long:  # 之前短期MA不小于长期MA
                    # 这里需要获取当前持仓数量，简化处理返回一个固定数量
                    # 实际应用中需要查询当前持仓
                    return True, self.get_current_position(symbol)

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
