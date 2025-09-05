from longport.openapi import QuoteContext, TradeContext

from .config import paper_longport_config, live_longport_config
from .logger import base_logger, SUCCESS

logger = base_logger.getChild("Context")

try:
    _paper_quote_context = QuoteContext(paper_longport_config)
    _paper_trade_context = TradeContext(paper_longport_config)
    logger.log(SUCCESS, "模拟盘上下文初始化成功")
except:
    logger.error("初始化模拟盘上下文失败")
    _paper_quote_context = None
    _paper_trade_context = None

try:
    _live_quote_context = QuoteContext(live_longport_config)
    _live_trade_context = TradeContext(live_longport_config)
    logger.log(SUCCESS, "实盘上下文初始化成功")
except:
    logger.error("初始化实盘上下文失败")
    _live_quote_context = None
    _live_trade_context = None


def get_quote_context(is_paper=True):
    """获取行情上下文"""
    return _paper_quote_context if is_paper else _live_quote_context


def get_trade_context(is_paper=True):
    """获取交易上下文"""
    return _paper_trade_context if is_paper else _live_trade_context
