from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import logging
import os

import quote
from quote.task import task_manager
from quote.account import get_account_manager
from quote.trade import get_trade_manager
from quote.strategy import list_available_strategies

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("LongPort量化交易系统启动")
    yield
    # 关闭时执行
    logger.info("正在关闭系统...")
    task_manager.shutdown()
    logger.info("系统已关闭")


app = FastAPI(title="LongPort量化交易系统", version="1.0.0", lifespan=lifespan)


# CORS 中间件配置，允许本机的前端3000端口访问
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic模型定义
class CreateTaskRequest(BaseModel):
    account: str  # "实盘" 或 "模拟盘"
    market: str  # "美股" 或 "港股"
    symbols: List[str]
    strategy: str
    trading_sessions: Optional[List[str]] = (
        None  # ["premarket", "market", "postmarket", "overnight"]
    )


class TaskResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[int] = None
    data: Optional[Dict] = None


class TaskStatusRequest(BaseModel):
    task_id: int


# 启动任务请求
class StartTaskRequest(BaseModel):
    task_id: int
    trading_sessions: Optional[List[str]] = None


@app.get("/")
async def root():
    """根路径"""
    return {"message": "LongPort量化交易系统API", "version": "1.0.0"}


# 账户相关接口
@app.get("/api/account/{account_type}/balance")
async def get_account_balance(account_type: str, currency: Optional[str] = None):
    """
    获取账户余额

    Args:
        account_type: 账户类型 (live/paper)
        currency: 货币类型 (可选)
    """
    try:
        is_paper = account_type.lower() == "paper"
        account_manager = get_account_manager(is_paper=is_paper)

        balances = account_manager.get_account_balance(currency)

        return {
            "success": True,
            "data": {
                "account_type": "PAPER" if is_paper else "LIVE",
                "balances": balances,
            },
        }

    except Exception as e:
        logger.error(f"获取账户余额失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/account/{account_type}/positions")
async def get_account_positions(account_type: str, symbols: Optional[str] = None):
    """
    获取账户持仓

    Args:
        account_type: 账户类型 (live/paper)
        symbols: 股票代码，多个用逗号分隔 (可选)
    """
    try:
        is_paper = account_type.lower() == "paper"
        account_manager = get_account_manager(is_paper=is_paper)

        symbol_list = symbols.split(",") if symbols else None
        positions = account_manager.get_stock_positions(symbol_list)

        return {
            "success": True,
            "data": {
                "account_type": "模拟盘" if is_paper else "实盘",
                "positions": positions,
            },
        }

    except Exception as e:
        logger.error(f"获取账户持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/account/{account_type}/summary")
async def get_account_summary(account_type: str):
    """
    获取账户摘要信息

    Args:
        account_type: 账户类型 (live/paper)
    """
    try:
        is_paper = account_type.lower() == "paper"
        account_manager = get_account_manager(is_paper=is_paper)

        summary = account_manager.get_account_summary()

        return {"success": True, "data": summary}

    except Exception as e:
        logger.error(f"获取账户摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quote/{account_type}/price")
async def get_stock_price(account_type: str, symbols: str):
    """
    获取股票最新价格, 可同时传入多只股票，每只股票之间用逗号分隔。
    如果是美股，则返回的价格还包含盘前和盘后以及夜盘价格。

    Args:
        account_type: 账户类型 (live/paper)
        symbols: 股票代码，多个用逗号分隔
    """
    try:
        symbol_list = [x.strip() for x in symbols.split(",")] if symbols else []
        print(symbol_list)
        is_paper = account_type.lower() == "paper"
        account_manager = get_account_manager(is_paper=is_paper)
        quote_list = account_manager.quote_context.quote(symbol_list)
        print(quote_list)
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
        return {"success": True, "data": price}

    except Exception as e:
        raise
        logger.error(f"获取股票价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 策略相关接口
@app.get("/api/strategies")
async def get_available_strategies():
    """获取可用策略列表"""
    try:
        strategies = list_available_strategies()

        return {
            "success": True,
            "data": {"strategies": strategies, "count": len(strategies)},
        }

    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 任务管理接口
@app.post("/api/tasks")
async def create_task(request: CreateTaskRequest):
    """创建新任务"""
    try:
        task_id = task_manager.create_task(
            account=request.account,
            market=request.market,
            symbols=request.symbols,
            strategy=request.strategy,
            trading_sessions=request.trading_sessions,
        )

        return TaskResponse(success=True, message="任务创建成功", task_id=task_id)

    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def list_tasks():
    """获取所有任务列表"""
    try:
        tasks = task_manager.list_all_tasks()

        return {
            "success": True,
            "data": {
                "tasks": tasks,
                "count": len(tasks),
                "running_count": task_manager.get_running_tasks_count(),
            },
        }

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """获取任务详情"""
    try:
        task_info = task_manager.get_task_info(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {"success": True, "data": task_info}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: int, request: StartTaskRequest):
    """启动任务"""
    try:
        success = task_manager.start_task(task_id, request.trading_sessions)

        if not success:
            raise HTTPException(status_code=400, detail="启动任务失败")

        return TaskResponse(success=True, message="任务启动成功", task_id=task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: int):
    """暂停任务"""
    try:
        success = task_manager.pause_task(task_id)

        if not success:
            raise HTTPException(status_code=400, detail="暂停任务失败")

        return TaskResponse(success=True, message="任务暂停成功", task_id=task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/stop")
async def stop_task(task_id: int):
    """停止任务"""
    try:
        success = task_manager.stop_task(task_id)

        if not success:
            raise HTTPException(status_code=400, detail="停止任务失败")

        return TaskResponse(success=True, message="任务停止成功", task_id=task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    try:
        success = task_manager.delete_task(task_id)

        if not success:
            raise HTTPException(status_code=400, detail="删除任务失败")

        return TaskResponse(success=True, message="任务删除成功", task_id=task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: int):
    """获取任务操作日志"""
    try:
        logs = task_manager.get_task_logs(task_id)

        return {
            "success": True,
            "data": {"task_id": task_id, "logs": logs, "count": len(logs)},
        }

    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 系统状态接口
@app.get("/api/status")
async def get_system_status():
    """获取系统状态"""
    try:
        all_tasks = task_manager.list_all_tasks()
        running_count = task_manager.get_running_tasks_count()

        return {
            "success": True,
            "data": {
                "system_status": "running",
                "total_tasks": len(all_tasks),
                "running_tasks": running_count,
                "available_strategies": list_available_strategies(),
            },
        }

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "系统运行正常"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))

    uvicorn.run(app, host=host, port=port)
