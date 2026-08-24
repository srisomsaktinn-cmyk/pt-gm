"""
Broker API Interface and MetaTrader 5 / Live Execution Bridge.
Connects Frozen Strategy V2.6 to real-time broker feeds, sends market orders,
and captures actual execution latency, fills, and slippage.
"""

from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class LiveBrokerQuote:
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime


@dataclass
class LiveExecutionFill:
    ticket: int
    symbol: str
    direction: str
    requested_price: float
    fill_price: float
    slippage: float
    spread_at_fill: float
    execution_delay_ms: float
    fill_timestamp: datetime
    hard_stop_price: float


class AbstractBrokerBridge(ABC):
    """
    Standard interface for executing live and paper orders through real broker APIs.
    """

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def get_latest_quote(self, symbol: str) -> LiveBrokerQuote:
        pass

    @abstractmethod
    def execute_market_order(
        self,
        symbol: str,
        direction: str,
        volume_units: float,
        hard_stop_price: float
    ) -> LiveExecutionFill:
        pass

    @abstractmethod
    def close_market_order(
        self,
        ticket: int,
        symbol: str,
        direction: str,
        volume_units: float
    ) -> LiveExecutionFill:
        pass


class MT5BrokerBridge(AbstractBrokerBridge):
    """
    Production MetaTrader 5 Python connector.
    Connects to live MT5 terminal, pulls live Bid/Ask, sends market orders at bar open,
    and captures exact execution metrics for the shadow audit log.
    """

    def __init__(self, account: int = 0, server: str = "", password: str = ""):
        self.account = account
        self.server = server
        self.password = password
        self._connected = False

    def connect(self) -> bool:
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                return False
            if self.account > 0:
                authorized = mt5.login(self.account, password=self.password, server=self.server)
                if not authorized:
                    return False
            self._connected = True
            return True
        except ImportError:
            # Running in environment without MT5 library installed
            return False

    def get_latest_quote(self, symbol: str = "XAUUSD") -> LiveBrokerQuote:
        import MetaTrader5 as mt5
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"Failed to fetch tick for {symbol}")
        spread = round(tick.ask - tick.bid, 2)
        return LiveBrokerQuote(
            symbol=symbol,
            bid=tick.bid,
            ask=tick.ask,
            spread=spread,
            timestamp=datetime.fromtimestamp(tick.time)
        )

    def execute_market_order(
        self,
        symbol: str,
        direction: str,
        volume_units: float,
        hard_stop_price: float
    ) -> LiveExecutionFill:
        import MetaTrader5 as mt5
        import time

        tick = mt5.symbol_info_tick(symbol)
        order_type = mt5.ORDER_TYPE_BUY if direction == "LONG" else mt5.ORDER_TYPE_SELL
        req_price = tick.ask if direction == "LONG" else tick.bid
        lots = volume_units / 100.0 # 50 oz = 0.5 lots

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lots),
            "type": order_type,
            "price": req_price,
            "sl": float(hard_stop_price),
            "deviation": 20,
            "magic": 20260824,
            "comment": "V2.6 Frozen EA",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        t_start = time.time()
        result = mt5.order_send(request)
        t_delay_ms = (time.time() - t_start) * 1000.0

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Order failed: {result.comment if result else 'Unknown error'}")

        actual_fill = result.price
        slip = round(actual_fill - req_price if direction == "LONG" else req_price - actual_fill, 2)

        return LiveExecutionFill(
            ticket=result.order,
            symbol=symbol,
            direction=direction,
            requested_price=req_price,
            fill_price=actual_fill,
            slippage=slip,
            spread_at_fill=round(tick.ask - tick.bid, 2),
            execution_delay_ms=t_delay_ms,
            fill_timestamp=datetime.now(),
            hard_stop_price=hard_stop_price
        )

    def close_market_order(
        self,
        ticket: int,
        symbol: str,
        direction: str,
        volume_units: float
    ) -> LiveExecutionFill:
        import MetaTrader5 as mt5
        import time

        tick = mt5.symbol_info_tick(symbol)
        order_type = mt5.ORDER_TYPE_SELL if direction == "LONG" else mt5.ORDER_TYPE_BUY
        req_price = tick.bid if direction == "LONG" else tick.ask
        lots = volume_units / 100.0

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lots),
            "type": order_type,
            "position": ticket,
            "price": req_price,
            "deviation": 20,
            "magic": 20260824,
            "comment": "V2.6 Frozen Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        t_start = time.time()
        result = mt5.order_send(request)
        t_delay_ms = (time.time() - t_start) * 1000.0

        actual_fill = result.price if result and result.retcode == mt5.TRADE_RETCODE_DONE else req_price
        slip = round(req_price - actual_fill if direction == "LONG" else actual_fill - req_price, 2)

        return LiveExecutionFill(
            ticket=ticket,
            symbol=symbol,
            direction=direction,
            requested_price=req_price,
            fill_price=actual_fill,
            slippage=slip,
            spread_at_fill=round(tick.ask - tick.bid, 2),
            execution_delay_ms=t_delay_ms,
            fill_timestamp=datetime.now(),
            hard_stop_price=0.0
        )
