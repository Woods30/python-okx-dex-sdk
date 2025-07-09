# OKX DEX SDK (Python)

[![PyPI version](https://badge.fury.io/py/okx-dex-sdk.svg)](https://badge.fury.io/py/okx-dex-sdk)

一个用于与 OKX DEX 在多个链上（EVM, Solana, Sui）进行交互的 Python SDK。

此项目旨在提供一个与官方 [TypeScript SDK](https://github.com/okx/okx-dex-sdk) 功能对等的 Python 实现。

## ✨ 特性

*   在 Solana, EVM, Sui (即将支持) 链上执行代币兑换
*   **新功能**: 可按钱包余额的百分比执行兑换
*   获取实时报价和流动性信息
*   完整的异步支持
*   基于 Pydantic 的配置管理和数据模型
*   全面的类型提示

## 📦 安装

### 从 PyPI 安装 (推荐)

```bash
pip install okx-dex-sdk
```

### 从 GitHub 安装

你也可以直接从 GitHub 安装最新的开发版本：

```bash
pip install git+https://github.com/Woods30/python-okx-dex-sdk.git
```
**注意**: 从 GitHub 安装会获取 `main` 分支的最新代码，这可能包含尚未在 PyPI 上正式发布的功能或改动。

## ⚙️ 配置

SDK 使用 `pydantic-settings` 在启动时自动从 `.env` 文件加载配置。

1.  在项目根目录创建一个 `.env` 文件。
2.  根据需要填入以下变量：

```dotenv
# OKX API 凭证 (必须)
OKX_API_KEY="your_api_key"
OKX_SECRET_KEY="your_secret_key"
OKX_API_PASSPHRASE="your_passphrase"

# OKX 项目 ID (可选)
# OKX_PROJECT_ID="your_project_id"

# 代理 (可选)
# HTTP_PROXY="http://127.0.0.1:7890"

# --- 链配置 ---
# 使用 CHAINS__<chain_id>__<setting> 的格式为每条链进行配置
# chain_id 可以在 okx_dex_sdk.constants.ChainId 中找到
# 例如: solana, bsc, eth, polygon, base ...

# Solana 配置示例
CHAINS__solana__RPC_URL="your_solana_rpc_url"
CHAINS__solana__PRIVATE_KEY="your_solana_private_key_in_base58"

# BSC (EVM) 配置示例
CHAINS__bsc__RPC_URL="your_bsc_rpc_url"
CHAINS__bsc__PRIVATE_KEY="your_evm_compatible_private_key"

# Base (EVM) 配置示例
CHAINS__base__RPC_URL="your_base_rpc_url"
CHAINS__base__PRIVATE_KEY="your_evm_compatible_private_key"
```

## 🚀 使用方法

### 初始化客户端

配置会在导入时自动加载。你只需要导入 `settings` 和 `OkxDexClient` 即可。

```python
from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings

# `settings` 对象包含了从 .env 文件加载的所有配置
client = OkxDexClient(settings)
```

### 执行兑换

下面是一个在 BSC 链上将 `USDC` 兑换为 `BNB` 的例子。

```python
import asyncio
from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId, NATIVE_TOKEN_ADDRESS
from okx_dex_sdk.utils import get_wallet_address

async def swap_example():
    client = OkxDexClient(settings)

    chain_id = ChainId.BSC
    private_key = settings.chains[chain_id].private_key
    wallet_address = get_wallet_address(private_key, chain_id)

    # 将 1 USDC 兑换为 BNB
    from_token = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d" # BSC-USD
    to_token = NATIVE_TOKEN_ADDRESS[chain_id] # BNB on BSC
    amount = "1" # 兑换 1 USDC

    swap_result = await client.execute_swap(
        chain_id=chain_id,
        private_key=private_key,
        from_token_address=from_token,
        to_token_address=to_token,
        amount=amount,
        slippage="0.01", # 1%
        user_wallet_address=wallet_address,
    )
    print(f"交易成功! Tx Hash: {swap_result.tx_hash}")

asyncio.run(swap_example())
```

### 按余额百分比兑换

你还可以方便地按照代币余额的百分比进行兑换。

```python
# ... (imports and client initialization)

# 将钱包中 50% 的 USDC 兑换为 BNB
percent_to_swap = "0.5" # 50%

swap_result = await client.execute_swap_via_balance_percent(
    chain_id=chain_id,
    private_key=private_key,
    from_token_address=from_token,
    to_token_address=to_token,
    balance_percent=percent_to_swap,
    slippage="0.01",
    user_wallet_address=wallet_address,
)
print(f"交易成功! Tx Hash: {swap_result.tx_hash}")
```

## 📚 使用示例

我们提供了多个示例来演示如何在不同链上进行操作。请查看 `examples/` 目录获取完整、可运行的代码。

*   **EVM 链**:
    *   `examples/evm_swap.py`: 按固定数量兑换。
    *   `examples/evm_swap_with_balance_percent.py`: 按余额百分比兑换。
*   **Solana 链**:
    *   `examples/solana_swap.py`: 按固定数量兑换。
    *   `examples/solana_swap_with_balance_percent.py`: 按余额百分比兑换。
*   **其他工具**:
    *   `examples/get_tokens.py`: 获取支持的代币列表。
    *   `examples/get_token_balance.py`: 获取指定代币的余额。

## 快速开始 (开发者)

1.  **克隆项目**:
    ```bash
    git clone https://github.com/Woods30/python-okx-dex-sdk.git
    cd python-okx-dex-sdk
    ```

2.  **安装依赖 (推荐使用虚拟环境)**:
    ```bash
    # 安装 uv (如果尚未安装)
    # pip install uv
    # uv venv
    # source .venv/bin/activate

    # 安装项目为可编辑模式
    pip install -e .
    ```

3.  **配置环境变量**:
    *   复制 `env.example` 文件为 `.env`。
    *   在 `.env` 文件中填入你的 API 凭证和链配置信息。

4.  **运行示例**:
    *   查看并运行 `examples/` 目录下的示例脚本，例如:
        ```bash
        python examples/evm_swap.py
        ```

## 🔗 与现有项目集成

当您的主项目也使用了名为 `settings` 的配置对象时，为了避免命名冲突，我们推荐以下几种方式来集成 SDK：

### 方法 1: 使用 `import as` 重命名 (推荐)

在导入时给 SDK 的 `settings` 对象指定一个别名，这是最简单直接的方法。

```python
# 1. 导入您项目的 settings
from your_app_config import settings as project_settings

# 2. 导入 SDK 的 settings 并重命名
from okx_dex_sdk.config import settings as okx_settings
from okx_dex_sdk.client import OkxDexClient

# 3. 使用各自的配置
print(f"我的项目配置: {project_settings.SOME_VALUE}")
client = OkxDexClient(okx_settings)
```

### 方法 2: 手动创建配置实例

您也可以不导入 SDK 的全局 `settings` 实例，而是导入 `Settings` 类，然后手动创建它。

```python
# 1. 导入您项目的 settings
from your_app_config import settings as project_settings

# 2. 导入 SDK 的 Settings 类
from okx_dex_sdk.config import Settings as OkxDexSettings
from okx_dex_sdk.client import OkxDexClient

# 3. 为 SDK 创建一个独立的配置实例
okx_config = OkxDexSettings() # 它会自动读取环境变量

# 4. 初始化客户端
client = OkxDexClient(okx_config)
```

## 📦 打包与发布

本项目使用 `pyproject.toml` 进行配置，遵循最新的 Python 打包标准 (PEP 517/518)。

### 1. 安装构建工具

首先，你需要安装官方推荐的打包工具 `build` 和 `twine`。

```bash
pip install --upgrade build twine
```

### 2. 构建包

在项目根目录下运行以下命令：

```bash
python -m build
```

这个命令会在项目根目录创建一个 `dist/` 文件夹，其中包含两种格式的包：
*   `.whl` (Wheel) 文件：一个预编译的二进制分发包，安装速度快。
*   `.tar.gz` (sdist) 文件：一个源代码分发包，用户在安装时需要自行构建。

### 3. (可选) 检查包

在上传之前，你可以使用 `twine` 来检查生成的文件是否符合规范。

```bash
twine check dist/*
```

### 4. 上传到 PyPI

最后，使用 `twine` 将你的包上传到 PyPI。你需要一个 PyPI 账户和 API token。

```bash
# --repository testpypi 用于上传到测试环境，首次发布时建议使用
twine upload --repository testpypi dist/*

# 确认在测试环境一切正常后，上传到正式 PyPI
twine upload dist/*
```

上传成功后，任何人都可以通过 `pip install okx-dex-sdk` 来安装和使用你的包。

## 法律声明

使用此 SDK，即表示您同意：OKX 及其关联方对任何直接、间接、偶然、特殊、后果性或惩戒性损害不承担任何责任，如法律免责声明中所述。
