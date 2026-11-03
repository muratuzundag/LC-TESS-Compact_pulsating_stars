"""Offline integration tests; analytical fixtures are NOT observations."""
from types import SimpleNamespace
import numpy as np
import pytest

lk=pytest.importorskip("lightkurve")
from astropy.time import Time
from lc_tess.workflow import prepare, analyze


def test_units_time_and_amplitude(tmp_path):
    # Deliberate analytical unit-test fixture: 2-ppt sine at 1000 microhertz.
    # It is not used in the logo, examples, or any scientific inference.
    seconds=np.arange(1000)*120.
    time=Time(2459000+seconds/86400,format="jd",scale="tdb")
    flux=10000*(1+0.002*np.sin(2*np.pi*0.001*seconds))
    lc=lk.LightCurve(time=time,flux=flux,flux_err=np.full(1000,10.))
    clean=prepare(lc)
    assert np.median(clean.flux.value)==pytest.approx(0,abs=1e-6)
    assert np.median(clean.flux_err.value)==pytest.approx(1,rel=0.01)
    args=SimpleNamespace(fmin=800.,fmax=1200.,super_nyquist=False,
                         oversample=5,max_bins=10000)
    info=analyze(clean,tmp_path/"fixture",120,args)
    data=np.loadtxt(tmp_path/"fixture_lc.csv",delimiter=",",skiprows=1)
    lsp=np.loadtxt(tmp_path/"fixture_lsp.csv",delimiter=",",skiprows=1)
    assert data[0,0]==pytest.approx(2459000)
    assert info["time_export"]=="BJD_TDB"
    assert lsp[np.argmax(lsp[:,2]),0]==pytest.approx(1000,abs=3)
    assert np.max(lsp[:,2])==pytest.approx(2,rel=0.05)
