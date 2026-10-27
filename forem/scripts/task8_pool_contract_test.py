"""Bounded regression for SRC-1161, never trains or edits source maps."""
import importlib.util
from pathlib import Path
import json
import numpy as np

p=Path(__file__).with_name('task8_build_pool.py')
s=importlib.util.spec_from_file_location('builder',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert hasattr(m,'target_cells'), 'cube-export-v2 target O implementation missing'
src=m.ROOT/'results/task7/maps/a/20261021T021400Z/sparse/train/00000.json'
index=json.loads((src.parents[2]/'index.json').read_text()) if src.exists() else json.loads((m.ROOT/'results/task7/maps/a/20261021T021400Z/index.json').read_text())
row=next(r for r in index['maps'] if r['id']=='sparse_train_00000')
b=json.loads((m.ROOT/'results/task7/maps/a/20261021T021400Z'/row['path']).read_text())['boxes'][4]
cells=m.target_cells(b)
assert cells[1,14,22], 'known strictly interior r1 hole must be filled'
# Thin box has no world centre inside; fixture-containing cells preserve it.
thin=[.011,.012,.013,.001,.002,.003,1.,0.]
assert m.target_cells(thin).sum()==1
# The centre sample is on x=y=z=.05 world faces: all eight closed cells contain it.
face=[.025,.025,.025,.05,.05,.05,1.,0.]
assert m.target_cells(face)[0:2,100:102,100:102].all()
print('cube-export-v2 contract: strict r1 hole, thin box, closed face sample PASS')
