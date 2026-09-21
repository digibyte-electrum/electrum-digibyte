"""DigiByte mainnet header difficulty rules.

This is a small, integer-only port of DigiByte Core's V1--V4 rules in
``src/pow.cpp``.  It deliberately takes the already validated header history
as input; difficulty must never be inferred from the candidate header alone.
"""

from typing import Sequence


POW_LIMIT = ((1 << 256) - 1) >> 20
MULTI_ALGO_HEIGHT = 145_000
ALWAYS_UPDATE_HEIGHT = 400_000
V4_HEIGHT = 1_430_000
NUM_ALGOS = 5
AVERAGING_INTERVAL = 10
AVERAGING_TARGET = 1_500
AVERAGING_TARGET_V4 = 750
MIN_TIMESPAN = 1_200
MAX_TIMESPAN = 2_100
MIN_TIMESPAN_V3 = 1_260
MAX_TIMESPAN_V3 = 1_620
MIN_TIMESPAN_V4 = 630
MAX_TIMESPAN_V4 = 810


def bits_to_target(bits: int) -> int:
    size = (bits >> 24) & 0xff
    mantissa = bits & 0x007fffff
    if size <= 3:
        target = mantissa >> (8 * (3 - size))
    else:
        target = mantissa << (8 * (size - 3))
    if bits & 0x00800000:
        raise ValueError("negative DigiByte target")
    if target == 0 or target > POW_LIMIT:
        raise ValueError("DigiByte target outside consensus range")
    return target


def target_to_bits(target: int) -> int:
    target = min(target, POW_LIMIT)
    raw = target.to_bytes(32, "big").lstrip(b"\0") or b"\0"
    size = len(raw)
    mantissa = int.from_bytes((raw + b"\0\0\0")[:3], "big")
    if mantissa & 0x00800000:
        size += 1
        mantissa >>= 8
    return (size << 24) | mantissa


def algorithm(version: int, height: int) -> int:
    # Core selects the era from pindexLast (the candidate height minus one),
    # so the boundary candidate itself still uses the preceding era.
    if height <= MULTI_ALGO_HEIGHT:
        return 1  # Scrypt was the sole mainnet algorithm.
    # Header version bits and Core's internal ALGO_* enum are different:
    # version 0 means Scrypt, while enum 0 means SHA256d.
    return {
        0: 1,   # Scrypt
        2: 0,   # SHA256d
        4: 2,   # Groestl
        6: 3,   # Skein
        8: 4,   # Qubit
        14: 7,  # OdoCrypt
    }.get((version >> 8) & 0x0f, -1)


def _median_time(headers: Sequence[dict], end: int) -> int:
    return sorted(h["timestamp"] for h in headers[max(0, end - 10):end + 1])[len(headers[max(0, end - 10):end + 1]) // 2]


def _height(header: dict, fallback: int) -> int:
    return header.get("block_height", fallback)


def _div_trunc_zero(value: int, divisor: int) -> int:
    """Match C++ integer division for signed values."""
    return value // divisor if value >= 0 else -((-value) // divisor)


def _same_algo(headers: Sequence[dict], before: int, algo: int):
    for i in range(before, -1, -1):
        if algorithm(headers[i]["version"], _height(headers[i], i)) == algo:
            yield i


def _at_height(headers: Sequence[dict], height: int) -> dict:
    base = _height(headers[0], 0)
    index = height - base
    if not 0 <= index < len(headers):
        raise ValueError("DigiByte difficulty context is incomplete")
    return headers[index]


def next_bits(headers: Sequence[dict], candidate: dict) -> int:
    """Return the exact expected compact target for ``candidate``.

    ``headers`` contains all headers from genesis through the candidate's
    predecessor, indexed by block height.
    """
    height = candidate.get("block_height", _height(headers[-1], len(headers) - 1) + 1) if headers else 0
    if height == 0:
        return target_to_bits(POW_LIMIT)
    last = headers[-1]
    algo = algorithm(candidate["version"], height)

    if height <= MULTI_ALGO_HEIGHT:
        interval = 1 if height >= 67_200 else 144
        if height % interval:
            return last["bits"]
        first_height = height - interval if height == interval else height - interval - 1
        first = _at_height(headers, first_height)
        timespan = last["timestamp"] - first["timestamp"]
        target_span = 60 if height >= 67_200 else 8_640
        if height >= 67_200:
            timespan = max(target_span - target_span // 4, min(target_span + target_span // 2, timespan))
        else:
            timespan = max(target_span // 4, min(target_span * 4, timespan))
        return target_to_bits(bits_to_target(last["bits"]) * timespan // target_span)

    # ``headers`` is a bounded rolling window, so the search bound is a
    # local list index even though each header retains its absolute height.
    same = list(_same_algo(headers, len(headers) - 1, algo))
    if not same:
        return target_to_bits(POW_LIMIT)
    previous_algo = same[0]
    if height <= ALWAYS_UPDATE_HEIGHT:
        if len(same) < AVERAGING_INTERVAL:
            return target_to_bits(POW_LIMIT)
        first = headers[same[AVERAGING_INTERVAL - 1]]
        timespan = headers[previous_algo]["timestamp"] - first["timestamp"]
        timespan = max(MIN_TIMESPAN, min(MAX_TIMESPAN, timespan))
        return target_to_bits(bits_to_target(headers[previous_algo]["bits"]) * timespan // AVERAGING_TARGET)

    if height <= V4_HEIGHT:
        first_height = height - 1 - NUM_ALGOS * AVERAGING_INTERVAL
        if first_height < 0:
            return target_to_bits(POW_LIMIT)
        first_index = first_height - _height(headers[0], 0)
        timespan = _median_time(headers, len(headers) - 1) - _median_time(headers, first_index)
        timespan = AVERAGING_TARGET + _div_trunc_zero(timespan - AVERAGING_TARGET, 6)
        timespan = max(MIN_TIMESPAN_V3, min(MAX_TIMESPAN_V3, timespan))
        target = bits_to_target(headers[previous_algo]["bits"]) * timespan // AVERAGING_TARGET
        adjustments = _height(headers[previous_algo], previous_algo) - (height - 1) + NUM_ALGOS - 1
        for _ in range(abs(adjustments)):
            target = target * (100 if adjustments > 0 else 104) // (104 if adjustments > 0 else 100)
        return target_to_bits(target)

    first_height = height - 1 - NUM_ALGOS * AVERAGING_INTERVAL
    if first_height < 0:
        return target_to_bits(POW_LIMIT)
    first_index = first_height - _height(headers[0], 0)
    timespan = _median_time(headers, len(headers) - 1) - _median_time(headers, first_index)
    timespan = AVERAGING_TARGET_V4 + _div_trunc_zero(timespan - AVERAGING_TARGET_V4, 4)
    timespan = max(MIN_TIMESPAN_V4, min(MAX_TIMESPAN_V4, timespan))
    target = bits_to_target(headers[previous_algo]["bits"]) * timespan // AVERAGING_TARGET_V4
    adjustments = _height(headers[previous_algo], previous_algo) + NUM_ALGOS - 1 - (height - 1)
    for _ in range(abs(adjustments)):
        target = target * (100 if adjustments > 0 else 104) // (104 if adjustments > 0 else 100)
    return target_to_bits(target)
