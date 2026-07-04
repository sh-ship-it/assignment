"""Tkinter GUI for the Simplified Binance Futures Testnet Trading Bot."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import os
from typing import Any
from dotenv import load_dotenv

from .client import BinanceFuturesClient
from .models import OrderRequest, Side, OrderType
from .exceptions import TradingBotError

# Styling Constants
BG_COLOR = "#121214"          # Deep Dark
CARD_BG = "#1e1e24"           # Medium Dark
TEXT_COLOR = "#ffffff"        # White text
ACCENT_YELLOW = "#f0b90b"     # Binance Yellow
ACCENT_GREEN = "#0ecb81"      # Binance Buy Green
ACCENT_RED = "#f6465d"        # Binance Sell Red
TEXT_MUTED = "#848e9c"        # Grey text
FONT_FAMILY = "Segoe UI"

class TradingBotGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Binance Futures Trading Bot")
        self.root.geometry("620x750")
        self.root.configure(bg=BG_COLOR)
        
        # Load environment variables
        load_dotenv()
        
        self._setup_styles()
        self._build_ui()
        self._init_client()

    def _setup_styles(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure Ttk frame and label styles
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_FAMILY, 10))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background=CARD_BG, relief="flat", borderwidth=0)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_COLOR)
        self.style.configure("Title.TLabel", background=BG_COLOR, foreground=ACCENT_YELLOW, font=(FONT_FAMILY, 16, "bold"))
        self.style.configure("Section.TLabel", background=CARD_BG, foreground=ACCENT_YELLOW, font=(FONT_FAMILY, 11, "bold"))
        
        # ComboBox styles
        self.style.map("TCombobox", fieldbackground=[("readonly", CARD_BG)], background=[("readonly", CARD_BG)], foreground=[("readonly", TEXT_COLOR)])

    def _build_ui(self) -> None:
        # 1. Title Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=15)
        
        title_lbl = ttk.Label(header_frame, text="BINANCE FUTURES BOT", style="Title.TLabel")
        title_lbl.pack(side="left")
        
        self.mode_lbl = ttk.Label(header_frame, text="Offline Mode", foreground=ACCENT_YELLOW, font=(FONT_FAMILY, 10, "italic"))
        self.mode_lbl.pack(side="right", pady=5)

        # 2. Credentials Card
        cred_frame = ttk.Frame(self.root, style="Card.TFrame")
        cred_frame.pack(fill="x", padx=20, pady=10)
        cred_container = tk.Frame(cred_frame, bg=CARD_BG, padx=15, pady=15)
        cred_container.pack(fill="x")
        
        ttk.Label(cred_container, text="API CONFIGURATION", style="Section.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        ttk.Label(cred_container, text="API Key:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.api_key_var = tk.StringVar(value=os.getenv("BINANCE_TESTNET_API_KEY", ""))
        self.api_key_entry = tk.Entry(cred_container, textvariable=self.api_key_var, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=(FONT_FAMILY, 10))
        self.api_key_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        ttk.Label(cred_container, text="API Secret:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.api_secret_var = tk.StringVar(value=os.getenv("BINANCE_TESTNET_API_SECRET", ""))
        self.api_secret_entry = tk.Entry(cred_container, textvariable=self.api_secret_var, show="*", bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=(FONT_FAMILY, 10))
        self.api_secret_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        cred_container.columnconfigure(1, weight=1)
        
        # Ping and Re-init buttons
        btn_frame = tk.Frame(cred_container, bg=CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.apply_btn = tk.Button(btn_frame, text="Apply & Reconnect", command=self._init_client, bg=ACCENT_YELLOW, fg=BG_COLOR, font=(FONT_FAMILY, 9, "bold"), relief="flat", cursor="hand2", activebackground="#dfaa00", activeforeground=BG_COLOR)
        self.apply_btn.pack(side="left", padx=(0, 10))
        
        self.ping_btn = tk.Button(btn_frame, text="Ping Testnet", command=self._ping_testnet, bg=BG_COLOR, fg=TEXT_COLOR, font=(FONT_FAMILY, 9), relief="flat", cursor="hand2", activebackground=CARD_BG, activeforeground=TEXT_COLOR)
        self.ping_btn.pack(side="left")
        
        self.ping_status_lbl = ttk.Label(btn_frame, text="", style="Card.TLabel", font=(FONT_FAMILY, 9, "bold"))
        self.ping_status_lbl.pack(side="right")

        # 3. Order Placement Card
        order_frame = ttk.Frame(self.root, style="Card.TFrame")
        order_frame.pack(fill="x", padx=20, pady=10)
        order_container = tk.Frame(order_frame, bg=CARD_BG, padx=15, pady=15)
        order_container.pack(fill="x")
        
        ttk.Label(order_container, text="PLACE NEW ORDER", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Symbol
        ttk.Label(order_container, text="Symbol (e.g. BTCUSDT):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        self.symbol_combobox = ttk.Combobox(order_container, textvariable=self.symbol_var, values=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT"], font=(FONT_FAMILY, 10))
        self.symbol_combobox.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Side Selector (BUY/SELL buttons)
        ttk.Label(order_container, text="Direction:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        side_frame = tk.Frame(order_container, bg=CARD_BG)
        side_frame.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.side_var = tk.StringVar(value="BUY")
        self.buy_radio = tk.Radiobutton(side_frame, text="BUY", variable=self.side_var, value="BUY", bg=CARD_BG, fg=ACCENT_GREEN, selectcolor=BG_COLOR, font=(FONT_FAMILY, 10, "bold"), activebackground=CARD_BG, activeforeground=ACCENT_GREEN)
        self.buy_radio.pack(side="left", padx=(0, 15))
        self.sell_radio = tk.Radiobutton(side_frame, text="SELL", variable=self.side_var, value="SELL", bg=CARD_BG, fg=ACCENT_RED, selectcolor=BG_COLOR, font=(FONT_FAMILY, 10, "bold"), activebackground=CARD_BG, activeforeground=ACCENT_RED)
        self.sell_radio.pack(side="left")
        
        # Type
        ttk.Label(order_container, text="Order Type:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        self.type_var = tk.StringVar(value="MARKET")
        self.type_combobox = ttk.Combobox(order_container, textvariable=self.type_var, values=["MARKET", "LIMIT"], state="readonly", font=(FONT_FAMILY, 10))
        self.type_combobox.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.type_combobox.bind("<<ComboboxSelected>>", self._on_type_change)
        
        # Quantity
        ttk.Label(order_container, text="Quantity:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        self.qty_var = tk.StringVar(value="0.001")
        self.qty_entry = tk.Entry(order_container, textvariable=self.qty_var, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=(FONT_FAMILY, 10))
        self.qty_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        # Price (Conditional)
        self.price_label = ttk.Label(order_container, text="Limit Price:", style="Card.TLabel")
        self.price_label.grid(row=5, column=0, sticky="w", pady=5)
        self.price_var = tk.StringVar(value="")
        self.price_entry = tk.Entry(order_container, textvariable=self.price_var, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=(FONT_FAMILY, 10))
        self.price_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        
        order_container.columnconfigure(1, weight=1)
        self._on_type_change() # Update visibility of price input
        
        # Submit Button
        self.order_btn = tk.Button(order_container, text="PLACE ORDER", command=self._place_order, bg=ACCENT_GREEN, fg=BG_COLOR, font=(FONT_FAMILY, 11, "bold"), relief="flat", cursor="hand2", activebackground="#0b9a62", activeforeground=BG_COLOR)
        self.order_btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        # 4. Logs Console
        log_frame = ttk.Frame(self.root, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        log_container = tk.Frame(log_frame, bg=CARD_BG, padx=15, pady=15)
        log_container.pack(fill="both", expand=True)
        
        ttk.Label(log_container, text="LOG CONSOLE", style="Section.TLabel").pack(anchor="w", pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_container, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief="flat", font=("Consolas", 9.5), borderwidth=0, state="disabled")
        self.log_text.pack(fill="both", expand=True)
        
        # Redirect custom logs to widget
        self.log("System initialized. Ready.")

    def _on_type_change(self, event: Any = None) -> None:
        if self.type_var.get() == "LIMIT":
            self.price_label.grid()
            self.price_entry.grid()
            if not self.price_var.get():
                self.price_var.set("60000.0")
        else:
            self.price_label.grid_remove()
            self.price_entry.grid_remove()

    def log(self, msg: str, is_err: bool = False) -> None:
        timestamp = time.strftime("%H:%M:%S")
        prefix = "ERR" if is_err else "INFO"
        text_line = f"[{timestamp}] | {prefix:<4} | {msg}\n"
        
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, text_line)
        if is_err:
            # tag the last inserted line as error
            last_line_index = self.log_text.index("end-1c")
            start_index = f"{float(last_line_index) - 1.0}"
            self.log_text.tag_add("error", start_index, last_line_index)
            self.log_text.tag_config("error", foreground=ACCENT_RED)
        
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    def _init_client(self) -> None:
        api_key = self.api_key_var.get().strip()
        api_secret = self.api_secret_var.get().strip()
        
        try:
            self.client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
            if self.client.demo_mode:
                self.mode_lbl.configure(text="Offline Demo Mode", foreground=ACCENT_YELLOW)
                self.log("Connected in OFFLINE DEMO MODE. Responses will be simulated.")
            else:
                self.mode_lbl.configure(text="Testnet Live Mode", foreground=ACCENT_GREEN)
                self.log(f"Connected in LIVE MODE to {self.client.base_url}")
        except Exception as exc:
            self.log(f"Client Init Error: {exc}", is_err=True)
            self.mode_lbl.configure(text="Not Configured", foreground=ACCENT_RED)

    def _ping_testnet(self) -> None:
        self.ping_status_lbl.configure(text="Pinging...", foreground=TEXT_MUTED)
        self.ping_btn.configure(state="disabled")
        
        def run() -> None:
            ok = self.client.ping()
            self.root.after(0, self._ping_finished, ok)
            
        threading.Thread(target=run, daemon=True).start()

    def _ping_finished(self, ok: bool) -> None:
        self.ping_btn.configure(state="normal")
        if ok:
            self.ping_status_lbl.configure(text="ONLINE", foreground=ACCENT_GREEN)
            self.log("Ping successful. Connectivity verified.")
        else:
            self.ping_status_lbl.configure(text="OFFLINE", foreground=ACCENT_RED)
            self.log("Ping failed. Please check network connectivity or base URL.", is_err=True)

    def _place_order(self) -> None:
        symbol = self.symbol_var.get().strip().upper()
        side_val = self.side_var.get()
        type_val = self.type_var.get()
        
        try:
            qty = float(self.qty_var.get().strip())
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a numeric value.")
            return

        price = None
        if type_val == "LIMIT":
            try:
                price = float(self.price_var.get().strip())
            except ValueError:
                messagebox.showerror("Validation Error", "Limit Price must be a numeric value.")
                return

        # Build order request object
        try:
            order_req = OrderRequest(
                symbol=symbol,
                side=Side(side_val),
                order_type=OrderType(type_val),
                quantity=qty,
                price=price
            )
            order_req.validate()
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
            return
            
        self.order_btn.configure(state="disabled", text="PLACING ORDER...")
        self.log(f"Sending Order: {side_val} {qty} {symbol} @ {type_val}")
        
        def run() -> None:
            try:
                res = self.client.place_order(order_req)
                self.root.after(0, self._order_success, res)
            except Exception as exc:
                self.root.after(0, self._order_failure, exc)
                
        threading.Thread(target=run, daemon=True).start()

    def _order_success(self, response: dict) -> None:
        self.order_btn.configure(state="normal", text="PLACE ORDER")
        self.log(f"Order Accepted: orderId={response.get('orderId')} | status={response.get('status')}")
        
        details = "\n".join(f"  {k:<12}: {v}" for k, v in response.items() if k in ["orderId", "status", "symbol", "side", "type", "origQty", "executedQty", "avgPrice"])
        self.log(f"Response Details:\n{details}")
        messagebox.showinfo("Order Placed", f"Order {response.get('orderId')} was placed successfully!\nStatus: {response.get('status')}")

    def _order_failure(self, exc: Exception) -> None:
        self.order_btn.configure(state="normal", text="PLACE ORDER")
        self.log(f"Order Failed: {exc}", is_err=True)
        messagebox.showerror("Order Rejected", str(exc))

def main() -> None:
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
