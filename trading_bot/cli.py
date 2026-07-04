"""CLI layer: argument parsing, orchestration, and presentation."""
from __future__ import annotations
import argparse
import sys
from typing import List, Optional
from .client import BinanceFuturesClient
from .exceptions import AuthenticationError, ConfigurationError, OrderError, ValidationError
from .logger import setup_logger
from .models import OrderRequest, OrderType, Side

logger = setup_logger(__name__)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading-bot", description="Place MARKET/LIMIT orders on Binance USDT-M Futures Testnet.")
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=[s.value for s in Side], help="Order direction")
    parser.add_argument("--type", required=True, choices=[t.value for t in OrderType], help="Order type")
    parser.add_argument("--quantity", required=True, type=float, help="Order quantity")
    parser.add_argument("--price", type=float, default=None, help="Limit price (required when --type=LIMIT)")
    parser.add_argument("--api-key", default=None, help="Override API key")
    parser.add_argument("--api-secret", default=None, help="Override API secret")
    parser.add_argument("--ping", action="store_true", help="Only verify testnet connectivity.")
    return parser

def build_order_request(args: argparse.Namespace) -> OrderRequest:
    if args.type == OrderType.LIMIT.value and args.price is None:
        raise ValidationError("--price is required for LIMIT orders.")
    return OrderRequest(symbol=args.symbol, side=Side(args.side), order_type=OrderType(args.type), quantity=args.quantity, price=args.price)

def print_order_summary(order: OrderRequest) -> None:
    print("\n" + "=" * 50)
    print("             ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"  Symbol     : {order.symbol}")
    print(f"  Side       : {order.side.value}")
    print(f"  Type       : {order.order_type.value}")
    print(f"  Quantity   : {order.quantity}")
    if order.order_type == OrderType.LIMIT:
        print(f"  Price      : {order.price}")
        print(f"  TimeInForce: GTC")
    print("=" * 50 + "\n")

def print_order_response(response: dict) -> None:
    print("=" * 50)
    print("             ORDER RESPONSE")
    print("=" * 50)
    fields = [("orderId", "orderId"), ("status", "status"), ("symbol", "symbol"), ("side", "side"), ("type", "type"), ("origQty", "origQty"), ("executedQty", "executedQty"), ("avgPrice", "avgPrice"), ("price", "price")]
    for label, key in fields:
        if key in response:
            print(f"  {label:<14}: {response[key]}")
    print("=" * 50 + "\n")

def main(argv: Optional[List[str]] = None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = BinanceFuturesClient(api_key=args.api_key, api_secret=args.api_secret)
    except ConfigurationError as exc:
        print(f"[FAILURE] {exc}")
        return 3

    if args.ping:
        ok = client.ping()
        print(f"[{'SUCCESS' if ok else 'FAILURE'}] Testnet connectivity: {ok}")
        return 0 if ok else 1

    try:
        order = build_order_request(args)
    except ValidationError as exc:
        parser.error(str(exc))
        return 2

    print_order_summary(order)

    try:
        response = client.place_order(order)
    except AuthenticationError as exc:
        print(f"[FAILURE] Authentication error: {exc}")
        return 3
    except OrderError as exc:
        print(f"[FAILURE] Order rejected (code={exc.code}): {exc}")
        return 1

    print_order_response(response)
    print("[SUCCESS] Order placed successfully.")
    return 0
