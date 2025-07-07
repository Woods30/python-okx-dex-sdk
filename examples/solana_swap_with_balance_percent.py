import asyncio
import os

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId, ChainType
from okx_dex_sdk.utils import get_wallet_address


async def main():
    """
    本示例演示如何在 Solana 链上执行一笔兑换交易。
    """
    # 配置在导入 `settings` 时已自动加载并验证。
    print("配置加载成功。")

    client = OkxDexClient(settings)
    chain_id = ChainId.SOLANA

    # 检查并派生钱包地址
    if chain_id not in settings.chains:
        print(f"请在 .env 文件中配置 chain_id={chain_id} 的 RPC 和私钥")
        print(
            f"例如: CHAINS__{chain_id}__RPC_URL=... 和 CHAINS__{chain_id}__PRIVATE_KEY=..."
        )
        return

    private_key = settings.solana_private_key
    wallet_address = get_wallet_address(ChainType.SOLANA, private_key)
    print(f"使用钱包地址: {wallet_address}")

    to_token = "11111111111111111111111111111111"  # SOL
    from_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    # from_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    # to_token = "11111111111111111111111111111111"  # SOL
    balance_percent = "1"  # 兑换 0.001 SOL
    slippage = "0.01"  # 1% 滑点

    # 准备：获取代币列表，这是 swap API 的前置要求
    print("正在获取代币列表...")
    await client.get_tokens(chain_id=chain_id)

    # 执行兑换 (SOL -> USDC)
    print(f"准备执行兑换: {balance_percent}% SOL -> USDC...")
    swap_params = {
        "chain_id": chain_id,
        "from_token_address": from_token,
        "to_token_address": to_token,
        "balance_percent": balance_percent,
        "slippage": slippage,
        "user_wallet_address": wallet_address,
        "private_key": private_key,
    }
    try:
        swap_result = await client.execute_swap_via_balance_percent(**swap_params)
        print("Solana 兑换成功!")
        print(f"  - 交易哈希 (txhash): {swap_result.tx_hash}")
        print(f"  - 在 Solscan 上查看: https://solscan.io/tx/{swap_result.tx_hash}")
        print(
            f"  - 发送 (from token ui): {swap_result.from_amount_decimal:.6f} {swap_result.from_token.token_symbol}"
        )
        print(
            f"  - 收到 (to token amount): {swap_result.to_amount_decimal:.6f} {swap_result.to_token.token_symbol}"
        )
        print(f"  - 滑点 (price_impact_pct): {swap_result.price_impact_pct}%")
        print(f"  - 执行价格 (execution_price): {swap_result.execution_price}")
        print(f"  - 价值 (value_in_usd): {swap_result.value_in_usd}")
        print(f"  - from token price: {swap_result.from_token.token_unit_price}")
        print(f"  - to token price: {swap_result.to_token.token_unit_price}")
        print(f"  - 交易费 (trade_fee): {swap_result.trade_fee}")

    except Exception as e:
        print(f"Solana 兑换失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
