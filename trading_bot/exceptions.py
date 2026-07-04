"""Custom exception hierarchy for the trading bot."""

class TradingBotError(Exception):
    pass

class ConfigurationError(TradingBotError):
    pass

class ValidationError(TradingBotError):
    pass

class AuthenticationError(TradingBotError):
    pass

class OrderError(TradingBotError):
    def __init__(self, message: str, code: int = -1, response: dict | None = None):
        super().__init__(message)
        self.code = code
        self.response = response or {}
