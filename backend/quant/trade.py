from typing import Dict, List, Optional, Set
from datetime import datetime, time

from pytz import timezone
from decimal import Decimal
from longport.openapi import (
    TradeContext,
    QuoteContext,
    Order,
    OrderSide,
    OrderType,
    TimeInForceType,
)
from .utils.context import get_trade_context, get_quote_context
from .utils.db import db_manager, OperationType
from .utils.logger import base_logger, SUCCESS

logger = base_logger.getChild("Trade")


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
    def is_trading_time(cls, symbol: str):
        """检查是否在交易时间内"""
        try:
            if symbol.endswith(".US"):
                current_time = datetime.now(timezone("US/Eastern")).time()
                return cls.is_us_trading_time(
                    current_time, {"premarket", "regular", "postmarket", "overnight"}
                )
            elif symbol.endswith(".HK"):
                current_time = datetime.now(timezone("Asia/Hong_Kong")).time()
                return cls.is_hk_trading_time(current_time)
            else:
                logger.warning(f"未知市场代码: {symbol}")
                return False
        except Exception as e:
            logger.error(f"检查交易时间失败: {e}")
            return False

    @classmethod
    def get_us_trading_session(cls, current_time: time = None) -> Optional[str]:
        """获取当前美股交易时段"""
        current_time = current_time or datetime.now(timezone("US/Eastern")).time()
        if cls.US_PREMARKET_START <= current_time < cls.US_PREMARKET_END:
            return "pre_market"
        elif cls.US_MARKET_START <= current_time < cls.US_MARKET_END:
            return "regular"
        elif cls.US_POSTMARKET_START <= current_time < cls.US_POSTMARKET_END:
            return "post_market"
        elif (
            current_time >= cls.US_OVERNIGHT_START
            or current_time < cls.US_OVERNIGHT_END
        ):
            # 因为跨天了，所以跟别的判断条件不同
            # NOTE: 注意，由于当前没有订阅夜盘，所以夜盘价格目前是空
            return "overnight"
        else:
            return None

    @classmethod
    def is_us_trading_time(cls, current_time: time, trading_sessions: Set[str]) -> bool:
        """检查是否在美股交易时间内"""
        if "premarket" in trading_sessions:
            if cls.US_PREMARKET_START <= current_time < cls.US_PREMARKET_END:
                return True

        if "regular" in trading_sessions:
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


class SubmitOrderResponse:
    """
    Response for submit order request
    """

    order_id: str
    """
    Order id
    """


class TradeManager:
    """交易管理器"""

    def __init__(self, is_paper: bool = False):
        self.is_paper = is_paper
        self.trade_context = None
        self.quote_context = None
        self.initialize_contexts()

    def initialize_contexts(self):
        """初始化交易上下文"""
        try:
            self.trade_context = get_trade_context(is_paper=self.is_paper)
            self.quote_context = get_quote_context(is_paper=self.is_paper)
            logger.log(
                SUCCESS,
                f"交易上下文初始化成功 ({'模拟盘' if self.is_paper else '实盘'})",
            )
        except Exception as e:
            logger.error(f"初始化交易上下文失败: {e}")
            raise

    def submit_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[Decimal] = None,
        order_type: OrderType = OrderType.LO,
        time_in_force: TimeInForceType = TimeInForceType.Day,
    ) -> Optional[SubmitOrderResponse]:
        """
        提交买入订单

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 买入价格（市价单可为None）
            order_type: 订单类型
            time_in_force: 订单有效期
        """
        try:
            if order_type == OrderType.MO:
                price = None

            response = self.trade_context.submit_order(
                symbol=symbol,
                order_type=order_type,
                side=OrderSide.Buy,
                submitted_quantity=Decimal(str(quantity)),
                time_in_force=time_in_force,
                submitted_price=price,
            )

            logger.log(
                SUCCESS,
                f"买入订单提交成功: {symbol}, 数量: {quantity}, 订单ID: {response.order_id}",
            )
            return response

        except Exception as e:
            logger.error(f"提交买入订单失败: {symbol}, 数量: {quantity}, 错误: {e}")
            return None

    def submit_sell_order(
        self,
        symbol: str,
        quantity: int,
        price: Optional[Decimal] = None,
        order_type: OrderType = OrderType.LO,
        time_in_force: TimeInForceType = TimeInForceType.Day,
    ) -> Optional[SubmitOrderResponse]:
        """
        提交卖出订单

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 卖出价格（市价单可为None）
            order_type: 订单类型
            time_in_force: 订单有效期
        """
        try:
            if order_type == OrderType.MO:
                price = None

            response = self.trade_context.submit_order(
                symbol=symbol,
                order_type=order_type,
                side=OrderSide.Sell,
                submitted_quantity=Decimal(str(quantity)),
                time_in_force=time_in_force,
                submitted_price=price,
            )

            logger.log(
                SUCCESS,
                f"卖出订单提交成功: {symbol}, 数量: {quantity}, 订单ID: {response.order_id}",
            )
            return response

        except Exception as e:
            logger.error(f"提交卖出订单失败: {symbol}, 数量: {quantity}, 错误: {e}")
            return None

    def execute_strategy_operations(
        self, task_id: int, operations: List[Dict]
    ) -> List[Dict]:
        """
        执行策略操作

        Args:
            task_id: 任务ID
            operations: 操作列表 [{'action': 'buy/sell', 'symbol': str, 'quantity': int, 'price': Decimal}]

        Returns:
            执行结果列表
        """
        results = []

        for operation in operations:
            try:
                action = operation.get("action")
                symbol = operation.get("symbol")
                quantity = operation.get("quantity", 0)
                price = operation.get("price")

                if not symbol or quantity <= 0:
                    continue

                result = {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "success": False,
                    "order_id": None,
                    "error": None,
                }

                # 执行买入操作
                if action == "buy":
                    response = self.submit_buy_order(
                        symbol=symbol,
                        quantity=quantity,
                        price=price,
                        order_type=OrderType.LO,
                    )

                    if response:
                        result["success"] = True
                        result["order_id"] = response.order_id

                        # 记录交易日志
                        db_manager.log_trade_operation(
                            task_id=task_id,
                            symbol=symbol,
                            operation=OperationType.BUY,
                            price=float(price),
                            quantity=quantity,
                        )
                    else:
                        result["error"] = "买入订单提交失败"

                # 执行卖出操作
                elif action == "sell":
                    response = self.submit_sell_order(
                        symbol=symbol,
                        quantity=quantity,
                        price=price,
                        order_type=OrderType.LO,
                    )

                    if response:
                        result["success"] = True
                        result["order_id"] = response.order_id

                        # 记录交易日志
                        db_manager.log_trade_operation(
                            task_id=task_id,
                            symbol=symbol,
                            operation=OperationType.SELL,
                            price=float(price),
                            quantity=quantity,
                        )
                    else:
                        result["error"] = "卖出订单提交失败"

                results.append(result)

            except Exception as e:
                logger.error(f"执行操作失败: {operation}, 错误: {e}")
                results.append(
                    {
                        "symbol": operation.get("symbol"),
                        "action": operation.get("action"),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """获取当前股票价格"""
        try:
            quotes = self.quote_context.quote([symbol])
            if quotes:
                quote = quotes[0]
                # 根据市场状态返回相应价格
                if quote.pre_market_quote and quote.pre_market_quote.last_done:
                    return quote.pre_market_quote.last_done
                elif quote.post_market_quote and quote.post_market_quote.last_done:
                    return quote.post_market_quote.last_done
                elif quote.overnight_quote and quote.overnight_quote.last_done:
                    return quote.overnight_quote.last_done
                else:
                    return quote.last_done
            return None
        except Exception as e:
            logger.error(f"获取股票价格失败: {symbol}, 错误: {e}")
            return None

    def get_account_balance(self) -> Dict:
        """获取账户余额信息"""
        try:
            balances = self.trade_context.account_balance()
            if balances:
                balance = balances[0]
                return {
                    "total_cash": float(balance.total_cash),
                    "max_finance_amount": float(balance.max_finance_amount),
                    "remaining_finance_amount": float(balance.remaining_finance_amount),
                    "net_assets": float(balance.net_assets),
                    "buy_power": float(balance.buy_power),
                    "currency": balance.currency,
                }
            return {}
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            return {}

    def get_stock_positions(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """获取股票持仓信息"""
        try:
            response = self.trade_context.stock_positions(symbols)
            positions = []

            for channel in response.channels:
                for position in channel.positions:
                    positions.append(
                        {
                            "symbol": position.symbol,
                            "symbol_name": position.symbol_name,
                            "quantity": float(position.quantity),
                            "available_quantity": float(position.available_quantity),
                            "currency": position.currency,
                            "cost_price": float(position.cost_price),
                            "market": str(position.market),
                            "account_channel": channel.account_channel,
                        }
                    )

            return positions
        except Exception as e:
            logger.error(f"获取持仓信息失败: {e}")
            return []

    def check_sufficient_funds(
        self, symbol: str, quantity: int, price: Decimal
    ) -> bool:
        """检查资金是否充足"""
        try:
            balance = self.get_account_balance()
            required_amount = float(price) * quantity

            # 简单检查可用资金是否充足
            buy_power = balance.get("buy_power", 0)
            return buy_power >= required_amount
        except Exception as e:
            logger.error(f"检查资金失败: {e}")
            return False

    def check_sufficient_shares(self, symbol: str, quantity: int) -> bool:
        """检查持仓是否充足"""
        try:
            positions = self.get_stock_positions([symbol])
            for position in positions:
                if position["symbol"] == symbol:
                    return position["available_quantity"] >= quantity
            return False
        except Exception as e:
            logger.error(f"检查持仓失败: {e}")
            return False


try:
    live_trade_manager = TradeManager(is_paper=False)
except Exception as e:
    logger.error(f"初始化实盘交易管理器失败: {e}")
    live_trade_manager = None

try:
    paper_trade_manager = TradeManager(is_paper=True)
except Exception as e:
    logger.error(f"初始化模拟盘交易管理器失败: {e}")
    paper_trade_manager = None


# 全局交易管理器实例
def get_trade_manager(is_paper: bool = False) -> TradeManager:
    """获取交易管理器实例"""
    return paper_trade_manager if is_paper else live_trade_manager
