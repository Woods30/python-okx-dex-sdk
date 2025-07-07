# OKX DEX SDK (Python)

[![PyPI version](https://badge.fury.io/py/okx-dex-sdk.svg)](https://badge.fury.io/py/okx-dex-sdk)

一个用于与 OKX DEX 在多个链上（EVM, Solana, Sui）进行交互的 Python SDK。

此项目旨在提供一个与官方 [TypeScript SDK](https://github.com/okx/okx-dex-sdk) 功能对等的 Python 实现。

## 特性

*   在 Solana, EVM, Sui 链上执行代币兑换
*   获取实时报价和流动性信息
*   完整的异步支持
*   类型提示和 Pydantic 模型

## 安装

本项目使用 `uv` 进行包管理。

```bash
pip install okx-dex-sdk
```

## 配置

首先，在您的项目中设置环境变量，或者直接在代码中配置。创建一个 `.env` 文件是推荐的做法：

```
# OKX API 凭证
OKX_API_KEY="your_api_key"
OKX_SECRET_KEY="your_secret_key"
OKX_API_PASSPHRASE="your_passphrase"
OKX_PROJECT_ID="your_project_id"

# Solana 配置
SOLANA_RPC_URL="your_solana_rpc_url"
SOLANA_PRIVATE_KEY="your_solana_private_key_in_base58"

# EVM 配置
EVM_RPC_URL="your_evm_rpc_url"
EVM_PRIVATE_KEY="your_evm_private_key"
```

## 使用方法

### 初始化客户端

```python
import os
import asyncio
from okx_dex_sdk.client import OkxDexClient, OkxDexConfig

# 从环境变量或直接提供配置
config = OkxDexConfig(
    api_key=os.getenv("OKX_API_KEY"),
    secret_key=os.getenv("OKX_SECRET_KEY"),
    passphrase=os.getenv("OKX_API_PASSPHRASE"),
    project_id=os.getenv("OKX_PROJECT_ID"),
    solana_config={
        "rpc_url": os.getenv("SOLANA_RPC_URL"),
        "private_key": os.getenv("SOLANA_PRIVATE_KEY"),
    },
    evm_config={
        "rpc_url": os.getenv("EVM_RPC_URL"),
        "private_key": os.getenv("EVM_PRIVATE_KEY"),
    }
)

client = OkxDexClient(config)
```

### 使用示例

我们提供了多个示例来演示如何在不同链上进行操作。请查看 `examples/` 目录获取完整、可运行的代码。

*   **EVM 链**: `examples/evm_swap.py`
*   **Solana 链**: `examples/solana_swap.py`

#### 快速开始

1.  **克隆项目**:
    ```bash
    git clone https://github.com/your-repo/python-okx-dex-sdk.git
    cd python-okx-dex-sdk
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量**:
    *   复制 `.env.example` 文件为 `.env`。
    *   在 `.env` 文件中填入你的 OKX API 凭证和私钥等信息。

4.  **运行示例**:
    *   修改示例文件 (例如 `examples/solana_swap.py`)，填入你的钱包地址。
    *   执行脚本:
        ```bash
        python examples/solana_swap.py
        ```

## 法律声明

使用此 SDK，即表示您同意：OKX 及其关联方对任何直接、间接、偶然、特殊、后果性或惩戒性损害不承担任何责任，如法律免责声明中所述。
