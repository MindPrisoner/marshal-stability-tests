"""Representative marshal test cases.

The cases are selected with black-box testing techniques: equivalence
partitioning, boundary value analysis, and deterministic fuzzing support.
Only standard-library modules are used.
"""

from __future__ import annotations

import marshal
import math
import random
import struct
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarshalCase:
    """A named input value used by the test suite."""

    label: str
    value: Any


def nan_from_bits(bits: int) -> float:
    """Create a float from its IEEE-754 bit pattern."""
    return struct.unpack(">d", bits.to_bytes(8, "big"))[0]


def stable_cases() -> list[MarshalCase]:
    """Return deterministic cases covering supported marshal types."""
    cases = [
        MarshalCase("none", None),
        MarshalCase("ellipsis", Ellipsis),
        MarshalCase("stop_iteration", StopIteration),
        MarshalCase("bool_true", True),
        MarshalCase("bool_false", False),
        MarshalCase("int_zero", 0),
        MarshalCase("int_minus_one", -1),
        MarshalCase("int_32_bit_min", -(2**31)),
        MarshalCase("int_32_bit_max", 2**31 - 1),
        MarshalCase("int_64_bit_min", -(2**63)),
        MarshalCase("int_64_bit_max", 2**63 - 1),
        MarshalCase("int_big", 2**100 + 12345),
        MarshalCase("float_zero", 0.0),
        MarshalCase("float_negative_zero", -0.0),
        MarshalCase("float_small", 1.5),
        MarshalCase("float_inf", math.inf),
        MarshalCase("float_negative_inf", -math.inf),
        MarshalCase("float_nan_canonical", nan_from_bits(0x7FF8000000000000)),
        MarshalCase("float_nan_payload", nan_from_bits(0x7FF8000000000001)),
        MarshalCase("complex_regular", complex(1.25, -2.5)),
        MarshalCase("complex_inf_nan", complex(math.inf, math.nan)),
        MarshalCase("str_empty", ""),
        MarshalCase("str_one_char", "a"),
        MarshalCase("str_255_chars", "x" * 255),
        MarshalCase("str_256_chars", "x" * 256),
        MarshalCase("str_unicode", "marshal 測試 🚀"),
        MarshalCase("bytes_empty", b""),
        MarshalCase("bytes_binary", bytes(range(256))),
        MarshalCase("bytearray_binary", bytearray(range(16))),
        MarshalCase("tuple_empty", ()),
        MarshalCase("tuple_nested", (1, "two", (3, 4), None)),
        MarshalCase("list_empty", []),
        MarshalCase("list_nested", [1, "two", [3, 4], None]),
        MarshalCase("dict_empty", {}),
        MarshalCase("dict_ordered", {"a": 1, "b": [2, 3], "c": None}),
        MarshalCase("set_empty", set()),
        MarshalCase("set_strings", {"apple", "banana", "cherry", "date"}),
        MarshalCase("frozenset_strings", frozenset({"apple", "banana", "cherry"})),
        MarshalCase("large_list_5000", list(range(5000))),
        MarshalCase("large_bytes_4096", b"z" * 4096),
    ]
    if marshal.version >= 5:
        cases.append(MarshalCase("slice_object", slice(1, 20, 3)))
    return cases


def cyclic_list_case() -> list[Any]:
    """Return a recursive list that contains itself."""
    recursive: list[Any] = []
    recursive.append(recursive)
    return recursive


def fuzz_values(seed: int = 12345, count: int = 100) -> list[Any]:
    """Create deterministic random values using supported marshal types."""
    rng = random.Random(seed)

    def primitive() -> Any:
        choice = rng.randrange(8)
        if choice == 0:
            return rng.randint(-(2**40), 2**40)
        if choice == 1:
            return rng.choice([True, False, None, Ellipsis])
        if choice == 2:
            return rng.choice([0.0, -0.0, 1.25, -2.5, math.inf, -math.inf])
        if choice == 3:
            return complex(rng.randint(-5, 5), rng.randint(-5, 5))
        if choice == 4:
            return "s" + str(rng.randint(0, 9999))
        if choice == 5:
            return bytes(rng.randrange(256) for _ in range(rng.randrange(8)))
        if choice == 6:
            return ()
        return []

    def value(depth: int) -> Any:
        if depth <= 0:
            return primitive()
        choice = rng.randrange(5)
        if choice == 0:
            return [value(depth - 1) for _ in range(rng.randrange(4))]
        if choice == 1:
            return tuple(value(depth - 1) for _ in range(rng.randrange(4)))
        if choice == 2:
            return {"k" + str(i): value(depth - 1) for i in range(rng.randrange(4))}
        if choice == 3:
            return {rng.randint(-20, 20) for _ in range(rng.randrange(5))}
        return primitive()

    return [value(3) for _ in range(count)]
