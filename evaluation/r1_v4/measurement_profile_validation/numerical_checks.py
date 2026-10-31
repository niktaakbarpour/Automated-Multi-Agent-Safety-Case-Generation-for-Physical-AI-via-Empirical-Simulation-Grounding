"""Exact-rational checks of computational BOX envelopes, not physical calibration."""
from fractions import Fraction as F
import math
import numpy as np
from .geometry import corners,SIGNS

def check():
 positions=[(0.,0.,0.),(.1,-.3,.43676000000000015),(-.7,.2,1.05)]
 rotations=[np.eye(3),np.array([[0,0,1],[0,1,0],[-1,0,0]]),np.array([[math.cos(.7),-math.sin(.7),0],[math.sin(.7),math.cos(.7),0],[0,0,1]])]
 sizes=[(.040608,.021336,.008936),(.01184,.07752,.67171),(.0724,.06368,.00667)]
 count=0
 for p in positions:
  for r in rotations:
   for s in sizes:
    nominal,lo,hi=corners(p,r,s)
    for k,sign in enumerate(SIGNS):
     for axis in range(3):
      exact=F(p[axis])+sum((F(float(r[axis,j]))*F(sign[j]*s[j]) for j in range(3)),F(0))
      assert F(float(lo[k,axis]))<=exact<=F(float(hi[k,axis]))
      assert lo[k,axis]<=nominal[k,axis]<=hi[k,axis]
      count+=1
 return dict(passed=True,exact_rational_coordinate_checks=count,BOX_cases=27,scope='Computational enclosure of exact finite binary64 inputs only',physical_uncertainty_bound=None)
if __name__=='__main__':print(check())
