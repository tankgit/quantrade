from typing import Optional
from sqlalchemy import (
    JSON,
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import OperationalError, ProgrammingError
from datetime import datetime
import json
import pymysql
from enum import Enum as PyEnum
from .config import db_config
from .logger import base_logger, SUCCESS

logger = base_logger.getChild("Database")

Base = declarative_base()


class AccountType(PyEnum):
    LIVE = "实盘"
    PAPER = "模拟盘"


class MarketType(PyEnum):
    US = "美股"
    HK = "港股"


class TaskStatus(PyEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"


class OperationType(PyEnum):
    BUY = "buy"
    SELL = "sell"


class QuoteTask(Base):
    __tablename__ = "quote_task"

    task_id = Column(Integer, primary_key=True, autoincrement=True)
    account = Column(Enum(AccountType), nullable=False)
    market = Column(Enum(MarketType), nullable=False)
    symbols = Column(JSON, default="[]")  # JSON字符串格式存储股票代码列表
    strategy = Column(String(100), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.STOPPED)
    run_data = Column(JSON, default="{}")
    created_at = Column(DateTime, default=func.now())

    # 关联日志记录
    logs = relationship("QuoteTaskLog", back_populates="task")


class QuoteTaskLog(Base):
    __tablename__ = "quote_task_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("quote_task.task_id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    op = Column(Enum(OperationType), nullable=False)
    price = Column(Float, nullable=False)
    qty = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # 关联任务
    task = relationship("QuoteTask", back_populates="logs")


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.initialize_database()

    def create_database_if_not_exists(self):
        """如果数据库不存在则创建"""
        try:
            # 使用不指定数据库的连接URL来创建数据库
            base_url = f"mysql+pymysql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/"
            temp_engine = create_engine(base_url, echo=False)

            # 检查数据库是否存在，如果不存在则创建
            with temp_engine.connect() as connection:
                # 使用text()包装SQL语句
                result = connection.execute(
                    text(f"SHOW DATABASES LIKE '{db_config.database}'")
                )
                row = result.fetchone()

                if row is None:
                    logger.info(f"数据库 {db_config.database} 不存在，正在创建...")
                    # 执行创建数据库的SQL
                    connection.execute(
                        text(
                            f"CREATE DATABASE `{db_config.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        )
                    )
                    # SQLAlchemy 2.0+ 需要显式提交
                    connection.commit()
                    logger.log(SUCCESS, f"数据库 {db_config.database} 创建成功")
                else:
                    logger.info(f"数据库 {db_config.database} 已存在，跳过创建")

            temp_engine.dispose()

        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            # 如果创建失败，尝试检查是否是权限问题
            logger.info("尝试检查数据库连接...")
            try:
                # 尝试直接连接到指定数据库
                test_engine = create_engine(db_config.get_connection_url(), echo=False)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("数据库已存在且可连接")
                test_engine.dispose()
            except Exception as e2:
                logger.error(f"数据库连接测试也失败: {e2}")
                raise e

    def initialize_database(self):
        """初始化数据库连接"""
        try:
            # 首先确保数据库存在
            self.create_database_if_not_exists()

            # 创建到具体数据库的连接
            self.engine = create_engine(
                db_config.get_connection_url(),
                echo=False,  # 改为False减少日志输出
                pool_pre_ping=True,  # 连接池预检查
                pool_recycle=3600,  # 1小时回收连接
            )

            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            # 创建表
            self.create_tables()

            logger.log(SUCCESS, "数据库初始化成功")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def create_tables(self):
        """创建数据库表"""
        try:
            # 检查是否能连接到数据库
            with self.engine.connect() as connection:
                logger.log(SUCCESS, "数据库连接成功，开始创建表...")

            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            logger.log(SUCCESS, "数据库表创建成功")

        except (OperationalError, ProgrammingError) as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            raise

    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.log(SUCCESS, "数据库连接测试成功")
                return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def get_session(self):
        """获取数据库会话"""
        if not self.SessionLocal:
            raise Exception("数据库未初始化")
        return self.SessionLocal()

    def ensure_connection(self):
        """确保数据库连接可用"""
        if not self.test_connection():
            logger.warning("数据库连接失效，重新初始化...")
            self.initialize_database()

    def create_task(
        self, account: AccountType, market: MarketType, symbols: list, strategy: str
    ):
        """创建新任务"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            task = QuoteTask(
                account=account,
                market=market,
                symbols=symbols,
                strategy=strategy,
                status=TaskStatus.STOPPED,
                run_data={},
            )
            session.add(task)
            session.commit()
            task_id = task.task_id
            logger.log(SUCCESS, f"任务创建成功: ID={task_id}")
            return task_id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"创建任务失败: {e}")
            raise
        finally:
            if session:
                session.close()

    def get_task(self, task_id: int) -> Optional[QuoteTask]:
        """获取任务信息"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            return session.query(QuoteTask).filter(QuoteTask.task_id == task_id).first()
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_all_tasks(self):
        """获取所有任务"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            return session.query(QuoteTask).all()
        except Exception as e:
            logger.error(f"获取所有任务失败: {e}")
            return []
        finally:
            if session:
                session.close()

    def update_task_status(self, task_id: int, status: TaskStatus):
        """更新任务状态"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            task = session.query(QuoteTask).filter(QuoteTask.task_id == task_id).first()
            if task:
                task.status = status
                session.commit()
                logger.log(
                    SUCCESS, f"任务状态更新成功: ID={task_id}, 状态={status.value}"
                )
                return True
            else:
                logger.warning(f"任务不存在: ID={task_id}")
                return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"更新任务状态失败: {e}")
            return False
        finally:
            if session:
                session.close()

    def update_task_data(self, task_id: int, run_data: dict):
        """更新任务数据"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            task = session.query(QuoteTask).filter(QuoteTask.task_id == task_id).first()
            if task:
                task.run_data = run_data
                session.commit()
                logger.log(SUCCESS, f"任务数据更新成功: ID={task_id}")
                return True
            else:
                logger.warning(f"任务不存在: ID={task_id}")
                return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"更新任务数据失败: {e}")
            return False
        finally:
            if session:
                session.close()

    def delete_task(self, task_id: int):
        """删除任务"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            # 先删除相关日志
            session.query(QuoteTaskLog).filter(QuoteTaskLog.task_id == task_id).delete()
            # 再删除任务
            task = session.query(QuoteTask).filter(QuoteTask.task_id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                logger.log(SUCCESS, f"任务删除成功: ID={task_id}")
                return True
            else:
                logger.warning(f"任务不存在: ID={task_id}")
                return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"删除任务失败: {e}")
            return False
        finally:
            if session:
                session.close()

    def log_trade_operation(
        self,
        task_id: int,
        symbol: str,
        operation: OperationType,
        price: float,
        quantity: float,
    ):
        """记录交易操作日志"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            log = QuoteTaskLog(
                task_id=task_id, symbol=symbol, op=operation, price=price, qty=quantity
            )
            session.add(log)
            session.commit()
            log_id = log.log_id
            logger.log(SUCCESS, f"交易日志记录成功: ID={log_id}")
            return log_id
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"记录交易日志失败: {e}")
            return None
        finally:
            if session:
                session.close()

    def get_task_logs(self, task_id: int):
        """获取任务的所有操作日志"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            return (
                session.query(QuoteTaskLog)
                .filter(QuoteTaskLog.task_id == task_id)
                .order_by(QuoteTaskLog.created_at.asc())
                .all()
            )
        except Exception as e:
            logger.error(f"获取任务日志失败: {e}")
            return []
        finally:
            if session:
                session.close()

    def get_task_run_data(self, task_id: int):
        """获取任务的所有运行数据"""
        session = None
        try:
            self.ensure_connection()
            session = self.get_session()
            # 获取其中的run_data字段
            return (
                session.query(QuoteTask)
                .filter(QuoteTask.task_id == task_id)
                .first()
                .run_data
            )
        except Exception as e:
            logger.error(f"获取任务运行数据失败: {e}")
            return None
        finally:
            if session:
                session.close()


# 全局数据库管理器实例
try:
    db_manager = DatabaseManager()
    logger.log(SUCCESS, "数据库管理器初始化成功")
except Exception as e:
    logger.error(f"数据库管理器初始化失败: {e}")
    db_manager = None
