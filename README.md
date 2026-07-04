# Simplified Binance Futures Testnet Trading Bot

A fast, lightweight Python CLI tool for placing MARKET and LIMIT orders on the Binance USDT-M Futures Testnet.

## Prerequisites

- Python 3.8 or higher
- Binance Futures Testnet API Key and Secret (register at [testnet.binancefuture.com](https://testnet.binancefuture.com/))

## Installation

1. Clone or navigate to the project directory:
   ```bash
   cd trading_bot
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the template `.env.example` file to `.env`:
   ```bash
   # Windows (cmd/PowerShell):
   copy .env.example .env
   # macOS/Linux:
   cp .env.example .env
   ```

2. Open the `.env` file and replace the placeholders with your actual credentials:
   ```env
   BINANCE_TESTNET_API_KEY=your_testnet_api_key_here
   BINANCE_TESTNET_API_SECRET=your_testnet_api_secret_here
   ```

## Usage

You can invoke the bot using `python -m trading_bot` followed by arguments.

### 1. Verify Connectivity (Ping)

Check if the client can successfully communicate with the Binance Futures Testnet server:
```bash
python -m trading_bot --ping
```

### 2. Place a MARKET Buy Order

Place a market buy order for a specific symbol (e.g., BTCUSDT):
```bash
python -m trading_bot --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### 3. Place a LIMIT Sell Order

Place a limit sell order at a specific price:
```bash
python -m trading_bot --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000.0
```

### Command Line Options

```text
options:
  -h, --help            show this help message and exit
  --symbol SYMBOL       Trading pair, e.g. BTCUSDT
  --side {BUY,SELL}     Order direction
  --type {MARKET,LIMIT}
                        Order type
  --quantity QUANTITY   Order quantity
  --price PRICE         Limit price (required when --type=LIMIT)
  --api-key API_KEY     Override API key
  --api-secret API_SECRET
                        Override API secret
  --ping                Only verify testnet connectivity.
```

## Logs

A rotating file handler records detailed operational logs inside the `logs/` directory.
