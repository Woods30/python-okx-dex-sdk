class OKXDexSDKException(Exception):
    pass


class ChainNotSupported(OKXDexSDKException):
    pass


class TokenNotFound(OKXDexSDKException):
    pass
