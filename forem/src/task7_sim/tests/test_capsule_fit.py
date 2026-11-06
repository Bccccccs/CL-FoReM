import numpy as np
from task7_sim.robot import fit_capsule

def test_bounding_capsule_fits_spherical_end_caps_without_axis_overshoot():
    # An exact unit sphere is already a zero-length capsule; extending a line
    # between +/-1 first and then appending hemispheres produces radius-2 bounds.
    v=np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],dtype=float)
    a,b,r=fit_capsule(v)
    assert np.linalg.norm(a-b)<1e-6 and abs(r-1)<1e-6
    assert max(np.linalg.norm(v-a,axis=-1))<=r+1e-8
