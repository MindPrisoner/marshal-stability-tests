"""Stability and correctness tests for Python's marshal module."""

from __future__ import annotations

import inspect
import io
import json
import marshal
import math
import os
import subprocess
import sys
import unittest

from marshal_stability.cases import cyclic_list_case, fuzz_values, stable_cases
from marshal_stability.fingerprint import equivalent, sha256_of_marshal


class MarshalStabilityTests(unittest.TestCase):
    """Tests focused on hash-identical marshal output."""

    def test_repeated_dumps_are_hash_identical(self) -> None:
        for case in stable_cases():
            with self.subTest(case=case.label):
                hashes = {sha256_of_marshal(case.value) for _ in range(20)}
                self.assertEqual(1, len(hashes))

    def test_dump_and_dumps_produce_same_bytes(self) -> None:
        for case in stable_cases():
            with self.subTest(case=case.label):
                buffer = io.BytesIO()
                marshal.dump(case.value, buffer)
                self.assertEqual(marshal.dumps(case.value), buffer.getvalue())

    def test_round_trip_supported_values(self) -> None:
        for case in stable_cases():
            with self.subTest(case=case.label):
                loaded = marshal.loads(marshal.dumps(case.value))
                self.assertTrue(equivalent(case.value, loaded))

    def test_loads_ignores_trailing_bytes(self) -> None:
        payload = marshal.dumps({"status": "ok"}) + b"extra bytes"
        self.assertEqual({"status": "ok"}, marshal.loads(payload))

    def test_invalid_input_raises_documented_exception(self) -> None:
        with self.assertRaises((EOFError, ValueError, TypeError)):
            marshal.loads(b"not a marshal stream")

    def test_unsupported_objects_raise_value_error(self) -> None:
        unsupported_values = [object(), lambda value: value]
        for value in unsupported_values:
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ValueError):
                    marshal.dumps(value)

    def test_recursive_list_round_trip_preserves_cycle(self) -> None:
        value = cyclic_list_case()
        first = marshal.dumps(value)
        second = marshal.dumps(value)
        loaded = marshal.loads(first)
        self.assertEqual(first, second)
        self.assertIs(loaded[0], loaded)

    def test_special_float_values_remain_stable(self) -> None:
        values = [0.0, -0.0, math.inf, -math.inf, math.nan]
        for value in values:
            with self.subTest(value=repr(value)):
                first = marshal.dumps(value)
                second = marshal.dumps(value)
                loaded = marshal.loads(first)
                self.assertEqual(first, second)
                if math.isnan(value):
                    self.assertTrue(math.isnan(loaded))
                else:
                    self.assertEqual(value, loaded)

    def test_deterministic_fuzz_values_are_stable_and_correct(self) -> None:
        for index, value in enumerate(fuzz_values(count=100)):
            with self.subTest(index=index, value_type=type(value).__name__):
                first = marshal.dumps(value)
                second = marshal.dumps(value)
                loaded = marshal.loads(first)
                self.assertEqual(first, second)
                self.assertTrue(equivalent(value, loaded))

    def test_cross_process_hash_seed_stability(self) -> None:
        script = """
import hashlib
import json
import marshal
values = {
    "set_strings": {"apple", "banana", "cherry", "date"},
    "frozenset_strings": frozenset({"apple", "banana", "cherry"}),
    "dict_ordered": {"a": 1, "b": [2, 3], "c": None},
    "tuple_nested": (1, "two", (3, 4), None),
}
print(json.dumps({
    name: hashlib.sha256(marshal.dumps(value)).hexdigest()
    for name, value in values.items()
}, sort_keys=True))
"""
        outputs = []
        for seed in ["1", "2", "3", "4", "5"]:
            environment = os.environ.copy()
            environment["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                [sys.executable, "-c", script],
                check=True,
                capture_output=True,
                env=environment,
                text=True,
            )
            outputs.append(json.loads(completed.stdout))
        self.assertTrue(all(item == outputs[0] for item in outputs))

    def test_code_objects_can_be_blocked_when_supported(self) -> None:
        parameters = inspect.signature(marshal.dumps).parameters
        if "allow_code" not in parameters:
            self.skipTest("allow_code is not available in this Python version")
        code_object = (lambda x: x + 1).__code__
        with self.assertRaises(ValueError):
            marshal.dumps(code_object, allow_code=False)
