"""
账户模块 - 查询账户信息、持仓、历史交易等
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from longport.openapi import TradeContext, QuoteContext

from .config import TradingConfig


class AccountManager:
    """账户管理器"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger("account_manager")
        self.trade_context: Optional[TradeContext] = None
        self.quote_context: Optional[QuoteContext] = None

        # 缓存数据
        self._balance_cache = None
        self._positions_cache = []
        self._cache_timeout = 300  # 缓存5分钟
        self._last_cache_time: Optional[datetime] = None

    async def initialize(self) -> bool:
        """初始化账户管理器"""
        try:
            longport_config = self.config.get_longport_config()
            self.trade_context = TradeContext(longport_config)
            self.quote_context = QuoteContext(longport_config)
            self.logger.info("账户管理器初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"账户管理器初始化失败: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self._last_cache_time:
            return False

        return (datetime.now() - self._last_cache_time).seconds < self._cache_timeout

    async def get_account_balance(self, force_refresh: bool = False):
        """获取账户余额"""
        try:
            if not force_refresh and self._is_cache_valid() and self._balance_cache:
                return self._balance_cache

            if not self.trade_context:
                self.logger.error("交易上下文未初始化")
                return None

            # 调用longport API获取账户余额
            balance_resp = self.trade_context.account_balance(
                self.config.default_currency
            )
            self._last_cache_time = datetime.now()
            self._balance_cache = balance_resp[0]
            self.logger.info("成功获取账户余额")
            return self._balance_cache

        except Exception as e:
            self.logger.error(f"获取账户余额失败: {e}")
            return None

    def _balance_cache_to_dict(self) -> Dict[str, Any]:
        """转换余额缓存为字典"""
        if not self._balance_cache:
            return {}

        balance_data_dict = self._balance_cache.__dict__()
        cash_infos = []
        for cash_info in balance_data_dict["cash_infos"]:
            cash_infos.append(cash_info.__dict__())
        balance_data_dict["cash_infos"] = cash_infos

        return balance_data_dict

    async def get_positions(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        try:
            if not force_refresh and self._is_cache_valid() and self._positions_cache:
                return self._positions_cache

            if not self.trade_context:
                self.logger.error("交易上下文未初始化")
                return []

            # 调用longport API获取持仓
            positions_resp = self.trade_context.stock_positions()
            self._positions_cache = positions_resp.channels[0].positions
            self._last_cache_time = datetime.now()

            self.logger.info(f"成功获取 {len(self._positions_cache)} 个持仓")
            return self._positions_cache

        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return []

    def _positions_cache_to_list(self) -> List[Dict[str, Any]]:
        """转换持仓缓存为列表"""
        data = []
        for pos in self._positions_cache:
            pos_dict = pos.__dict__()
            data.append(pos_dict)
        return data

    async def get_position_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """根据股票代码获取持仓"""
        positions = await self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None

    async def get_history_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[List[str]] = None,
    ) -> List:
        """获取历史订单"""
        try:
            if not self.trade_context:
                self.logger.error("交易上下文未初始化")
                return []

            # 设置默认查询时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 调用longport API获取历史订单
            orders_data = self.trade_context.today_orders()

            # 过滤条件
            filtered_orders = []
            for order in orders_data:
                # 时间过滤
                if order.submitted_at < start_date or order.submitted_at > end_date:
                    continue

                # 股票代码过滤
                if symbol and order.symbol in symbol:
                    continue

                filtered_orders.append(order)

            self.logger.info(f"成功获取 {len(filtered_orders)} 个历史订单")
            return filtered_orders

        except Exception as e:
            self.logger.error(f"获取历史订单失败: {e}")
            return []

    async def get_today_orders(self) -> List[Dict[str, Any]]:
        """获取今日订单"""
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today, datetime.max.time())

        return await self.get_history_orders(start_time, end_time)

    async def get_cash_flow(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List:
        """获取资金流水"""
        try:
            if not self.trade_context:
                self.logger.error("交易上下文未初始化")
                return []

            # 设置默认查询时间范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 调用longport API获取资金流水
            cash_flow_data = self.trade_context.cash_flow(
                start_at=start_date,
                end_at=end_date,
            )

            self.logger.info(f"成功获取 {len(cash_flow_data)} 条资金流水")
            return cash_flow_data

        except Exception as e:
            self.logger.error(f"获取资金流水失败: {e}")
            return []

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取投资组合摘要"""
        try:
            balance = await self.get_account_balance()
            positions = await self.get_positions()

            if not balance:
                return {}

            # 计算总市值
            total_market_value = 0
            positions_latest_price = {}
            for pos in positions:
                symbol = pos.symbol
                positions_latest_price[symbol] = self.quote_context.quote([symbol])[
                    0
                ].last_done
                total_market_value += positions_latest_price[symbol] * pos.quantity

            total_cost = sum(pos.cost_price * pos.quantity for pos in positions)
            total_unrealized_pnl = total_market_value - total_cost
            total_unrealized_pnl_percent = (
                total_unrealized_pnl / total_cost * 100 if total_cost > 0 else 0
            )

            # 计算持仓数量
            long_positions = len([pos for pos in positions if pos.quantity > 0])

            # 计算资产配置
            cash_ratio = (
                balance.total_cash / balance.net_assets if balance.net_assets > 0 else 0
            )
            stock_ratio = (
                total_market_value / balance.net_assets if balance.net_assets > 0 else 0
            )

            portfolio_summary = {
                "account_info": balance,
                "total_positions": len(positions),
                "long_positions": long_positions,
                "total_market_value": total_market_value,
                "total_cost": total_cost,
                "total_unrealized_pnl": total_market_value - total_cost,
                "total_unrealized_pnl_percent": total_unrealized_pnl_percent,
                "cash_ratio": cash_ratio,
                "stock_ratio": stock_ratio,
                "positions": positions,
                "positions_latest_price": positions_latest_price,
            }

            self.logger.info("成功获取投资组合摘要")
            return portfolio_summary

        except Exception as e:
            self.logger.error(f"获取投资组合摘要失败: {e}")
            return {}

    async def refresh_all_data(self) -> None:
        """刷新所有数据"""
        try:
            await self.get_account_balance(force_refresh=True)
            await self.get_positions(force_refresh=True)
            self.logger.info("所有账户数据刷新完成")

        except Exception as e:
            self.logger.error(f"刷新账户数据失败: {e}")

    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "cache_valid": self._is_cache_valid(),
            "last_cache_time": (
                self._last_cache_time.isoformat() if self._last_cache_time else None
            ),
            "cache_timeout": self._cache_timeout,
            "balance_cached": self._balance_cache is not None,
            "positions_count": len(self._positions_cache),
        }
