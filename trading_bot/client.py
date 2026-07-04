"""API layer: thin wrapper around Binance Futures Testnet REST endpoints."""
from __future__ import annotations
import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional
import requests
from .exceptions import AuthenticationError, ConfigurationError, OrderError
from .logger import setup_logger
from .models import OrderRequest

logger = setup_logger(__name__)
BASE_URL = "https://testnet.binancefuture.com"
ORDER_ENDPOINT = "/fapi/v1/order"
TIME_SYNC_ENDPOINT = "/fapi/v1/time"

class BinanceFuturesClient:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, base_url: str = BASE_URL, timeout: int = 10) -> None:
        self.api_key = api_key or os.getenv("BINANCE_TESTNET_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_TESTNET_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise ConfigurationError("Missing API credentials. Set BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET env vars.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        
        # Detect demo/mock mode
        placeholders = {"your_testnet_api_key_here", "your_testnet_api_secret_here", "demo", "mock"}
        self.demo_mode = (
            self.api_key in placeholders or
            self.api_secret in placeholders or
            (self.api_key is not None and self.api_key.startswith("http"))
        )
        if self.demo_mode:
            logger.info("BinanceFuturesClient initialised in offline DEMO/MOCK mode.")
        else:
            logger.info("BinanceFuturesClient initialised (base_url=%s)", self.base_url)

    def _sign(self, params: Dict[str, Any]) -> str:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def _build_signed_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        params["signature"] = self._sign(params)
        return params

    def _safe_log_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        redacted = dict(params)
        redacted.pop("signature", None)
        return redacted

    def ping(self) -> bool:
        url = f"{self.base_url}{TIME_SYNC_ENDPOINT}"
        try:
            r = self.session.get(url, timeout=self.timeout)
            return r.status_code == 200
        except requests.RequestException as exc:
            logger.error("Ping failed: %s", exc)
            return False

    def place_order(self, order: OrderRequest) -> Dict[str, Any]:
        order.validate()
        if self.demo_mode:
            logger.info("[DEMO MODE] Simulating order placement...")
            time.sleep(0.05)  # Simulate small network latency
            mock_price = str(order.price) if order.price is not None else "60000.0"
            payload = {
                "orderId": 987654321,
                "symbol": order.symbol,
                "status": "FILLED" if order.order_type == "MARKET" else "NEW",
                "clientOrderId": "demo_client_order_id",
                "price": mock_price,
                "avgPrice": mock_price,
                "origQty": str(order.quantity),
                "executedQty": str(order.quantity),
                "side": order.side.value,
                "type": order.order_type.value,
                "updateTime": int(time.time() * 1000)
            }
            logger.info("Order accepted (DEMO): orderId=%s status=%s", payload.get("orderId"), payload.get("status"))
            return payload

        params = self._build_signed_params(order.to_dict())
        url = f"{self.base_url}{ORDER_ENDPOINT}"
        logger.info("POST %s | params=%s", url, self._safe_log_params(params))
        try:
            response = self.session.post(url, data=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise OrderError(f"Network error: {exc}") from exc

        if response.status_code in (401, 403):
            raise AuthenticationError(f"Authentication failed (HTTP {response.status_code}). Check API key/secret.")
        try:
            payload = response.json()
        except ValueError:
            raise OrderError(f"Non-JSON response (HTTP {response.status_code}): {response.text[:300]}", code=response.status_code)

        if response.status_code >= 400:
            code = payload.get("code", response.status_code)
            msg = payload.get("msg", response.text)
            logger.error("Order rejected: HTTP=%s code=%s msg=%s", response.status_code, code, msg)
            raise OrderError(msg, code=code, response=payload)

        logger.info("Order accepted: orderId=%s status=%s", payload.get("orderId"), payload.get("status"))
        return payload
