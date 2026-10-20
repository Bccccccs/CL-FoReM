#!/usr/bin/env python3
"""Syntax gate before any ROS launch; validates cached source without import/executing actor."""
import py_compile,sys
from pathlib import Path

def compile_sources(root,files):
 for relative in files:
  p=Path(root)/'scripts'/relative
  if p.suffix=='.py':py_compile.compile(str(p),doraise=True)
 return True
if __name__=='__main__':
 from task4_identity import ROOT,RUNTIME_FILES,verify_runtime
 compile_sources(ROOT,RUNTIME_FILES);verify_runtime();print('PASS pre-launch Python syntax and actual source/binary identity')
