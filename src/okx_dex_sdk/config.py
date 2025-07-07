import sys
from typing import Dict, Optional

from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChainSettings(BaseSettings):
    """单条链的配置"""

    rpc_url: str
    private_key: str


class Settings(BaseSettings):
    """
    主配置类，使用 pydantic-settings 自动从环境变量加载。
    """

    # .env 文件路径和编码
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__"
    )

    # OKX API 凭证
    okx_api_key: str
    okx_secret_key: SecretStr
    okx_api_passphrase: SecretStr
    okx_project_id: Optional[str] = None
    http_proxy: Optional[str] = None

    # 链特定配置, key 为 chain_id
    chains: Dict[str, ChainSettings] = {}


# 创建一个全局可用的配置实例
# 这段代码会在模块被导入时执行
try:
    settings = Settings()
except ValidationError as e:
    print("--- 配置错误 ---", file=sys.stderr)
    print(
        "错误: SDK 配置加载失败。请确保项目根目录下的 .env 文件存在且格式正确。",
        file=sys.stderr,
    )
    print("详细错误信息如下:", file=sys.stderr)
    print(e, file=sys.stderr)
    print("-----------------", file=sys.stderr)
    sys.exit(1)
