"""Helpers for hashing and comparing marshal byte streams."""

from __future__ import annotations

import hashlib
import marshal
import math
from typing import Any


def marshal_bytes(value: Any) -> bytes:
    """Serialize a value using the current default marshal format."""
    return marshal.dumps(value)


def sha256_of_marshal(value: Any) -> str:
    """Return the SHA-256 hash of a value's marshal byte stream."""
    return hashlib.sha256(marshal_bytes(value)).hexdigest()


def equivalent(expected: Any, actual: Any) -> bool:
    """Compare values after a marshal round trip.

    The function handles special cases where regular equality is not enough,
    such as NaN values and bytearray being loaded as bytes.
    """
    if expected is StopIteration:
        return actual is StopIteration
    if isinstance(expected, bytearray):
        return actual == bytes(expected)
    if isinstance(expected, float):
        if math.isnan(expected):
            return isinstance(actual, float) and math.isnan(actual)
        return expected == actual and _same_float_sign(expected, actual)
    if isinstance(expected, complex):
        return _float_component_equal(expected.real, actual.real) and (
            _float_component_equal(expected.imag, actual.imag)
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and _sequence_equivalent(expected, actual)
    if isinstance(expected, tuple):
        return isinstance(actual, tuple) and _sequence_equivalent(expected, actual)
    if isinstance(expected, dict):
        return isinstance(actual, dict) and _dict_equivalent(expected, actual)
    if isinstance(expected, (set, frozenset)):
        return type(expected) is type(actual) and expected == actual
    return expected == actual


def _sequence_equivalent(expected: Any, actual: Any) -> bool:
    if len(expected) != len(actual):
        return False
    return all(equivalent(left, right) for left, right in zip(expected, actual))


def _dict_equivalent(expected: dict[Any, Any], actual: dict[Any, Any]) -> bool:
    if set(expected.keys()) != set(actual.keys()):
        return False
    return all(equivalent(expected[key], actual[key]) for key in expected)


def _float_component_equal(left: float, right: float) -> bool:
    if math.isnan(left):
        return math.isnan(right)
    return left == right and _same_float_sign(left, right)


def _same_float_sign(left: float, right: float) -> bool:
    if left == 0.0 and right == 0.0:
        return math.copysign(1.0, left) == math.copysign(1.0, right)
    return True
