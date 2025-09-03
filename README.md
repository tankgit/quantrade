# PawQuant Trade

基于长桥证券 API 的 Python 量化交易系统，支持实盘和模拟盘交易。

## 项目结构

```
longport-trading-project/
├── .env                    # 配置文件
├── pyproject.toml          # 项目配置管理
├── init_db.py              # 数据库初始化
├── server.py              # FastAPI服务器
├── start.sh              # 启动服务入口
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

项目使用`uv`命令管理，请先安装`uv`，然后同步环境：

```bash
uv sync
```

然后前端相关的环境请进入前端目录，然后安装

```bash
cd ./frontend

npm install
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

如果使用启动脚本，运行服务时会自动处理数据库的创建和初始化：

1. **自动创建数据库**: 如果指定的数据库不存在（.env 环境变量里设置），会自动创建
2. **自动创建表**: 运行服务会自动创建所需的数据库表：
   - `quote_task`: 任务信息表
   - `quote_task_log`: 操作日志表

### 4. 启动后端服务

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

后端服务将在 `http://localhost:8000` 启动。（默认配置地址，也可以改）

访问`http://localhost:8000/redoc`查看接口文档

### 5. 启动前端应用

如果是在开发中，进入前端目录，然后

```bash
cd ./frontend

npm start
```

同时项目使用 tailwindcss 4，开发时可以实时运行监控来刷新样式文件：

```bash
#在前端目录下执行
npx @tailwindcss/cli -i src/styles/index.raw.css -o src/styles/index.css --watch
```

正式发布的话直接`npm run build`发布静态文件，然后用 nginx 部署前端文件。

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

### License

GPL
