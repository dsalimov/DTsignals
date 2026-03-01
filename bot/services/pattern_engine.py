import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Tuple
from scipy.signal import argrelextrema

logger = logging.getLogger(__name__)


def find_peaks_and_troughs(prices: np.ndarray, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Find local peaks and troughs."""
    peaks = argrelextrema(prices, np.greater_equal, order=order)[0]
    troughs = argrelextrema(prices, np.less_equal, order=order)[0]
    return peaks, troughs


def detect_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Head & Shoulders pattern."""
    if len(df) < 30:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values
    peaks, troughs = find_peaks_and_troughs(close, order=5)

    if len(peaks) < 3 or len(troughs) < 2:
        return {"detected": False}

    for i in range(len(peaks) - 2):
        left_shoulder = close[peaks[i]]
        head = close[peaks[i + 1]]
        right_shoulder = close[peaks[i + 2]]

        if head <= left_shoulder or head <= right_shoulder:
            continue

        shoulder_diff = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder)
        if shoulder_diff > 0.08:
            continue

        relevant_troughs = [t for t in troughs if peaks[i] < t < peaks[i + 2]]
        if len(relevant_troughs) < 2:
            continue

        neckline = np.mean([close[relevant_troughs[0]], close[relevant_troughs[-1]]])

        left_vol = np.mean(volume[max(0, peaks[i] - 3): peaks[i] + 3])
        right_vol = np.mean(volume[max(0, peaks[i + 2] - 3): peaks[i + 2] + 3])
        vol_confirmed = bool(right_vol < left_vol)

        confidence = 65
        if vol_confirmed:
            confidence += 10
        if shoulder_diff < 0.04:
            confidence += 7

        measured_move = head - neckline
        target = neckline - measured_move

        return {
            "detected": True,
            "pattern": "Head & Shoulders",
            "bias": "bearish",
            "confidence": min(confidence, 92),
            "neckline": round(float(neckline), 2),
            "target": round(float(target), 2),
            "invalidation": round(float(head) * 1.02, 2),
            "measured_move": round(float(measured_move), 2),
            "vol_confirmed": vol_confirmed,
        }

    return {"detected": False}


def detect_inverse_head_and_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Inverse Head & Shoulders pattern."""
    if len(df) < 30:
        return {"detected": False}

    close = df["Close"].values
    peaks, troughs = find_peaks_and_troughs(close, order=5)

    if len(troughs) < 3:
        return {"detected": False}

    for i in range(len(troughs) - 2):
        left_shoulder = close[troughs[i]]
        head = close[troughs[i + 1]]
        right_shoulder = close[troughs[i + 2]]

        if head >= left_shoulder or head >= right_shoulder:
            continue

        shoulder_diff = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder)
        if shoulder_diff > 0.08:
            continue

        relevant_peaks = [p for p in peaks if troughs[i] < p < troughs[i + 2]]
        if len(relevant_peaks) < 2:
            continue

        neckline = np.mean([close[relevant_peaks[0]], close[relevant_peaks[-1]]])
        measured_move = neckline - head
        target = neckline + measured_move

        confidence = 65
        if shoulder_diff < 0.04:
            confidence += 10

        return {
            "detected": True,
            "pattern": "Inverse Head & Shoulders",
            "bias": "bullish",
            "confidence": min(confidence, 90),
            "neckline": round(float(neckline), 2),
            "target": round(float(target), 2),
            "invalidation": round(float(head) * 0.98, 2),
            "measured_move": round(float(measured_move), 2),
        }

    return {"detected": False}


def detect_double_top(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Double Top pattern."""
    if len(df) < 20:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values
    peaks, troughs = find_peaks_and_troughs(close, order=5)

    if len(peaks) < 2:
        return {"detected": False}

    for i in range(len(peaks) - 1):
        peak1 = close[peaks[i]]
        peak2 = close[peaks[i + 1]]

        price_diff = abs(peak1 - peak2) / max(peak1, peak2)
        if price_diff > 0.04:
            continue

        between_troughs = [t for t in troughs if peaks[i] < t < peaks[i + 1]]
        if not between_troughs:
            continue

        neckline = float(min(close[between_troughs]))
        measured_move = max(peak1, peak2) - neckline
        target = neckline - measured_move

        vol1 = np.mean(volume[max(0, peaks[i] - 3): peaks[i] + 3])
        vol2 = np.mean(volume[max(0, peaks[i + 1] - 3): peaks[i + 1] + 3])
        vol_confirmed = bool(vol2 < vol1)

        confidence = 68
        if price_diff < 0.02:
            confidence += 8
        if vol_confirmed:
            confidence += 7

        return {
            "detected": True,
            "pattern": "Double Top",
            "bias": "bearish",
            "confidence": min(confidence, 88),
            "neckline": round(neckline, 2),
            "target": round(float(target), 2),
            "invalidation": round(float(max(peak1, peak2)) * 1.02, 2),
            "vol_confirmed": vol_confirmed,
        }

    return {"detected": False}


def detect_double_bottom(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Double Bottom pattern."""
    if len(df) < 20:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values
    peaks, troughs = find_peaks_and_troughs(close, order=5)

    if len(troughs) < 2:
        return {"detected": False}

    for i in range(len(troughs) - 1):
        trough1 = close[troughs[i]]
        trough2 = close[troughs[i + 1]]

        price_diff = abs(trough1 - trough2) / max(trough1, trough2)
        if price_diff > 0.04:
            continue

        between_peaks = [p for p in peaks if troughs[i] < p < troughs[i + 1]]
        if not between_peaks:
            continue

        neckline = float(max(close[between_peaks]))
        measured_move = neckline - min(trough1, trough2)
        target = neckline + measured_move

        vol1 = np.mean(volume[max(0, troughs[i] - 3): troughs[i] + 3])
        vol2 = np.mean(volume[max(0, troughs[i + 1] - 3): troughs[i + 1] + 3])
        vol_confirmed = bool(vol2 > vol1)

        confidence = 68
        if price_diff < 0.02:
            confidence += 8
        if vol_confirmed:
            confidence += 7

        return {
            "detected": True,
            "pattern": "Double Bottom",
            "bias": "bullish",
            "confidence": min(confidence, 88),
            "neckline": round(neckline, 2),
            "target": round(float(target), 2),
            "invalidation": round(float(min(trough1, trough2)) * 0.98, 2),
            "vol_confirmed": vol_confirmed,
        }

    return {"detected": False}


def detect_ascending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Ascending Triangle."""
    if len(df) < 20:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values
    peaks, troughs = find_peaks_and_troughs(close, order=4)

    if len(peaks) < 3 or len(troughs) < 3:
        return {"detected": False}

    recent_peaks = peaks[-3:]
    peak_prices = close[recent_peaks]
    peak_std = np.std(peak_prices) / np.mean(peak_prices)

    if peak_std > 0.03:
        return {"detected": False}

    recent_troughs = troughs[-3:]
    trough_prices = close[recent_troughs]

    if not np.all(np.diff(trough_prices) > 0):
        return {"detected": False}

    resistance = float(np.mean(peak_prices))
    current_price = float(close[-1])
    near_breakout = (current_price / resistance) > 0.97

    measured_move = resistance - float(trough_prices[0])
    target = resistance + measured_move

    vol_recent = np.mean(volume[-5:])
    vol_earlier = np.mean(volume[-20:-5])
    vol_expanding = bool(vol_recent > vol_earlier * 1.2)

    confidence = 70
    if near_breakout:
        confidence += 10
    if vol_expanding:
        confidence += 8
    if peak_std < 0.015:
        confidence += 5

    return {
        "detected": True,
        "pattern": "Ascending Triangle",
        "bias": "bullish",
        "confidence": min(confidence, 90),
        "resistance": round(resistance, 2),
        "target": round(float(target), 2),
        "invalidation": round(float(trough_prices[-1]) * 0.97, 2),
        "breakout_imminent": near_breakout,
        "vol_confirmed": vol_expanding,
    }


def detect_descending_triangle(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Descending Triangle."""
    if len(df) < 20:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values
    peaks, troughs = find_peaks_and_troughs(close, order=4)

    if len(peaks) < 3 or len(troughs) < 3:
        return {"detected": False}

    recent_troughs = troughs[-3:]
    trough_prices = close[recent_troughs]
    trough_std = np.std(trough_prices) / np.mean(trough_prices)

    if trough_std > 0.03:
        return {"detected": False}

    recent_peaks = peaks[-3:]
    peak_prices = close[recent_peaks]

    if not np.all(np.diff(peak_prices) < 0):
        return {"detected": False}

    support = float(np.mean(trough_prices))
    measured_move = float(peak_prices[0]) - support
    target = support - measured_move

    return {
        "detected": True,
        "pattern": "Descending Triangle",
        "bias": "bearish",
        "confidence": 68,
        "support": round(support, 2),
        "target": round(float(target), 2),
        "invalidation": round(float(peak_prices[-1]) * 1.02, 2),
    }


def detect_cup_and_handle(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Cup & Handle pattern."""
    if len(df) < 50:
        return {"detected": False}

    close = df["Close"].values

    handle_len = max(int(len(close) * 0.15), 5)
    cup_data = close[:-handle_len]
    handle_data = close[-handle_len:]

    cup_third = max(len(cup_data) // 3, 1)
    cup_left = float(np.max(cup_data[:cup_third]))
    cup_bottom = float(np.min(cup_data))
    cup_right = float(np.max(cup_data[-cup_third:]))

    rim_diff = abs(cup_left - cup_right) / max(cup_left, cup_right)
    if rim_diff > 0.08:
        return {"detected": False}

    cup_depth = (max(cup_left, cup_right) - cup_bottom) / max(cup_left, cup_right)
    if not 0.10 < cup_depth < 0.55:
        return {"detected": False}

    handle_max = float(np.max(handle_data))
    handle_min = float(np.min(handle_data))
    handle_depth = (handle_max - handle_min) / max(cup_left, cup_right)
    if handle_depth > cup_depth * 0.5:
        return {"detected": False}

    resistance = max(cup_left, cup_right)
    measured_move = resistance - cup_bottom
    target = resistance + measured_move

    current_price = float(close[-1])
    near_breakout = (current_price / resistance) > 0.96

    confidence = 72
    if rim_diff < 0.04:
        confidence += 8
    if near_breakout:
        confidence += 10
    if 0.25 < cup_depth < 0.45:
        confidence += 5

    return {
        "detected": True,
        "pattern": "Cup & Handle",
        "bias": "bullish",
        "confidence": min(confidence, 90),
        "resistance": round(resistance, 2),
        "cup_bottom": round(cup_bottom, 2),
        "target": round(float(target), 2),
        "invalidation": round(float(handle_min) * 0.97, 2),
        "breakout_imminent": near_breakout,
    }


def detect_flag(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect Bull/Bear Flag pattern."""
    if len(df) < 15:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values

    pole_period = min(10, len(close) // 3)
    handle_len = max(int(len(close) * 0.25), 3)
    pole_end = len(close) - handle_len
    pole_start = pole_end - pole_period

    if pole_start < 0:
        return {"detected": False}

    pole_move = (close[pole_end] - close[pole_start]) / close[pole_start] * 100

    if abs(pole_move) < 5:
        return {"detected": False}

    flag_data = close[pole_end:]
    if len(flag_data) < 3:
        return {"detected": False}

    flag_range = (max(flag_data) - min(flag_data)) / abs(close[pole_end]) * 100

    if flag_range > abs(pole_move) * 0.5:
        return {"detected": False}

    is_bull_flag = pole_move > 0
    measured_move = abs(close[pole_end] - close[pole_start])

    if is_bull_flag:
        target = float(close[-1]) + measured_move
        invalidation = float(min(flag_data)) * 0.98
        bias = "bullish"
        pattern = "Bull Flag"
    else:
        target = float(close[-1]) - measured_move
        invalidation = float(max(flag_data)) * 1.02
        bias = "bearish"
        pattern = "Bear Flag"

    vol_pole = np.mean(volume[pole_start:pole_end])
    vol_flag = np.mean(volume[pole_end:])
    vol_confirmed = bool(vol_flag < vol_pole * 0.7)

    confidence = 70
    if vol_confirmed:
        confidence += 10
    if flag_range < abs(pole_move) * 0.3:
        confidence += 8

    return {
        "detected": True,
        "pattern": pattern,
        "bias": bias,
        "confidence": min(confidence, 88),
        "pole_move_pct": round(float(pole_move), 1),
        "target": round(target, 2),
        "invalidation": round(invalidation, 2),
        "vol_confirmed": vol_confirmed,
    }


def detect_breakout(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect breakout from consolidation."""
    if len(df) < 20:
        return {"detected": False}

    close = df["Close"].values
    volume = df["Volume"].values

    consolidation = close[-20:-3]
    resistance = float(np.max(consolidation))
    support = float(np.min(consolidation))
    range_pct = (resistance - support) / support * 100

    if range_pct > 20:
        return {"detected": False}

    current_price = float(close[-1])

    if current_price > resistance * 1.02:
        vol_breakout = np.mean(volume[-3:])
        vol_avg = np.mean(volume[-20:-3])
        vol_ratio = float(vol_breakout / vol_avg) if vol_avg > 0 else 1.0
        vol_confirmed = bool(vol_ratio > 1.5)

        measured_move = resistance - support
        target = resistance + measured_move

        confidence = 65
        if vol_confirmed:
            confidence += 15
        if current_price > resistance * 1.03:
            confidence += 7

        return {
            "detected": True,
            "pattern": "Breakout",
            "bias": "bullish",
            "confidence": min(confidence, 90),
            "resistance": round(resistance, 2),
            "target": round(float(target), 2),
            "invalidation": round(support, 2),
            "vol_ratio": round(vol_ratio, 1),
            "vol_confirmed": vol_confirmed,
        }

    if current_price < support * 0.98:
        vol_breakdown = np.mean(volume[-3:])
        vol_avg = np.mean(volume[-20:-3])
        vol_ratio = float(vol_breakdown / vol_avg) if vol_avg > 0 else 1.0

        measured_move = resistance - support
        target = support - measured_move

        confidence = 65
        if vol_ratio > 1.5:
            confidence += 15

        return {
            "detected": True,
            "pattern": "Breakdown",
            "bias": "bearish",
            "confidence": min(confidence, 88),
            "support": round(support, 2),
            "target": round(float(target), 2),
            "invalidation": round(resistance, 2),
            "vol_ratio": round(vol_ratio, 1),
            "vol_confirmed": bool(vol_ratio > 1.5),
        }

    return {"detected": False}


def detect_unusual_volume(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect unusual volume spikes."""
    if len(df) < 20:
        return {"detected": False}

    volume = df["Volume"].values
    close = df["Close"].values

    avg_vol = float(np.mean(volume[-20:-1]))
    current_vol = float(volume[-1])
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

    if vol_ratio < 2.0:
        return {"detected": False}

    price_change = (close[-1] - close[-2]) / close[-2] * 100

    return {
        "detected": True,
        "pattern": "Unusual Volume",
        "bias": "bullish" if price_change > 0 else "bearish",
        "confidence": min(50 + int(vol_ratio * 5), 90),
        "vol_ratio": round(vol_ratio, 1),
        "price_change_pct": round(float(price_change), 2),
        "avg_volume": int(avg_vol),
        "current_volume": int(current_vol),
    }


# Pattern detection dispatcher
PATTERNS = {
    "h&s": detect_head_and_shoulders,
    "head_shoulders": detect_head_and_shoulders,
    "inverse_hs": detect_inverse_head_and_shoulders,
    "double_top": detect_double_top,
    "double_bottom": detect_double_bottom,
    "ascending_triangle": detect_ascending_triangle,
    "triangle": detect_ascending_triangle,
    "descending_triangle": detect_descending_triangle,
    "cup_handle": detect_cup_and_handle,
    "cup": detect_cup_and_handle,
    "flag": detect_flag,
    "bull_flag": detect_flag,
    "breakout": detect_breakout,
    "unusual_volume": detect_unusual_volume,
}


def detect_all_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Run all pattern detectors and return detected results sorted by confidence."""
    results = []
    detectors = [
        detect_breakout,
        detect_unusual_volume,
        detect_double_top,
        detect_double_bottom,
        detect_head_and_shoulders,
        detect_inverse_head_and_shoulders,
        detect_ascending_triangle,
        detect_flag,
        detect_cup_and_handle,
    ]
    for detector in detectors:
        try:
            result = detector(df)
            if result.get("detected"):
                results.append(result)
        except Exception:
            continue
    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return results


def detect_pattern(pattern_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Detect a specific pattern by name."""
    key = pattern_name.lower().replace(" ", "_").replace("-", "_")
    detector = PATTERNS.get(key)
    if detector:
        return detector(df)
    all_results = detect_all_patterns(df)
    return all_results[0] if all_results else {"detected": False}
