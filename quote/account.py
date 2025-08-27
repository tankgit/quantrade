import math
from platform import libc_ver
from typing import Dict, List, Optional
from longport.openapi import TradeContext, QuoteContext
from .config import longport_config
import logging

logger = logging.getLogger(__name__)


class AccountManager:
    """账户管理器"""

    def __init__(self, is_paper: bool = False):
        self.is_paper = is_paper
        self.config = longport_config.get_config(is_paper)
        self.trade_context = None
        self.quote_context = None
        self.initialize_contexts()

    def initialize_contexts(self):
        """初始化上下文"""
        try:
            self.trade_context = TradeContext(self.config)
            self.quote_context = QuoteContext(self.config)
            logger.info(
                f"账户上下文初始化成功 ({'模拟盘' if self.is_paper else '实盘'})"
            )
        except Exception as e:
            logger.error(f"初始化账户上下文失败: {e}")
            raise

    def get_account_balance(self, currency: Optional[str] = None) -> List[Dict]:
        """
        获取账户余额信息

        Args:
            currency: 货币类型，None表示获取所有货币

        Returns:
            账户余额信息列表
        """
        try:
            balances = self.trade_context.account_balance(currency)
            result = []

            for balance in balances:
                balance_info = {
                    "total_cash": float(balance.total_cash),
                    "max_finance_amount": float(balance.max_finance_amount),
                    "remaining_finance_amount": float(balance.remaining_finance_amount),
                    "risk_level": balance.risk_level,
                    "margin_call": float(balance.margin_call),
                    "currency": balance.currency,
                    "net_assets": float(balance.net_assets),
                    "init_margin": float(balance.init_margin),
                    "maintenance_margin": float(balance.maintenance_margin),
                    "buy_power": float(balance.buy_power),
                }

                # 添加现金详情
                if balance.cash_infos:
                    balance_info["cash_infos"] = [
                        {
                            "withdraw_cash": float(cash_info.withdraw_cash),
                            "available_cash": float(cash_info.available_cash),
                            "frozen_cash": float(cash_info.frozen_cash),
                            "settling_cash": float(cash_info.settling_cash),
                            "currency": cash_info.currency,
                        }
                        for cash_info in balance.cash_infos
                    ]

                result.append(balance_info)

            return result

        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            return []

    def get_stock_positions(self, symbols: Optional[List[str]] = None) -> Dict:
        """
        获取股票持仓信息

        Args:
            symbols: 股票代码列表，None表示获取所有持仓

        Returns:
            持仓信息字典
        """
        try:
            response = self.trade_context.stock_positions(symbols)
            result = {"channels": []}

            for channel in response.channels:
                channel_info = {
                    "account_channel": channel.account_channel,
                    "positions": [],
                }

                for position in channel.positions:
                    position_info = {
                        "symbol": position.symbol,
                        "symbol_name": position.symbol_name,
                        "quantity": float(position.quantity),
                        "available_quantity": float(position.available_quantity),
                        "currency": position.currency,
                        "cost_price": float(position.cost_price),
                        "market": str(position.market),
                    }

                    # 添加初始持仓数量（如果有）
                    if position.init_quantity is not None:
                        position_info["init_quantity"] = float(position.init_quantity)

                    channel_info["positions"].append(position_info)

                result["channels"].append(channel_info)

            return result

        except Exception as e:
            logger.error(f"获取股票持仓失败: {e}")
            return {"channels": []}

    def get_account_summary(self) -> Dict:
        """
        获取账户摘要信息

        Returns:
            包含余额和持仓的账户摘要
        """
        try:
            balance_USD = self.trade_context.account_balance("USD")[0]
            balance_HKD = self.trade_context.account_balance("HKD")[0]
            cash_infos = balance_USD.cash_infos
            usd_cash = balance_USD.total_cash
            hkd_cash = balance_HKD.total_cash
            net_assets_usd = balance_USD.net_assets
            net_assets_hkd = balance_HKD.net_assets
            # 计算汇率，这里直接依照长桥的不同货币单位数据算出汇率
            ratio = float(hkd_cash / usd_cash) if usd_cash > 0 else None

            summary = {
                "account_type": "模拟盘" if self.is_paper else "实盘",
                "assets": {
                    info.currency[:-1]: {
                        "cash": float(info.available_cash),
                        "stock": 0.0,
                    }
                    for info in cash_infos
                },
                "balances": {
                    "USD": {
                        "total_cash": float(balance_USD.total_cash),
                        "net_assets": float(balance_USD.net_assets),
                    },
                    "HKD": {
                        "total_cash": float(balance_HKD.total_cash),
                        "net_assets": float(balance_HKD.net_assets),
                    },
                },
                "positions": self.get_stock_positions(),
                "total_positions": 0,
                "stock_market_value": {"US": 0.0, "HK": 0.0},
                "asset_ratio": {},
            }

            # 计算总持仓数量和市值
            for channel in summary["positions"]["channels"]:
                for position in channel["positions"]:
                    summary["total_positions"] += 1
                    # 这里可以进一步计算市值，需要获取当前价格
                    symbol = position["symbol"]
                    currency = position["currency"]
                    # TODO: 美股要根据交易时段获取相应价位
                    price = self.quote_context.quote([symbol])[0].last_done
                    market_value = float(position["quantity"]) * float(price)
                    summary["assets"][currency[:-1]]["stock"] += market_value

            stock_us = summary["assets"]["US"]["stock"]
            stock_hk = summary["assets"]["HK"]["stock"]
            total_stock_usd = stock_us + (stock_hk / ratio if ratio else 0.0)
            total_stock_hkd = stock_hk + (stock_us * ratio if ratio else 0.0)
            summary["stock_market_value"]["US"] = total_stock_usd
            summary["stock_market_value"]["HK"] = total_stock_hkd
            summary["asset_ratio"] = {
                "US": stock_us / float(net_assets_usd),
                "HK": stock_hk / float(net_assets_hkd),
            }
            summary["stock_ratio"] = sum(summary["asset_ratio"].values())
            summary["asset_ratio"]["cash"] = 1 - summary["stock_ratio"]

            new_position = {"US": [], "HK": []}
            for position in summary["positions"]["channels"][0]["positions"]:
                market = position["market"].split(".")[-1]
                new_position[market].append(position)

            summary["positions"] = new_position

            return summary

        except Exception as e:
            logger.error(f"获取账户摘要失败: {e}")
            return {}

    def get_position_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        获取指定股票的持仓信息

        Args:
            symbol: 股票代码

        Returns:
            持仓信息字典，如果没有持仓返回None
        """
        try:
            positions = self.get_stock_positions([symbol])

            for channel in positions["channels"]:
                for position in channel["positions"]:
                    if position["symbol"] == symbol:
                        return position

            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 持仓失败: {e}")
            return None

    def get_available_buy_power(self, currency: str = "USD") -> float:
        """
        获取指定货币的可用购买力

        Args:
            currency: 货币类型

        Returns:
            可用购买力
        """
        try:
            balances = self.get_account_balance(currency)

            for balance in balances:
                if balance["currency"] == currency:
                    return balance["buy_power"]

            return 0.0

        except Exception as e:
            logger.error(f"获取购买力失败: {e}")
            return 0.0

    def get_total_cash(self, currency: str = "USD") -> float:
        """
        获取指定货币的总现金

        Args:
            currency: 货币类型

        Returns:
            总现金
        """
        try:
            balances = self.get_account_balance(currency)

            for balance in balances:
                if balance["currency"] == currency:
                    return balance["total_cash"]

            return 0.0

        except Exception as e:
            logger.error(f"获取总现金失败: {e}")
            return 0.0

    def check_trading_permission(self, symbol: str) -> bool:
        """
        检查是否有交易权限

        Args:
            symbol: 股票代码

        Returns:
            是否有交易权限
        """
        try:
            # 简单检查：尝试获取股票信息
            if self.quote_context:
                quotes = self.quote_context.quote([symbol])
                return len(quotes) > 0
            return False

        except Exception as e:
            logger.error(f"检查交易权限失败: {symbol}, 错误: {e}")
            return False


try:
    live_account_manager = AccountManager(is_paper=False)
except Exception as e:
    logger.error(f"实盘账户管理器初始化失败: {e}")
    live_account_manager = None

try:
    paper_account_manager = AccountManager(is_paper=True)
except Exception as e:
    logger.error(f"模拟盘账户管理器初始化失败: {e}")
    paper_account_manager = None


# 全局账户管理器实例
def get_account_manager(is_paper: bool = False) -> AccountManager:
    """获取账户管理器实例"""
    return paper_account_manager if is_paper else live_account_manager
