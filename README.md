# LongPort 量化交易系统

基于长桥证券 API 的 Python 量化交易系统，支持实盘和模拟盘交易。

## 功能特性

- 🏦 **多账户支持**: 实盘和模拟盘账户切换
- 📈 **多市场支持**: 美股和港股交易
- 🤖 **策略框架**: 可扩展的策略基类，内置移动平均线策略
- ⏰ **时间管理**: 支持美股不同交易时段（盘前、盘中、盘后、夜盘）
- 📊 **任务管理**: 完整的任务生命周期管理
- 💾 **数据持久化**: MySQL 数据库存储任务和交易记录
- 🔌 **RESTful API**: FastAPI 提供的完整 API 接口
- 📝 **日志记录**: 完整的操作日志和错误追踪

## 项目结构

```
longport-trading-project/
├── .env                    # 配置文件
├── server.py              # FastAPI服务器
├── requirements.txt       # 项目依赖
└── quote/                 # 核心模块目录
    ├── __init__.py
    ├── config.py          # 配置管理
    ├── db.py             # 数据库模块
    ├── strategy.py       # 策略模块
    ├── trade.py          # 交易模块
    ├── account.py        # 账户模块
    └── task.py           # 任务管理模块
```

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env` 文件并填入您的长桥证券 API 密钥：

```bash
# 长桥证券配置
LONGPORT_QUOTE_URL=wss://openapi-quote.longportapp.cn
LONGPORT_TRADE_URL=wss://openapi-trade.longportapp.cn
LONGPORT_HTTP_URL=https://openapi.longportapp.cn

# 实盘配置
LONGPORT_LIVE_APP_KEY=your_live_app_key
LONGPORT_LIVE_APP_SECRET=your_live_app_secret
LONGPORT_LIVE_ACCESS_TOKEN=your_live_access_token

# 模拟盘配置
LONGPORT_PAPER_APP_KEY=your_paper_app_key
LONGPORT_PAPER_APP_SECRET=your_paper_app_secret
LONGPORT_PAPER_ACCESS_TOKEN=your_paper_access_token

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=Stock
```

### 3. 数据库设置

系统会自动处理数据库的创建和初始化：

1. **自动创建数据库**: 如果指定的数据库不存在，系统会自动创建
2. **自动创建表**: 系统会自动创建所需的数据库表：
   - `quote_task`: 任务信息表
   - `quote_task_log`: 操作日志表
3. **确保 MySQL 服务运行**: 请确保 MySQL 服务正在运行并且配置正确

**数据库权限要求**:

- 数据库用户需要有创建数据库的权限（CREATE 权限）
- 如果使用 root 用户，通常已有足够权限
- 如果使用普通用户，请确保用户有相应的权限

**手动创建数据库（可选）**:
如果您希望手动创建数据库，可以执行：

```sql
CREATE DATABASE Stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动服务

#### 方法一：使用启动脚本（推荐）

```bash
bash start.sh
```

#### 方法二：手动启动

```bash
# 先初始化数据库
python3 init_db.py

# 启动服务
python3 server.py
```

服务将在 `http://localhost:8000` 启动。

## 故障排除

### 数据库连接问题

如果遇到数据库连接问题，请按以下步骤排查：

1. **检查 MySQL 服务**

   ```bash
   # 检查MySQL服务状态
   sudo systemctl status mysql
   # 或者
   sudo service mysql status
   ```

2. **测试数据库连接**

   ```bash
   # 使用独立的初始化脚本测试
   python3 init_db.py
   ```

3. **检查配置**

   - 确认 `.env` 文件中的数据库配置正确
   - 确认数据库用户有足够的权限（CREATE DATABASE 权限）

4. **常见错误解决**

   **错误**: `Not an executable object`

   - 已在新版本中修复，使用了正确的 SQLAlchemy 2.0 语法

   **错误**: `Access denied for user`

   - 检查 MySQL 用户名和密码
   - 确保用户有数据库创建权限

   **错误**: `Can't connect to MySQL server`

   - 检查 MySQL 服务是否运行
   - 检查主机名和端口配置

### API 密钥问题

1. **获取长桥 API 密钥**

   - 登录长桥证券开发者平台
   - 创建应用并获取 API 密钥
   - 分别配置实盘和模拟盘密钥

2. **配置检查**
   ```bash
   # 检查.env文件是否存在且配置完整
   cat .env
   ```

## API 使用指南

### 系统状态

```bash
# 健康检查
GET /health

# 系统状态
GET /api/status
```

### 账户管理

```bash
# 获取账户余额
GET /api/account/{account_type}/balance?currency=USD

# 获取账户持仓
GET /api/account/{account_type}/positions?symbols=AAPL,TSLA

# 获取账户摘要
GET /api/account/{account_type}/summary
```

### 策略管理

```bash
# 获取可用策略
GET /api/strategies
```

### 任务管理

```bash
# 创建任务
POST /api/tasks
{
  "account": "模拟盘",
  "market": "美股",
  "symbols": ["AAPL", "TSLA"],
  "strategy": "SimpleMA",
  "trading_sessions": ["market", "postmarket"]
}

# 获取所有任务
GET /api/tasks

# 获取任务详情
GET /api/tasks/{task_id}

# 启动任务
POST /api/tasks/{task_id}/start
{
  "task_id": 1,
  "trading_sessions": ["premarket", "market", "postmarket"]
}

# 暂停任务
POST /api/tasks/{task_id}/pause

# 停止任务
POST /api/tasks/{task_id}/stop

# 删除任务
DELETE /api/tasks/{task_id}

# 获取任务日志
GET /api/tasks/{task_id}/logs
```

## 策略开发

### 创建自定义策略

继承 `BaseStrategy` 类实现您的交易策略：

```python
from quote.strategy import BaseStrategy
from typing import Dict, Tuple
from decimal import Decimal

class MyCustomStrategy(BaseStrategy):
    def __init__(self, is_paper: bool = False):
        super().__init__("MyCustom", is_paper)
        # 初始化策略参数

    def should_buy(self, symbol: str, data: Dict) -> Tuple[bool, Decimal]:
        """买入逻辑"""
        # 实现买入信号逻辑
        return False, Decimal('0')

    def should_sell(self, symbol: str, data: Dict) -> Tuple[bool, int]:
        """卖出逻辑"""
        # 实现卖出信号逻辑
        return False, 0
```

### 注册策略

在 `strategy.py` 的 `AVAILABLE_STRATEGIES` 字典中添加您的策略：

```python
AVAILABLE_STRATEGIES = {
    'SimpleMA': SimpleMAStrategy,
    'MyCustom': MyCustomStrategy,  # 添加自定义策略
}
```

## 交易时段说明

### 美股交易时段

- **盘前**: 04:00 - 09:30 ET
- **盘中**: 09:30 - 16:00 ET
- **盘后**: 16:00 - 20:00 ET
- **夜盘**: 20:00 - 04:00 ET（次日）

### 港股交易时段

- **上午**: 09:30 - 12:00 HKT
- **下午**: 13:00 - 16:00 HKT

## 更新日志

### v1.0.1 (最新)

- ✅ 修复数据库自动创建功能
- ✅ 添加独立的数据库初始化脚本
- ✅ 更新 FastAPI 到最新语法（使用 lifespan 替代 on_event）
- ✅ 改善错误处理和日志记录
- ✅ 添加详细的故障排除指南

### v1.0.0

- 🎉 初始版本发布
- 📊 完整的量化交易框架
- 🤖 策略系统和任务管理
- 🔌 RESTful API 接口

1. **API 密钥安全**: 请妥善保管您的长桥 API 密钥，不要提交到版本控制系统
2. **风险控制**: 建议先在模拟盘环境测试策略，确认无误后再使用实盘
3. **网络连接**: 确保网络连接稳定，避免因网络问题导致交易异常
4. **资金管理**: 合理设置每次交易的资金量，控制风险敞口
5. **监控日志**: 定期检查系统日志，及时发现并处理异常情况

## 技术支持

如有问题，请查看日志文件或联系技术支持。

## 免责声明

本系统仅供学习和研究使用，使用者需要自行承担投资风险。请在充分了解相关风险的情况下使用本系统进行交易。
