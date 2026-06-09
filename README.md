# Marshal Stability and Correctness Test Suite

This repository contains a black-box and light white-box test suite for Python's
`marshal` module. The central question is whether the same input creates the
same marshal byte stream under repeated execution and across selected runtime
conditions.

## Test scope

The suite covers:

- supported primitive values: `None`, booleans, integers, floats, complex values,
  strings, bytes, bytearray, `Ellipsis`, and `StopIteration`;
- supported containers: tuple, list, dictionary, set, frozenset, and recursive
  lists;
- boundary values: empty strings/bytes/collections, 1-item values, 255/256
  character strings, 32-bit and 64-bit integer boundaries, big integers, and a
  large list;
- floating-point special values: `NaN`, `Inf`, `-Inf`, and `-0.0`;
- deterministic fuzzing with randomly generated but reproducible values;
- cross-process stability under different `PYTHONHASHSEED` values;
- selected documented behavior: trailing bytes are ignored by `loads()`, invalid
  streams raise documented exceptions, and unsupported values raise `ValueError`.

Only the Python standard library is required.

## Run locally

```bash
python -m unittest discover -s tests -v
python scripts/collect_fingerprints.py --repeats 10
```

## Recommended CI use

The included GitHub Actions workflow runs the test suite on Linux, Windows, and
macOS, and across multiple Python versions. The fingerprint script can be used to
compare hash outputs between CI jobs.

