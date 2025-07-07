from __future__ import annotations

from decimal import Decimal
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from .api import OKXDexAPI
from .chains.evm import EvmChain
from .chains.solana import SolanaChain
from .config import Settings
from .constants import ChainId, ChainType
from .models import (
    QuoteResponse,
    SwapResult,
    TokenBalanceRequestItem,
    TokenBalancesResponse,
    TokensResponse,
)

if TYPE_CHECKING:
    from .chains.sui import SuiChain


class OkxDexClient:
    """
    OKX DEX SDK 高级客户端。
    这个客户端是与 SDK 交互的主要入口点。
    """

    def __init__(self, settings: Settings):
        """
        初始化 OkxDexClient。

        Args:
            settings: 包含所有必要配置的 Pydantic-settings 对象。
        """
        self.settings = settings
        self.api = OKXDexAPI(
            api_key=self.settings.okx_api_key,
            secret_key=self.settings.okx_secret_key.get_secret_value(),
            passphrase=self.settings.okx_api_passphrase.get_secret_value(),
            access_project=self.settings.okx_project_id,
            http_proxy=self.settings.http_proxy,
        )
        self._chain_handlers: Dict[str, Union[EvmChain, SolanaChain, "SuiChain"]] = {}
        self.token_decimals_cache: Dict[str, int] = {}

    def _get_chain_handler(
        self, chain_id: str
    ) -> Union[EvmChain, SolanaChain, "SuiChain"]:
        """
        根据 chain_id 动态获取并缓存对应的链处理器。
        """
        if chain_id in self._chain_handlers:
            return self._chain_handlers[chain_id]

        if chain_id not in self.settings.chains:
            raise ValueError(f"Chain with id '{chain_id}' not configured in settings.")

        chain_settings = self.settings.chains[chain_id]

        if chain_id in [
            ChainId.ETHEREUM,
            ChainId.OKTC,
            ChainId.BSC,
            ChainId.POLYGON,
            ChainId.FANTOM,
            ChainId.AVALANCHE,
            ChainId.ARBITRUM,
            ChainId.OPTIMISM,
            ChainId.BASE,
        ]:
            handler = EvmChain(self.api, chain_settings)
        elif chain_id == ChainId.SOLANA:
            handler = SolanaChain(self.api, chain_settings)
        # elif chain_id == ChainId.SUI:
        #     handler = SuiChain(self.api, chain_settings)
        else:
            raise NotImplementedError(
                f"Chain type '{chain_settings.chain_type}' is not supported yet."
            )

        self._chain_handlers[chain_id] = handler
        return handler

    async def get_tokens(self, chain_id: str) -> TokensResponse:
        """
        获取支持的代币列表。
        """
        return await self.api.get_tokens(chain_id)

    async def get_quote(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        fee_percent: Optional[str] = None,
    ) -> QuoteResponse:
        """
        获取兑换报价。
        """
        from_token_decimals = await self.get_token_decimals_from_address(
            chain_id=chain_id, token_contract_address=from_token_address
        )
        raw_amount = int(Decimal(amount) * 10**from_token_decimals)
        print(f"raw_amount: {raw_amount}")
        return await self.api.get_quote(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=str(raw_amount),
            fee_percent=fee_percent,
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
    ) -> SwapResult:
        """
        执行兑换。
        """
        handler = self._get_chain_handler(chain_id)
        if not hasattr(handler, "execute_swap"):
            raise NotImplementedError(
                f"execute_swap is not implemented for chain_id {chain_id}"
            )

        from_token_decimals = await self.get_token_decimals_from_address(
            chain_id=chain_id, token_contract_address=from_token_address
        )
        raw_amount = int(Decimal(amount) * 10**from_token_decimals)

        return await handler.execute_swap(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=str(raw_amount),
            slippage=slippage,
            user_wallet_address=user_wallet_address,
            private_key=private_key,
        )

    async def execute_swap_via_balance_percent(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        balance_percent: str,
        slippage: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ) -> SwapResult:

        from_token_balance = await self.get_token_balance(
            chain_id=chain_id,
            user_wallet_address=user_wallet_address,
            token_contract_addresses=[from_token_address],
        )
        print(
            f"Token {from_token_address} 余额: {from_token_balance.data[0].token_assets[0].balance}"
        )
        from_token_decimals = await self.get_token_decimals_from_address(
            chain_id=chain_id, token_contract_address=from_token_address
        )
        raw_amount = int(
            Decimal(from_token_balance.data[0].token_assets[0].balance)
            * 10**from_token_decimals
            * Decimal(balance_percent)
        )
        print(f"raw_amount: {raw_amount}")

        handler = self._get_chain_handler(chain_id)
        if not hasattr(handler, "execute_swap"):
            raise NotImplementedError(
                f"execute_swap is not implemented for chain_id {chain_id}"
            )

        return await handler.execute_swap(
            chain_id=chain_id,
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=str(raw_amount),
            slippage=slippage,
            user_wallet_address=user_wallet_address,
            private_key=private_key,
        )

    async def approve(
        self,
        chain_id: str,
        token_contract_address: str,
        approve_amount: str,
        user_wallet_address: str,
        private_key: Optional[str] = None,
    ):
        handler = self._get_chain_handler(chain_id)
        if not hasattr(handler, "approve"):
            raise NotImplementedError(
                f"approve is not implemented for chain_id {chain_id}"
            )
        return await handler.approve(
            chain_id=chain_id,
            token_contract_address=token_contract_address,
            approve_amount=approve_amount,
            user_wallet_address=user_wallet_address,
            private_key=private_key,
        )

    async def get_token_balance(
        self,
        chain_id: str,
        user_wallet_address: str,
        token_contract_addresses: List[str],
    ) -> TokenBalancesResponse:
        """
        查询指定代币的余额。
        """
        token_contract_addresses_data = [
            TokenBalanceRequestItem(
                chain_index=chain_id,
                token_contract_address=token_contract_address,
            )
            for token_contract_address in token_contract_addresses
        ]
        return await self.api.get_token_balances(
            address=user_wallet_address,
            token_contract_addresses=token_contract_addresses_data,
        )

    async def get_all_token_balances(
        self,
        chains: List[str],
        user_wallet_address: str,
    ) -> TokenBalancesResponse:
        """
        获取资产明细（所有代币的余额）。
        """
        return await self.api.get_all_token_balances(
            address=user_wallet_address,
            chains=chains,
        )

    async def get_token_decimals_from_address(
        self, chain_id: str, token_contract_address: str
    ) -> int:
        """
        获取代币的小数位数。
        """
        if token_contract_address in self.token_decimals_cache:
            print(
                f"Token {token_contract_address} 小数位数缓存: {self.token_decimals_cache[token_contract_address]}"
            )
            return self.token_decimals_cache[token_contract_address]

        handler = self._get_chain_handler(chain_id)
        if not hasattr(handler, "get_token_decimals"):
            raise NotImplementedError(
                f"get_token_decimals is not implemented for chain_id {chain_id}"
            )
        decimals = await handler.get_token_decimals(token_contract_address)
        self.token_decimals_cache[token_contract_address] = decimals
        return decimals
