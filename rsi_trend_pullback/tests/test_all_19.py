"""
Comprehensive Test Suite for RSI(14) Trend Pullback Re-entry Strategy V1.
Implements all 19 mandatory unit tests specified in the requirements.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from ..data.loader import Candle
from ..indicator.rsi import WilderRSI
from ..state_machine.states import StrategyState, SignalType, PositionSide
from ..state_machine.engine import RSIStateMachine
from ..strategy.rsi_strategy import RSIStrategyEngine
from ..execution.simulator import ExecutionConfig


def make_candles(close_prices: List[float], start_time: datetime = datetime(2023, 1, 1)) -> List[Candle]:
    """Helper to generate candle objects from a list of close prices."""
    candles = []
    t = start_time
    prev_close = close_prices[0] if close_prices else 100.0
    for idx, c in enumerate(close_prices):
        o = prev_close
        h = max(o, c) + 0.5
        l = min(o, c) - 0.5
        candles.append(Candle(timestamp=t, open=o, high=h, low=l, close=c, volume=100.0))
        prev_close = c
        t += timedelta(hours=1)
    return candles


# ── TEST 1: Bullish Trend Detection ──
def test_1_bullish_trend_detection():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 55.0)
    assert sm.current_state == StrategyState.IDLE
    sm.evaluate_bar(2, now + timedelta(hours=1), 61.5)
    assert sm.current_state == StrategyState.BULLISH_TREND, f"Expected BULLISH_TREND, got {sm.current_state}"


# ── TEST 2: Bearish Trend Detection ──
def test_2_bearish_trend_detection():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 45.0)
    assert sm.current_state == StrategyState.IDLE
    sm.evaluate_bar(2, now + timedelta(hours=1), 38.5)
    assert sm.current_state == StrategyState.BEARISH_TREND, f"Expected BEARISH_TREND, got {sm.current_state}"


# ── TEST 3: Bullish Pullback Detection ──
def test_3_bullish_pullback():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    assert sm.current_state == StrategyState.BULLISH_TREND
    sm.evaluate_bar(2, now + timedelta(hours=1), 55.0)
    assert sm.current_state == StrategyState.BULLISH_TREND
    # Cross below 50 while remaining > 40
    sm.evaluate_bar(3, now + timedelta(hours=2), 48.0)
    assert sm.current_state == StrategyState.BULLISH_PULLBACK, f"Expected BULLISH_PULLBACK, got {sm.current_state}"


# ── TEST 4: Bearish Pullback Detection ──
def test_4_bearish_pullback():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 35.0)
    assert sm.current_state == StrategyState.BEARISH_TREND
    sm.evaluate_bar(2, now + timedelta(hours=1), 45.0)
    assert sm.current_state == StrategyState.BEARISH_TREND
    # Cross above 50 while remaining < 60
    sm.evaluate_bar(3, now + timedelta(hours=2), 52.0)
    assert sm.current_state == StrategyState.BEARISH_PULLBACK, f"Expected BEARISH_PULLBACK, got {sm.current_state}"


# ── TEST 5: Long Trigger ──
def test_5_long_trigger():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 48.0)
    assert sm.current_state == StrategyState.BULLISH_PULLBACK
    
    # Cross back above 50
    sig = sm.evaluate_bar(3, now + timedelta(hours=2), 52.0)
    assert sm.current_state == StrategyState.LONG_ENTRY
    assert sig is not None
    assert sig.signal_type == SignalType.LONG_ENTRY_SIGNAL


# ── TEST 6: Short Trigger ──
def test_6_short_trigger():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 35.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 52.0)
    assert sm.current_state == StrategyState.BEARISH_PULLBACK
    
    # Cross back below 50
    sig = sm.evaluate_bar(3, now + timedelta(hours=2), 48.0)
    assert sm.current_state == StrategyState.SHORT_ENTRY
    assert sig is not None
    assert sig.signal_type == SignalType.SHORT_ENTRY_SIGNAL


# ── TEST 7: Bullish Invalidation ──
def test_7_bullish_invalidation():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 48.0)
    assert sm.current_state == StrategyState.BULLISH_PULLBACK
    
    # Invalidation: drops < 40 -> flips directly to BEARISH_TREND
    sig = sm.evaluate_bar(3, now + timedelta(hours=2), 38.0)
    assert sm.current_state == StrategyState.BEARISH_TREND
    assert sig is None  # Invalidation does not emit entry signal


# ── TEST 8: Bearish Invalidation ──
def test_8_bearish_invalidation():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 35.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 52.0)
    assert sm.current_state == StrategyState.BEARISH_PULLBACK
    
    # Invalidation: rises > 60 -> flips directly to BULLISH_TREND
    sig = sm.evaluate_bar(3, now + timedelta(hours=2), 62.0)
    assert sm.current_state == StrategyState.BULLISH_TREND
    assert sig is None


# ── TEST 9: One-Trade-Per-Cycle Rule ──
def test_9_one_trade_per_cycle():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 48.0)
    sm.evaluate_bar(3, now + timedelta(hours=2), 52.0)
    assert sm.current_state == StrategyState.LONG_ENTRY
    
    # Order executes at next bar open -> notify TRADED
    sm.notify_order_executed(4, now + timedelta(hours=3))
    assert sm.current_state == StrategyState.BULLISH_TRADED
    
    # Second pullback in same bullish cycle
    sm.evaluate_bar(4, now + timedelta(hours=3), 48.0)
    assert sm.current_state == StrategyState.BULLISH_TRADED
    sig2 = sm.evaluate_bar(5, now + timedelta(hours=4), 52.0)
    assert sm.current_state == StrategyState.BULLISH_TRADED
    assert sig2 is None, "Subsequent pullback in same cycle must NOT generate another trade"


# ── TEST 10: Multi-Level Jump (62 -> 38) ──
def test_10_multi_level_jump():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 62.0)
    assert sm.current_state == StrategyState.BULLISH_TREND
    
    # Jump directly from 62.0 to 38.0
    sig = sm.evaluate_bar(2, now + timedelta(hours=1), 38.0)
    # Priority 1: RSI < 40 fires immediately -> flips to BEARISH_TREND, no pullback
    assert sm.current_state == StrategyState.BEARISH_TREND
    assert sig is None


# ── TEST 11: Boundary RSI = 60.00 ──
def test_11_boundary_rsi_60():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 60.00)
    assert sm.current_state == StrategyState.IDLE, "RSI == 60.00 must NOT trigger Bullish Trend (> 60 strict)"


# ── TEST 12: Boundary RSI = 50.00 ──
def test_12_boundary_rsi_50():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    # From 55 to 50.00 exactly is NOT a strict cross below 50
    sm.evaluate_bar(2, now + timedelta(hours=1), 50.00)
    assert sm.current_state == StrategyState.BULLISH_TREND


# ── TEST 13: Boundary RSI = 40.00 ──
def test_13_boundary_rsi_40():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 40.00)
    assert sm.current_state == StrategyState.IDLE, "RSI == 40.00 must NOT trigger Bearish Trend (< 40 strict)"


# ── TEST 14: Entry Executes on Next Candle Open ──
def test_14_entry_executes_on_next_candle_open():
    engine = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    # Manually constructed prices that trigger RSI:
    # Warmup 15 bars, then surge > 60, pull down < 50, pull up > 50
    prices = [100.0 + (i * 0.1) for i in range(15)] + [
        105.0, 110.0, 115.0, 120.0, # Push RSI > 60
        116.0, 112.0, 108.0,       # Pullback < 50
        113.0, 118.0, 122.0,       # Cross > 50 (trigger)
        125.0, 128.0               # Next bars
    ]
    candles = make_candles(prices)
    engine.run_backtest(candles)

    # Check signal and execution timing
    assert len(engine._signals_history) > 0
    first_sig = engine._signals_history[0]
    assert first_sig.signal_type == SignalType.LONG_ENTRY_SIGNAL
    
    assert len(engine.closed_trades) > 0 or engine.active_trade is not None
    trade = engine.closed_trades[0] if engine.closed_trades else engine.active_trade
    assert trade is not None
    assert trade.entry_bar_index == first_sig.bar_index + 1
    assert trade.entry_timestamp == candles[first_sig.bar_index + 1].timestamp
    assert trade.entry_price == candles[first_sig.bar_index + 1].open


# ── TEST 15: Exit Executes on Next Candle Open ──
def test_15_exit_executes_on_next_candle_open():
    engine = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    prices = [100.0 + (i * 0.1) for i in range(15)] + [
        105.0, 110.0, 115.0, 120.0, # Push RSI > 60
        116.0, 112.0, 108.0,       # Pullback < 50
        113.0, 118.0,              # Trigger Long
        119.0, 115.0, 105.0, 95.0, 85.0, 75.0 # Crash RSI < 40 (Exit signal)
    ]
    candles = make_candles(prices)
    engine.run_backtest(candles)

    assert len(engine.closed_trades) == 1
    closed_trade = engine.closed_trades[0]
    assert closed_trade.exit_signal_bar_index is not None
    assert closed_trade.exit_bar_index == closed_trade.exit_signal_bar_index + 1
    assert closed_trade.exit_timestamp == candles[closed_trade.exit_bar_index].timestamp
    assert closed_trade.exit_price == candles[closed_trade.exit_bar_index].open


# ── TEST 16: No Look-Ahead Verification ──
def test_16_no_look_ahead():
    # Run backtest on 20 bars
    prices_base = [100.0 + (i * 0.5) for i in range(25)]
    candles_base = make_candles(prices_base)
    
    engine1 = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine1.run_backtest(candles_base)
    states_at_15 = [t.current_state for t in engine1.transition_history if t.bar_index <= 15]

    # Mutate bars 16..24 drastically (e.g. massive market crash)
    prices_mutated = prices_base[:16] + [50.0 - (i * 2.0) for i in range(9)]
    candles_mutated = make_candles(prices_mutated)

    engine2 = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine2.run_backtest(candles_mutated)
    states_at_15_mutated = [t.current_state for t in engine2.transition_history if t.bar_index <= 15]

    # States up to bar 15 must be 100% identical!
    assert states_at_15 == states_at_15_mutated, "Look-ahead detected: Future bars changed past states!"


# ── TEST 17: Initial RSI Warm-Up ──
def test_17_initial_rsi_warmup():
    engine = RSIStrategyEngine()
    prices = [100.0 + i for i in range(14)]
    candles = make_candles(prices)
    engine.run_backtest(candles)

    # First 13 bars must have RSI = None
    for i in range(13):
        assert engine.rsi_series[i] is None, f"Bar {i} should be None during warmup"
    assert engine.state_machine.current_state == StrategyState.IDLE
    assert len(engine._signals_history) == 0


# ── TEST 18: State Transition After Trade (LONG_ENTRY -> BULLISH_TRADED) ──
def test_18_state_transition_after_trade():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 48.0)
    sm.evaluate_bar(3, now + timedelta(hours=2), 52.0)
    assert sm.current_state == StrategyState.LONG_ENTRY
    
    sm.notify_order_executed(4, now + timedelta(hours=3))
    assert sm.current_state == StrategyState.BULLISH_TRADED


# ── TEST 19: State Transition After Trend Reversal ──
def test_19_state_transition_after_trend_reversal():
    sm = RSIStateMachine()
    now = datetime(2023, 1, 1)
    sm.evaluate_bar(1, now, 65.0)
    sm.evaluate_bar(2, now + timedelta(hours=1), 48.0)
    sm.evaluate_bar(3, now + timedelta(hours=2), 52.0)
    sm.notify_order_executed(4, now + timedelta(hours=3))
    assert sm.current_state == StrategyState.BULLISH_TRADED

    # In BULLISH_TRADED, RSI drops < 40
    sig = sm.evaluate_bar(5, now + timedelta(hours=4), 38.0)
    assert sig is not None
    assert sig.signal_type == SignalType.LONG_EXIT_SIGNAL
    assert sm.current_state == StrategyState.BEARISH_TREND, f"Expected BEARISH_TREND, got {sm.current_state}"


def run_all_unit_tests() -> bool:
    tests = [
        ("Test 1: Bullish Trend Detection", test_1_bullish_trend_detection),
        ("Test 2: Bearish Trend Detection", test_2_bearish_trend_detection),
        ("Test 3: Bullish Pullback", test_3_bullish_pullback),
        ("Test 4: Bearish Pullback", test_4_bearish_pullback),
        ("Test 5: Long Trigger", test_5_long_trigger),
        ("Test 6: Short Trigger", test_6_short_trigger),
        ("Test 7: Bullish Invalidation", test_7_bullish_invalidation),
        ("Test 8: Bearish Invalidation", test_8_bearish_invalidation),
        ("Test 9: One-Trade-Per-Cycle", test_9_one_trade_per_cycle),
        ("Test 10: Multi-Level Jump (62 -> 38)", test_10_multi_level_jump),
        ("Test 11: Boundary RSI = 60", test_11_boundary_rsi_60),
        ("Test 12: Boundary RSI = 50", test_12_boundary_rsi_50),
        ("Test 13: Boundary RSI = 40", test_13_boundary_rsi_40),
        ("Test 14: Entry on Next Candle Open", test_14_entry_executes_on_next_candle_open),
        ("Test 15: Exit on Next Candle Open", test_15_exit_executes_on_next_candle_open),
        ("Test 16: No Look-Ahead Verification", test_16_no_look_ahead),
        ("Test 17: Initial RSI Warm-Up", test_17_initial_rsi_warmup),
        ("Test 18: State Transition After Trade", test_18_state_transition_after_trade),
        ("Test 19: State Transition After Trend Reversal", test_19_state_transition_after_trend_reversal),
    ]

    all_passed = True
    print("=" * 70)
    print("RUNNING UNIT TEST SUITE: RSI(14) TREND PULLBACK RE-ENTRY V1")
    print("=" * 70)
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            all_passed = False
            print(f"[FAIL] {name} -> Error: {str(e)}")

    print("=" * 70)
    if all_passed:
        print("ALL 19 UNIT TESTS PASSED PERFECTLY!")
    else:
        print("SOME UNIT TESTS FAILED!")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    run_all_unit_tests()
