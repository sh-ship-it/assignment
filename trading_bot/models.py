"""Order domain models and validation logic."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from .exceptions import ValidationError

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float
    price: Optional[float] = None

    def validate(self) -> None:
        if not self.symbol or not self.symbol.isupper() or not self.symbol.isalnum():
            raise ValidationError("Symbol must be a non-empty, uppercase, alphanumeric string (e.g. BTCUSDT).")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.order_type == OrderType.LIMIT:
            if self.price is None:
                raise ValidationError("Price is required for LIMIT orders.")
            if self.price <= 0:
                raise ValidationError("Price must be greater than zero for LIMIT orders.")

    def to_dict(self) -> dict:
        data = {"symbol": self.symbol, "side": self.side.value, "type": self.order_type.value, "quantity": self.quantity}
        if self.order_type == OrderType.LIMIT:
            data["price"] = self.price
            data["timeInForce"] = "GTC"
        return data
