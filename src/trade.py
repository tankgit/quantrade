"""
交易模块 - 处理实际的交易操作
"""

import logging
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from longport.openapi import (
    TradeContext,
    Order,
    OrderSide,
    OrderType,
    TimeInForceType,
    OrderStatus,
)

from .config import TradingConfig
from .strategy import TradingSignal, SignalType


class TradeStatus(Enum):
    """交易状态"""

    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass
class TradeOrder:
    """交易订单"""

    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    commission: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error_msg: Optional[str] = None


class RiskManager:
    """风控管理器"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger("risk_manager")

        # 风控参数
        self.max_single_trade_amount = 100000  # 单笔交易最大金额
        self.max_daily_trades = 50  # 每日最大交易次数
        self.max_position_pct = config.max_position_pct  # 最大持仓比例

        # 风控统计
        self.daily_trades = 0
        self.total_exposure = 0.0

    def check_trade_risk(
        self,
        signal: TradingSignal,
        account_value: float,
        current_positions: Dict[str, int],
    ) -> bool:
        """检查交易风险"""
        try:
            # 检查每日交易次数
            if self.daily_trades >= self.max_daily_trades:
                self.logger.warning(f"已达到每日最大交易次数: {self.max_daily_trades}")
                return False

            # 检查单笔交易金额
            if signal.price and signal.quantity:
                trade_amount = signal.price * signal.quantity
                if trade_amount > self.max_single_trade_amount:
                    self.logger.warning(f"单笔交易金额超限: {trade_amount}")
                    return False

            # 检查持仓比例
            if (
                signal.signal_type == SignalType.BUY
                and signal.price
                and signal.quantity
            ):
                position_value = signal.price * signal.quantity
                position_pct = position_value / account_value
                if position_pct > self.max_position_pct:
                    self.logger.warning(f"持仓比例超限: {position_pct:.2%}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"风控检查失败: {e}")
            return False

    def update_daily_trades(self) -> None:
        """更新每日交易次数"""
        self.daily_trades += 1

    def reset_daily_stats(self) -> None:
        """重置每日统计"""
        self.daily_trades = 0


class TradeEngine:
    """交易引擎"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger("trade_engine")
        self.trade_context: Optional[TradeContext] = None
        self.risk_manager = RiskManager(config)

        # 订单管理
        self._orders: Dict[str, TradeOrder] = {}
        self._order_counter = 0

    async def initialize(self) -> bool:
        """初始化交易引擎"""
        try:
            longport_config = self.config.get_longport_config()
            self.trade_context = TradeContext(longport_config)
            self.logger.info("交易引擎初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"交易引擎初始化失败: {e}")
            return False

    def _generate_order_id(self) -> str:
        """生成订单ID"""
        self._order_counter += 1
        return f"ORDER_{self._order_counter:06d}"

    def _signal_to_order_side(self, signal_type: SignalType) -> Optional[OrderSide]:
        """信号转换为订单方向"""
        if signal_type == SignalType.BUY:
            return OrderSide.Buy
        elif signal_type == SignalType.SELL:
            return OrderSide.Sell
        return None

    async def execute_signal(
        self,
        signal: TradingSignal,
        account_value: float,
        current_positions: Dict[str, int],
    ) -> Optional[TradeOrder]:
        """执行交易信号"""
        try:
            if not self.trade_context:
                self.logger.error("交易上下文未初始化")
                return None

            # 风控检查
            if not self.risk_manager.check_trade_risk(
                signal, account_value, current_positions
            ):
                self.logger.warning(f"信号 {signal.symbol} 风控检查未通过")
                return None

            # 转换信号为订单
            order_side = self._signal_to_order_side(signal.signal_type)
            if not order_side:
                self.logger.error(f"不支持的信号类型: {signal.signal_type}")
                return None

            # 计算交易数量（如果信号中没有指定）
            quantity = signal.quantity
            if not quantity:
                quantity = self._calculate_quantity(signal, account_value)

            if quantity <= 0:
                self.logger.warning(f"计算得到的交易数量无效: {quantity}")
                return None

            # 创建订单
            order_id = self._generate_order_id()
            trade_order = TradeOrder(
                order_id=order_id,
                symbol=signal.symbol,
                side=order_side,
                order_type=OrderType.LO,  # 限价单
                quantity=quantity,
                price=signal.price,
                status=TradeStatus.PENDING,
            )

            # 提交订单
            success = await self._submit_order(trade_order)
            if success:
                self._orders[order_id] = trade_order
                self.risk_manager.update_daily_trades()
                self.logger.info(f"订单提交成功: {order_id}")
                return trade_order
            else:
                raise
                self.logger.error(f"订单提交失败: {order_id}")
                return None

        except Exception as e:
            self.logger.error(f"执行交易信号失败: {e}")
            return None

    def _calculate_quantity(self, signal: TradingSignal, account_value: float) -> int:
        """计算交易数量"""
        if not signal.price:
            return 0

        # 基于信号强度和最大持仓比例计算
        position_value = account_value * self.config.max_position_pct * signal.strength
        quantity = int(position_value / signal.price)

        quantity = math.ceil(quantity / 500) * 500

        # 确保最小交易单位
        return max(quantity, 500)  # 最小100股

    async def _submit_order(self, trade_order: TradeOrder) -> bool:
        """提交订单到交易所"""
        try:
            if not self.trade_context:
                return False

            # 构建longport订单
            longport_order = dict(
                symbol=trade_order.symbol,
                order_type=trade_order.order_type,
                side=trade_order.side,
                submitted_quantity=trade_order.quantity,
                time_in_force=TimeInForceType.Day,
                submitted_price=trade_order.price,
            )
            self.logger.info(f"订单详情: {longport_order}")

            self.trade_context.submit_order(**longport_order)

            # 模拟订单提交成功
            trade_order.status = TradeStatus.SUBMITTED
            return True

        except Exception as e:
            trade_order.status = TradeStatus.FAILED
            trade_order.error_msg = str(e)
            self.logger.error(f"提交订单失败: {e}")
            return False

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            order = self._orders.get(order_id)
            if not order:
                self.logger.warning(f"订单不存在: {order_id}")
                return False

            if order.status not in [TradeStatus.SUBMITTED, TradeStatus.PARTIAL_FILLED]:
                self.logger.warning(f"订单状态不允许取消: {order.status}")
                return False

            # 调用API取消订单（这里是模拟）
            # await self.trade_context.cancel_order(order_id)

            order.status = TradeStatus.CANCELLED
            self.logger.info(f"订单已取消: {order_id}")
            return True

        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
            return False

    async def query_order_status(self, order_id: str) -> Optional[TradeOrder]:
        """查询订单状态"""
        try:
            order = self._orders.get(order_id)
            if not order:
                return None

            # 这里应该调用真实API查询订单状态
            # status = await self.trade_context.query_order(order_id)

            return order

        except Exception as e:
            self.logger.error(f"查询订单状态失败: {e}")
            return None

    def get_all_orders(self) -> Dict[str, TradeOrder]:
        """获取所有订单"""
        return self._orders.copy()

    def get_pending_orders(self) -> Dict[str, TradeOrder]:
        """获取待处理订单"""
        return {
            order_id: order
            for order_id, order in self._orders.items()
            if order.status
            in [TradeStatus.PENDING, TradeStatus.SUBMITTED, TradeStatus.PARTIAL_FILLED]
        }

    def get_filled_orders(self) -> Dict[str, TradeOrder]:
        """获取已成交订单"""
        return {
            order_id: order
            for order_id, order in self._orders.items()
            if order.status == TradeStatus.FILLED
        }

    async def batch_execute_signals(
        self,
        signals: List[TradingSignal],
        account_value: float,
        current_positions: Dict[str, int],
    ) -> List[TradeOrder]:
        """批量执行交易信号"""
        executed_orders = []

        for signal in signals:
            order = await self.execute_signal(signal, account_value, current_positions)
            if order:
                executed_orders.append(order)

        self.logger.info(f"批量执行完成，成功执行 {len(executed_orders)} 个订单")
        return executed_orders

    def get_trading_stats(self) -> Dict[str, Any]:
        """获取交易统计"""
        total_orders = len(self._orders)
        filled_orders = len(self.get_filled_orders())
        pending_orders = len(self.get_pending_orders())

        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "pending_orders": pending_orders,
            "daily_trades": self.risk_manager.daily_trades,
            "success_rate": filled_orders / total_orders if total_orders > 0 else 0,
        }
