#!/usr/bin/env python3
"""Fixed complete task8_sim regression under no-training guards."""
import json
from pathlib import Path
import sys
import torch
from task8_sim.profile_lower import prohibit_training

if __name__=='__main__':
    import pytest
    calls=prohibit_training();torch.set_num_threads(2)
    result=pytest.main(['-q','-p','no:cacheprovider',str(Path(__file__).resolve().parents[1]/'src/task8_sim/tests')])
    print(json.dumps(dict(guards=calls,exit_code=result)),flush=True)
    assert calls==dict(optimizer_constructed=0,backward_calls=0)
    raise SystemExit(result)
