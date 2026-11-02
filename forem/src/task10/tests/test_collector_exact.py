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
