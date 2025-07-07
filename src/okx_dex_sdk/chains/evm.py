from __future__ import annotations

import time
from pprint import pprint

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

        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)

    async def _check_and_approve_token(
        self,
        token_contract: Contract,
        spender_address: str,
        required_amount: int,
        chain_id: str,
    ):
        """
        使用合约实例检查代币授权额度，如果不足则在本地构建、发送并等待授权交易。
        """
        current_allowance = token_contract.functions.allowance(
            self.account.address, spender_address
        ).call()
        print(f"当前代币授权额度: {current_allowance}，所需授权额度: {required_amount}")

        if current_allowance < required_amount:
            print(
                f"当前代币授权额度 ({current_allowance}) 低于本次所需 ({required_amount})。"
                f"正在为代币 {token_contract.address} 向合约 {spender_address} 授权数量: {required_amount}"
            )

            # 1. 在本地构建 approve 交易
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            max_priority_fee_per_gas = self.w3.eth.max_priority_fee
            latest_block = self.w3.eth.get_block("latest")
            base_fee_per_gas = latest_block.get("baseFeePerGas", 0)
            max_fee_per_gas = int(base_fee_per_gas * 1.2) + max_priority_fee_per_gas

            approve_tx_data = token_contract.functions.approve(
                spender_address, required_amount
            ).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                    "maxFeePerGas": max_fee_per_gas,
                    "chainId": int(chain_id),
                }
            )

            # 2. 签名并发送
            signed_tx = self.w3.eth.account.sign_transaction(
                approve_tx_data, self.private_key
            )
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"授权交易已发送: {tx_hash.hex()}. 正在等待确认...")

            # 3. 等待确认
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print("授权已确认。")

    async def execute_swap(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        slippage: str,
        user_wallet_address: str,
    ) -> SwapResult:
        """
        执行 EVM 链上的兑换。
        """
        if not self.private_key:
            raise ValueError("A private key is required to execute a swap.")

        # 2. 获取兑换交易数据
        swap_response = await self.api.swap(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount,
            slippage=slippage,
            user_wallet_address=user_wallet_address,
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
            spender_address = self.w3.to_checksum_address(tx_data.to)
            await self._check_and_approve_token(
                token_contract=token_contract,
                spender_address=spender_address,
                required_amount=int(amount),
                chain_id=chain_id,
            )

        # 4. 构建 EIP-1559 格式的交易
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        max_priority_fee_per_gas = self.w3.eth.max_priority_fee
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = latest_block.get("baseFeePerGas", 0)
        # 使用更平滑的 gas fee 估算策略，避免费用过高
        max_fee_per_gas = int(base_fee_per_gas * 5) + max_priority_fee_per_gas

        tx_params = {
            "from": self.w3.to_checksum_address(tx_data.from_address),
            "to": self.w3.to_checksum_address(tx_data.to),
            "value": int(tx_data.value),
            # 为 API 返回的 gas limit 增加 50% 的缓冲，防止 "out of gas"
            "gas": int(int(tx_data.gas) * 1.5),
            "data": tx_data.data,
            "nonce": nonce,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas,
            "chainId": self.w3.eth.chain_id,
        }
        pprint(f"tx_params: {tx_params}")

        # 在发送交易前进行模拟
        print("正在模拟交易...")
        simulation = await self.simulate_transaction(tx_params)

        if not simulation["success"]:
            raise OKXDexSDKException(f"交易模拟失败: {simulation['error']}")

        # 5. 签名交易
        signed_tx = self.w3.eth.account.sign_transaction(tx_params, self.private_key)

        # 6. 发送交易
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # 7. 等待交易确认
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt.status != 1:
            raise OKXDexSDKException(f"Transaction failed: {tx_receipt}")

        result_data = router_result.model_dump()
        result_data["tx_hash"] = tx_hash.hex()
        return SwapResult.model_validate(result_data)

    async def approve(
        self,
        chain_id: str,
        token_contract_address: str,
        approve_amount: str,
    ):
        """
        执行 EVM 链上的代币授权。
        """
        if not self.private_key:
            raise ValueError("A private key is required to approve a token.")

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
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        max_priority_fee_per_gas = self.w3.eth.max_priority_fee
        latest_block = self.w3.eth.get_block("latest")
        base_fee_per_gas = latest_block.get("baseFeePerGas", 0)
        # 使用更平滑的 gas fee 估算策略，避免费用过高
        max_fee_per_gas = int(base_fee_per_gas * 1.2) + max_priority_fee_per_gas

        tx_params = {
            "to": self.w3.to_checksum_address(tx_data.dex_contract_address),
            "from": self.w3.to_checksum_address(self.account.address),
            "gas": int(tx_data.gas_limit),
            "data": tx_data.data,
            "nonce": nonce,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "maxFeePerGas": max_fee_per_gas,
            "chainId": self.w3.eth.chain_id,
        }

        # 3. 签名交易
        signed_tx = self.w3.eth.account.sign_transaction(tx_params, self.private_key)

        # 4. 发送交易
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # 5. 等待交易确认
        self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_hash.hex()

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

    async def simulate_transaction(self, tx_params: dict) -> dict:
        """
        模拟交易执行，返回模拟结果和gas估算。

        Args:
            tx_params: 交易参数字典

        Returns:
            包含模拟结果的字典
        """
        simulation_result = {
            "success": False,
            "estimated_gas": None,
            "call_result": None,
            "error": "",
        }

        try:
            # 1. 估算gas使用量
            estimated_gas = self.w3.eth.estimate_gas(tx_params)
            simulation_result["estimated_gas"] = estimated_gas

            # 2. 模拟调用（对于有返回值的交易）
            if tx_params.get("data"):
                call_result = self.w3.eth.call(tx_params)
                simulation_result["call_result"] = call_result.hex()

            simulation_result["success"] = True
            print(f"✅ 交易模拟成功，预估gas: {estimated_gas}")
        except Exception as e:
            simulation_result["error"] = str(e)
            simulation_result["success"] = False
            print(f"❌ 交易模拟失败: {e}")

        return simulation_result
