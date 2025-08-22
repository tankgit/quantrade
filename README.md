# 量化交易系统

基于长桥证券API的Python量化交易系统，支持策略开发、自动交易、风险管理等功能。

## 功能特性

- 🔧 **配置管理**: 支持实盘和模拟盘环境配置
- 📈 **策略框架**: 提供策略基类，支持自定义策略开发
- 💼 **账户管理**: 查询余额、持仓、历史交易等信息
- 🤖 **自动交易**: 基于策略信号自动执行交易
- 🎯 **任务管理**: 策略任务的创建、启动、暂停、删除
- 🛡️ **风险控制**: 内置风险管理机制
- 💻 **命令行工具**: 提供便捷的CLI操作界面

## 项目结构

```
量化交易系统/
├── src/                    # 源代码目录
│   ├── __init__.py        # 包初始化
│   ├── config.py          # 配置模块
│   ├── strategy.py        # 策略模块
│   ├── trade.py           # 交易模块
│   ├── account.py         # 账户模块
│   ├── task.py            # 任务模块
│   └── cmd.py             # 命令行模块
├── main.py                # 主程序示例
├── requirements.txt       # 依赖包
└── README.md             # 说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置系统

```python
from src.config import TradingConfig

# 创建配置
config = TradingConfig(
    app_key="your_app_key",
    app_secret="your_app_secret", 
    access_token="your_access_token",
    is_sandbox=True,  # True为模拟盘，False为实盘
)
```

### 2. 查询账户信息

```python
from src.account import AccountManager

# 创建账户管理器
account_manager = AccountManager(config)
await account_manager.initialize()

# 查询账户余额
balance = await account_manager.get_account_balance()
print(f"可用现金: {balance['available_cash']}")

# 查询持仓
positions = await account_manager.get_positions()
print(f"持仓数量: {len(positions)}")
```

### 3. 创建交易策略

```python
from src.strategy import SimpleMAStrategy

# 创建简单移动平均策略
strategy = SimpleMAStrategy(
    short_period=5,    # 短期均线
    long_period=20,    # 长期均线
    symbols=['00700.HK', '00941.HK']  # 监控股票
)
```

### 4. 创建和管理任务

```python
from src.task import TaskManager, TaskConfig

# 创建任务管理器
task_manager = TaskManager(config)
await task_manager.initialize()

# 配置任务参数
task_config = TaskConfig(
    interval=10.0,     # 执行间隔10秒
    max_runs=100,      # 最多执行100次
)

# 创建策略任务
task_id = task_manager.create_strategy_task(
    name="MA策略",
    strategy=strategy,
    symbols=['00700.HK', '00941.HK'],
    config=task_config
)

# 启动任务
task_manager.start_task(task_id)

# 启动监控
task_manager.start_monitoring()
```

## 命令行工具使用

系统提供了便捷的命令行工具：

```bash
# 查看帮助
python -m src.cmd --help

# 查询账户余额
python -m src.cmd account balance

# 查询持仓信息
python -m src.cmd account positions

# 查询历史订单
python -m src.cmd account orders

# 创建策略
python -m src.cmd strategy create "我的策略" --symbols "00700.HK,00941.HK"

# 查看所有任务
python -m src.cmd task list

# 启动任务
python -m src.cmd task start TASK_000001

# 启动监控
python -m src.cmd monitor start

# 查看监控状态
python -m src.cmd monitor status
```

## 运行示例

```bash
# 运行完整示例
python main.py

# 或者直接运行简单演示
# 修改main.py中的函数调用即可
```

## 自定义策略开发

继承 `BaseStrategy` 类来开发自定义策略：

```python
from src.strategy import BaseStrategy, TradingSignal, SignalType

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1, param2):
        super().__init__("MyStrategy", {'param1': param1, 'param2': param2})
        self.param1 = param1
        self.param2 = param2
    
    def get_required_data(self):
        return ['close', 'volume', 'symbol']
    
    def calculate_signals(self, market_data):
        signals = []
        
        # 在这里实现你的策略逻辑
        symbol = market_data.get('symbol')
        close = market_data.get('close')
        
        # 示例：简单的价格突破策略
        if close > self.param1:  # 突破阻力位
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=0.8,
                price=close,
                reason="价格突破阻力位"
            )
            signals.append(signal)
        
        return signals
```

## 环境变量配置

可以通过环境变量配置系统：

```bash
export LONGPORT_APP_KEY="your_app_key"
export LONGPORT_APP_SECRET="your_app_secret"
export LONGPORT_ACCESS_TOKEN="your_access_token"
export LONGPORT_SANDBOX="true"  # true为模拟盘，false为实盘
```

然后使用：

```python
config = TradingConfig.from_env()
```

## 注意事项

1. **安全性**: 请妥善保管您的API密钥，不要在代码中硬编码
2. **风险控制**: 系统内置了基础风险控制，但请根据实际需求调整参数
3. **数据延迟**: 注意市场数据可能存在延迟
4. **测试环境**: 建议先在模拟盘环境充分测试策略
5. **监控运行**: 在实盘环境中请密切监控系统运行状态

## 常见问题

### Q: 如何获取长桥API密钥？
A: 请访问长桥开放平台官网注册并申请API权限。

### Q: 策略运行出错怎么办？
A: 查看日志文件，检查网络连接和API配置是否正确。

### Q: 如何修改风险控制参数？
A: 在配置中调整 `max_position_pct` 等参数，或修改 `RiskManager` 类。

### Q: 支持哪些市场？
A: 支持长桥证券覆盖的所有市场，包括港股、美股等。

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和交易所规定。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。