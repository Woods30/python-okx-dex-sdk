from __future__ import annotations

import base64
from typing import Optional

from base58 import b58decode, b58encode
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from okx_dex_sdk.constants import NATIVE_TOKEN_ADDRESS, ChainId

from ..api import OKXDexAPI
from ..config import ChainSettings
from ..exceptions import OKXDexSDKException
from ..models import SwapResult


class SolanaChain:
    """
    处理 Solana 链特定操作的类。
    """

    SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

    def __init__(self, api_client: OKXDexAPI, settings: ChainSettings):
        """
        初始化 SolanaChain。

        Args:
            api_client: OKXDexAPI 的实例。
            settings: Solana 相关的 pydantic-settings 配置对象。
        """
        self.api = api_client
        self.settings = settings
        self.private_key = self.settings.private_key

        # 初始化 Solana 客户端
        self.solana_client = AsyncClient(settings.rpc_url or self.SOLANA_RPC_URL)

    async def poll_for_confirmation(self, tx_sig: str, sleep_seconds: float = 0.5):
        """轮询确认交易。"""
        await self.solana_client.confirm_transaction(
            tx_sig=tx_sig, commitment="confirmed", sleep_seconds=sleep_seconds
        )

    async def execute_swap(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        slippage: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
        poll_for_confirmation: bool = False,
        poll_sleep_seconds: float = 0.5,
    ) -> SwapResult:
        """根据 Solders 文档执行 Solana 兑换交易。"""

        assert chain_id == "501", "Solana 链 ID 必须为 501"
        # 验证私钥
        private_key = private_key or self.private_key
        if not private_key:
            raise ValueError("执行 Solana 交易需要私钥")

        # 1. 获取兑换交易数据
        swap_response = await self.api.swap(
            chain_id="501",  # Solana Chain ID
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            slippage=slippage,
            user_wallet_address=user_wallet_address,
        )
        router_result = swap_response.data[0].router_result

        # 2. 获取最新的区块哈希
        recent_blockhash = await self.solana_client.get_latest_blockhash("confirmed")

        # 3. 从私钥字节创建密钥对
        fee_payer = Keypair.from_bytes(b58decode(private_key))

        try:
            # 4. 解码交易字节
            tx_bytes = b58decode(swap_response.data[0].tx.data)
            original_tx = VersionedTransaction.from_bytes(tx_bytes)

            # 5. 使用更新后的区块哈希创建新消息
            new_message = MessageV0(
                header=original_tx.message.header,
                account_keys=original_tx.message.account_keys,
                recent_blockhash=recent_blockhash.value.blockhash,
                instructions=original_tx.message.instructions,
                address_table_lookups=original_tx.message.address_table_lookups,
            )

            # 6. 创建并签署交易
            tx = VersionedTransaction(new_message, [fee_payer])

            # 7. 发送并确认交易
            opts = TxOpts(
                skip_preflight=False,
                preflight_commitment="confirmed",
                max_retries=10,
            )
            result = await self.solana_client.send_transaction(tx, opts=opts)
            tx_hash = str(result.value)

            if poll_for_confirmation:
                await self.poll_for_confirmation(tx_hash, poll_sleep_seconds)

            # 使用 model_validate 创建实例，这种方式更健壮
            result_data = router_result.model_dump()
            result_data["tx_hash"] = tx_hash
            return SwapResult.model_validate(result_data)

        except Exception as e:
            raise ValueError(f"Solana 交易执行失败: {e}") from e

    async def execute_swap_via_okx(
        self,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        slippage: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ) -> str:
        """
        通过 OKX 广播 API 执行 Solana 兑换交易。
        返回用于跟踪的订单 ID。
        """
        # 获取兑换交易数据
        raw_swap = await self.api.swap(
            chain_id="501",
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            slippage=slippage,
            user_wallet_address=user_wallet_address,
        )

        try:
            # 获取最新的区块哈希
            recent_blockhash = await self.solana_client.get_latest_blockhash()

            # 从私钥字节创建密钥对
            private_key = private_key or self.private_key
            if not private_key:
                raise ValueError("执行 Solana 交易需要私钥")
            fee_payer = Keypair.from_bytes(b58decode(private_key))

            # 解码交易字节
            tx_bytes = b58decode(raw_swap.data[0].tx.data)
            original_tx = VersionedTransaction.from_bytes(tx_bytes)

            # 使用更新后的区块哈希创建新消息
            new_message = MessageV0(
                header=original_tx.message.header,
                account_keys=original_tx.message.account_keys,
                recent_blockhash=recent_blockhash.value.blockhash,
                instructions=original_tx.message.instructions,
                address_table_lookups=original_tx.message.address_table_lookups,
            )

            # 创建并签署新交易
            tx = VersionedTransaction(new_message, [fee_payer])

            # 将交易转换为 base58 字符串以用于 OKX API
            signed_tx_str = b58encode(bytes(tx)).decode("utf-8")

            # 广播已签名的交易
            order_id = await self.api.broadcast_transaction(
                signed_tx=signed_tx_str,
                chain_index="501",
                address=user_wallet_address,
            )
            return order_id

        except Exception as e:
            raise ValueError(f"交易失败: {e}") from e

    async def get_token_decimals(self, token_contract_address: str) -> int:
        """
        通过 Solana RPC 获取代币的小数位数。
        如果地址是原生 SOL，则直接返回 9。
        否则，查询 mint 账户信息来获取 decimals。
        """
        if (
            token_contract_address.lower()
            == NATIVE_TOKEN_ADDRESS[ChainId.SOLANA].lower()
        ):
            return 9

        if not self.settings.rpc_url:
            raise ValueError("Solana RPC URL is not configured.")

        try:
            mint_pubkey = Pubkey.from_string(token_contract_address)
            account_info = await self.solana_client.get_account_info_json_parsed(
                mint_pubkey
            )

            if account_info.value and hasattr(account_info.value.data, "parsed"):
                decimals = account_info.value.data.parsed["info"]["decimals"]
                return int(decimals)
            else:
                raise OKXDexSDKException(
                    f"无法解析代币 {token_contract_address} 的小数位数。请检查地址是否为有效的 SPL Token Mint 地址。"
                )
        except Exception as e:
            raise OKXDexSDKException(
                f"查询代币 {token_contract_address} 小数位数时出错: {e}"
            ) from e
