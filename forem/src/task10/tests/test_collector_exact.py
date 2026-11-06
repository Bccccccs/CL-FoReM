"""Collector acceptance must preserve bytes, including signed zero."""
import numpy as np
import pytest
import torch
from task10.recovery import tree_equal, mismatch_report


@pytest.mark.parametrize('make', [lambda x: torch.tensor([x], dtype=torch.float32),
                                 lambda x: np.array([x], dtype=np.float32),
                                 lambda x: x])
def test_collector_signed_zero_is_a_bitwise_mismatch(make):
    positive, negative = make(0.0), make(-0.0)
    assert not tree_equal(positive, negative)
    assert mismatch_report({'value': positive}, {'value': negative})


def test_collector_identical_bytes_remain_equal():
    values = {'tensor': torch.tensor([0.0, -0.0]), 'numpy': np.array([0.0, -0.0]),
              'nested': (1, 2.0, [True, None])}
    import copy
    assert tree_equal(values, copy.deepcopy(values))
    assert mismatch_report(values, copy.deepcopy(values)) == []


@pytest.mark.parametrize('dtype', [torch.float32, torch.float64, torch.int64, torch.bfloat16, torch.bool])
@pytest.mark.parametrize('shape', [(1,), (1, 1), (0,)])
def test_collector_singleton_or_empty_nonunit_stride_preserves_exact_comparison(dtype, shape):
    backing = torch.arange(39).to(dtype)
    value = backing.as_strided(shape, (13,) * len(shape), storage_offset=13)
    # Singleton/empty dimensions may be considered contiguous despite stride 13.
    assert value.is_contiguous() and value.stride()[-1] == 13
    expected = value.clone(memory_format=torch.contiguous_format)
    assert tree_equal(value, expected)
    assert tree_equal(expected, value)


def test_collector_strided_singleton_keeps_signed_zero_distinct():
    backing = torch.zeros(26)
    value = backing[::13][1:]
    assert value.stride() == (13,)
    assert tree_equal(value, torch.tensor([0.]))
    assert not tree_equal(value, torch.tensor([-0.]))


def test_collector_strided_singleton_compares_nan_payload_bytes():
    backing = torch.zeros(26, dtype=torch.int32)
    backing[13] = 0x7FC00001
    value = backing.view(torch.float32)[::13][1:]
    same = torch.tensor([0x7FC00001], dtype=torch.int32).view(torch.float32)
    different = torch.tensor([0x7FC00002], dtype=torch.int32).view(torch.float32)
    assert tree_equal(value, same)
    assert not tree_equal(value, different)
