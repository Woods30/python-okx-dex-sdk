import asyncio
import traceback

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import NATIVE_TOKEN_ADDRESS, ChainId, ChainType
from okx_dex_sdk.utils import get_wallet_address


async def main():
    # 配置在导入 `settings` 时已自动加载并验证。
    print("配置加载成功。")

    client = OkxDexClient(settings)

    chain_id = ChainId.BSC

    # 检查 EVM 配置
    if chain_id not in settings.chains:
        print(f"请在 .env 文件中配置 chain_id='{chain_id}' 的 RPC 和私钥")
        print(
            f"例如: CHAINS__{chain_id}__RPC_URL=https://mainnet.base.org 和 CHAINS__{chain_id}__PRIVATE_KEY=..."
        )
        return

    wallet_address = get_wallet_address(
        ChainType.EVM, settings.chains[chain_id].private_key
    )
    print(f"使用钱包地址: {wallet_address}")

    to_token_address = NATIVE_TOKEN_ADDRESS[chain_id]  # BNB on BSC
    from_token_address = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"  # USDC on BSC
    amount_percent_to_swap = 1  # 兑换 0.001 BNB

    print(f"准备从 {from_token_address} 兑换到 {to_token_address}")

    # 1. 执行兑换 (将自动处理授权，并使用我们提供的 decimals)
    print("\n1. 正在执行兑换...")
    try:
        swap_result = await client.execute_swap_via_balance_percent(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            balance_percent=amount_percent_to_swap,
            slippage="0.01",  # 1% 滑点
            user_wallet_address=wallet_address,
        )
        print("   EVM 兑换成功!")
        print(f"     - 交易哈希: {swap_result.tx_hash}")
        # 注意: 这里可以根据 chain_id 映射到对应的浏览器
        print(
            f"     - 在区块浏览器上查看: https://bscscan.com/tx/0x{swap_result.tx_hash}"
        )
        print(
            f"     - 发送: {swap_result.from_amount_decimal:.6f} {swap_result.from_token.token_symbol}"
        )
        print(
            f"     - 收到: {swap_result.to_amount_decimal:.6f} {swap_result.to_token.token_symbol}"
        )

    except Exception as e:
        traceback.print_exc()
        print(f"   EVM 兑换失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
