import pytest

from ebench import ebRigol



def test_framework():
    assert 1 == 1

# ------------------------------------------------------------------
# 

def test_extractMeasurements_no_statistics():
    measurements="1:VPP"
    measuremenList = ebRigol.MSO1104.extractMeasurements( measurements)
    assert measuremenList == [['1',None, "VPP"]]
    
def test_extractMeasurements_no_AVEGAE():
    measurements="1:AVERAGE:VPP"
    measuremenList = ebRigol.MSO1104.extractMeasurements( measurements)
    assert measuremenList == [['1',"AVERAGE", "VPP"]]
    
    

