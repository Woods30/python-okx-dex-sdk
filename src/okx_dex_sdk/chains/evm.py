from __future__ import annotations

import time
from pprint import pprint
from typing import Optional

from web3 import Web3
from web3.contract import Contract
from web3.middleware import ExtraDataToPOAMiddleware

from okx_dex_sdk.exceptions import OKXDexSDKException

from ..api import OKXDexAPI
from ..config import ChainSettings
from ..constants import NATIVE_TOKEN_ADDRESS, ChainType
from ..models import SwapResult

# 标准 ERC20 ABI，包含了 decimals, allowance, 和 approve 方法
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]


class EvmChain:
    """
    处理 EVM 兼容链特定操作的类。
    """

    def __init__(self, api_client: OKXDexAPI, settings: ChainSettings):
        """
        初始化 EvmChain。

        Args:
            api_client: OKXDexAPI 的实例。
            settings: EVM 相关的 pydantic-settings 配置对象。
        """
        self.api = api_client
        self.settings = settings
        self.private_key = self.settings.private_key

        if not self.settings.rpc_url:
            raise ValueError("EVM a Rpc url is required")

        self.w3 = Web3(Web3.HTTPProvider(self.settings.rpc_url))
        # Add POA middleware for chains like BSC, ankr, etc.
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    async def _check_and_approve_token(
        self,
        token_contract: Contract,
        # spender_address: str,
        required_amount: int,
        chain_id: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ):
        """
        使用合约实例检查代币授权额度，如果不足则在本地构建、发送并等待授权交易。
        """
        private_key = private_key or self.private_key
        if not private_key:
            raise ValueError("执行APPROVE交易需要提供钱包私钥")

        dex_contract_address = await self.get_dex_contract_address(chain_id)

        current_allowance = token_contract.functions.allowance(
            user_wallet_address, dex_contract_address
        ).call()
        print(f"当前代币授权额度: {current_allowance}，所需授权额度: {required_amount}")

        if current_allowance < required_amount:
            print(
                f"当前代币授权额度 ({current_allowance}) 低于本次所需 ({required_amount})。"
                f"正在为代币 {token_contract.address} 向合约 {dex_contract_address} 授权数量: {required_amount}"
            )

            # 1. 在本地构建 approve 交易
            approve_tx_data = token_contract.functions.approve(
                dex_contract_address, required_amount
            ).build_transaction(
                {
                    "from": user_wallet_address,
                    "chainId": int(chain_id),
                }
            )

            # 2. 签名并发送
            await self._execute_evm_transaction(approve_tx_data, private_key)
            print("授权已确认。")

    async def _execute_evm_transaction(self, tx_params: dict, private_key: str) -> str:
        """
        统一执行 EVM 交易的方法，包括模拟、填充nonce/gas、签名、发送和等待确认。

        Args:
            tx_params: 交易参数字典。
            private_key: 用于签名的私钥。

        Returns:
            交易哈希字符串。
        """
        if "from" not in tx_params:
            raise ValueError("交易参数'tx_params'中必须包含 'from' 地址")

        # 0. 在发送交易前进行模拟
        print("正在模拟交易...")
        try:
            # 如果调用者没有提供 gas limit，我们在这里通过模拟估算它
            if "gas" not in tx_params:
                estimated_gas = self.w3.eth.estimate_gas(tx_params)
                tx_params["gas"] = estimated_gas

            # 模拟调用以检查是否会 revert
            if tx_params.get("data"):
                self.w3.eth.call(tx_params)

            print(f"✅ 交易模拟成功，预估/设定gas: {tx_params.get('gas')}")
        except Exception as e:
            raise OKXDexSDKException(f"交易模拟失败: {e}") from e

        # 1. 填充 nonce (如果不存在)
        if "nonce" not in tx_params:
            checksum_from = self.w3.to_checksum_address(tx_params["from"])
            tx_params["nonce"] = self.w3.eth.get_transaction_count(checksum_from)

        # 2. 填充 EIP-1559 gas 费用 (如果不存在)
        if "maxPriorityFeePerGas" not in tx_params:
            tx_params["maxPriorityFeePerGas"] = self.w3.eth.max_priority_fee

        if "maxFeePerGas" not in tx_params:
            latest_block = self.w3.eth.get_block("latest")
            base_fee_per_gas = latest_block.get("baseFeePerGas", 0)
            tx_params["maxFeePerGas"] = (
                int(base_fee_per_gas * 5) + tx_params["maxPriorityFeePerGas"]
            )

        # 3. 估算并填充 gas limit (如果不存在, 尽管模拟步骤已处理)
        if "gas" not in tx_params:
            tx_params["gas"] = self.w3.eth.estimate_gas(tx_params)

        # 4. 签名交易
        signed_tx = self.w3.eth.account.sign_transaction(tx_params, private_key)

        # 5. 发送交易
        tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = tx_hash_bytes.hex()
        print(f"交易已发送: {tx_hash}. 正在等待确认...")

        # 6. 等待交易确认
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(
            tx_hash_bytes, timeout=120
        )

        if tx_receipt.status != 1:
            raise OKXDexSDKException(
                f"交易失败，状态码: {tx_receipt.status}，交易哈希: {tx_receipt['transactionHash'].hex()}"
            )

        print(f"✅ 交易已确认: {tx_hash}")
        return tx_hash

    async def execute_swap(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        slippage: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ) -> SwapResult:
        """
        执行 EVM 链上的兑换。
        """
        private_key = private_key or self.private_key
        if not private_key:
            raise ValueError("执行SWAP交易需要提供钱包私钥")

        user_checksum_address = self.w3.to_checksum_address(user_wallet_address)

        # 2. 获取兑换交易数据
        swap_response = await self.api.swap(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            slippage=slippage,
            user_wallet_address=user_checksum_address,
        )

        if not swap_response.data:
            raise ValueError(f"Failed to get swap data: {swap_response.msg}")

        router_result = swap_response.data[0].router_result
        tx_data = swap_response.data[0].tx

        if not tx_data:
            raise ValueError(f"Failed to get tx data: {swap_response.msg}")

        # 3. 如果是 ERC20 代币，则检查并处理授权
        if from_token_address.lower() != NATIVE_TOKEN_ADDRESS[ChainType.EVM].lower():
            token_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(from_token_address),
                abi=ERC20_ABI,
            )
            # spender_address = self.w3.to_checksum_address(tx_data.to)
            await self._check_and_approve_token(
                token_contract=token_contract,
                # spender_address=spender_address,
                required_amount=int(amount),
                chain_id=chain_id,
                user_wallet_address=user_checksum_address,
                private_key=private_key,
            )

        # 4. 构建 EIP-1559 格式的交易
        tx_params = {
            "from": self.w3.to_checksum_address(tx_data.from_address),
            "to": self.w3.to_checksum_address(tx_data.to),
            "value": int(tx_data.value),
            # 为 API 返回的 gas limit 增加 50% 的缓冲，防止 "out of gas"
            "gas": int(int(tx_data.gas) * 1.5),
            "data": tx_data.data,
            "chainId": self.w3.eth.chain_id,
        }

        # 5. 签名并发送交易 (模拟已内置)
        tx_hash = await self._execute_evm_transaction(tx_params, private_key)

        result_data = router_result.model_dump()
        result_data["tx_hash"] = tx_hash
        return SwapResult.model_validate(result_data)

    async def approve(
        self,
        chain_id: str,
        token_contract_address: str,
        approve_amount: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ):
        """
        执行 EVM 链上的代币授权。
        """
        private_key = private_key or self.private_key
        if not private_key:
            raise ValueError("执行APPROVE交易需要提供钱包私钥")

        user_checksum_address = self.w3.to_checksum_address(user_wallet_address)

        # 1. 获取授权交易数据
        approve_response = await self.api.approve_transaction(
            chain_id=chain_id,
            token_contract_address=token_contract_address,
            approve_amount=approve_amount,
        )

        if not approve_response.data:
            raise ValueError(f"Failed to get approval data: {approve_response.msg}")

        tx_data = approve_response.data[0]

        # 2. 构建 EIP-1559 格式的交易
        tx_params = {
            "to": self.w3.to_checksum_address(tx_data.dex_contract_address),
            "from": user_checksum_address,
            "gas": int(tx_data.gas_limit),
            "data": tx_data.data,
            "chainId": self.w3.eth.chain_id,
        }

        pprint(tx_params)
        # 3. 签名并发送交易
        tx_hash = await self._execute_evm_transaction(tx_params, private_key)
        return tx_hash

    async def get_token_decimals(self, token_contract_address: str) -> int:
        """
        通过 ERC20 ABI 获取代币的小数位数。
        """
        if (
            token_contract_address.lower()
            == NATIVE_TOKEN_ADDRESS[ChainType.EVM].lower()
        ):
            return 18

        token_contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(token_contract_address),
            abi=ERC20_ABI,
        )
        return token_contract.functions.decimals().call()

    async def get_dex_contract_address(self, chain_id: str) -> str:
        """
        获取指定链的 DEX 合约地址。
        """
        response = await self.api.get_supported_chains(chain_id)
        if not response.data[0].dex_token_approve_address:
            raise ValueError(f"Failed to get dex contract address: {response.msg}")

        return response.data[0].dex_token_approve_address
