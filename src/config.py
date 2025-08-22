"""
配置模块 - 管理基本的URL、账户信息和环境配置
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from decimal import Decimal
from longport.openapi import Config


@dataclass
class TradingConfig:
    """交易配置类"""

    # 基础URL配置
    base_url: str = "https://openapi.longportapp.cn"
    quote_url: str = "wss://openapi-quote.longportapp.cn"
    trade_url: str = "wss://openapi-trade.longportapp.cn"

    # 账户信息
    app_key: str = ""
    app_secret: str = ""
    access_token: str = ""

    # 环境配置
    is_sandbox: bool = False  # True为模拟盘，False为实盘

    # 交易配置
    default_currency: str = "USD"
    max_position_pct: float = Decimal("0.1")  # 单个股票最大仓位比例

    def __post_init__(self):
        """初始化后验证配置"""
        if not all([self.app_key, self.app_secret, self.access_token]):
            raise ValueError("缺少必要的认证信息")

    def get_longport_config(self) -> Config:
        """获取longport的Config对象"""
        return Config(
            app_key=self.app_key,
            app_secret=self.app_secret,
            access_token=self.access_token,
            http_url=self.base_url,
            quote_ws_url=self.quote_url,
            trade_ws_url=self.trade_url,
        )

    @classmethod
    def from_env(cls) -> "TradingConfig":
        """从环境变量创建配置"""
        return cls(
            app_key=os.getenv("LONGPORT_APP_KEY", ""),
            app_secret=os.getenv("LONGPORT_APP_SECRET", ""),
            access_token=os.getenv("LONGPORT_ACCESS_TOKEN", ""),
            is_sandbox=os.getenv("LONGPORT_SANDBOX", "false").lower() == "true",
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TradingConfig":
        """从字典创建配置"""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "base_url": self.base_url,
            "quote_url": self.quote_url,
            "trade_url": self.trade_url,
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "access_token": self.access_token,
            "is_sandbox": self.is_sandbox,
            "default_currency": self.default_currency,
            "max_position_pct": self.max_position_pct,
        }


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self._config: Optional[TradingConfig] = None
        self._config_file = config_file

    def load_config(self, config: Optional[TradingConfig] = None) -> TradingConfig:
        """加载配置"""
        if config:
            self._config = config
        elif not self._config:
            self._config = TradingConfig.from_env()

        return self._config

    def get_config(self) -> TradingConfig:
        """获取当前配置"""
        if not self._config:
            raise ValueError("配置未初始化，请先调用load_config")
        return self._config

    def update_config(self, **kwargs) -> None:
        """更新配置"""
        if not self._config:
            raise ValueError("配置未初始化")

        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def is_sandbox(self) -> bool:
        """是否为模拟盘"""
        return self.get_config().is_sandbox


# 全局配置管理器实例
config_manager = ConfigManager()
