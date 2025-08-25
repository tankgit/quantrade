#!/bin/bash

# LongPort量化交易系统启动脚本

echo "==================================="
echo "LongPort 量化交易系统"
echo "==================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 检查是否存在.env文件
if [ ! -f .env ]; then
    echo "警告: 未找到 .env 配置文件"
    echo "请先创建 .env 文件并配置您的API密钥"
    exit 1
fi

# 使用专门的初始化脚本
echo "初始化数据库..."
python3 init_db.py

if [ $? -ne 0 ]; then
    echo "数据库初始化失败，请检查配置"
    echo "您可以单独运行 'python3 init_db.py' 来调试数据库问题"
    exit 1
fi

# 启动服务
echo "==================================="
echo "启动 FastAPI 服务器..."

python3 server.py