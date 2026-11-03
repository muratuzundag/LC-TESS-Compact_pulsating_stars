import numpy as np
import pytest

from lc_tess.core import CADENCES, arrays, grid_limits
from lc_tess.cli import main, parser


def test_cadences():
    assert CADENCES["usc"]==(20,)
    assert CADENCES["sc"]==(120,)
    assert CADENCES["both"]==(20,120)


def test_sc_limits():
    lo,hi,nyquist,bins=grid_limits([0,10],120)
    assert lo==pytest.approx(1e6/(10*86400))
    assert nyquist==pytest.approx(4166.66666667)
    assert hi==pytest.approx(0.99*nyquist)
    assert bins>2


def test_usc_nyquist():
    assert grid_limits([0,10],20)[2]==25000


def test_supernyquist():
    with pytest.raises(ValueError):grid_limits([0,10],120,1,5000)
    assert grid_limits([0,10],120,1,5000,super_nyquist=True)[1]==5000


@pytest.mark.parametrize("lo,hi",[(0,10),(20,10),(1,float("nan"))])
def test_bad_bounds(lo,hi):
    with pytest.raises(ValueError):grid_limits([0,10],120,lo,hi)


def test_grid_guard():
    with pytest.raises(ValueError):grid_limits([0,1000],20,max_bins=100)


def test_sorted_valid_rows():
    t=np.arange(12.)[::-1]
    out,y,e,idx=arrays(t,np.ones(12),np.ones(12))
    assert np.array_equal(out,np.arange(12.))
    assert np.array_equal(t[idx],out)


def test_invalid_errors_removed():
    err=np.ones(12);err[0]=0
    assert len(arrays(np.arange(12.),np.ones(12),err)[0])==11


def test_duplicate_rejected():
    with pytest.raises(ValueError):arrays(np.ones(12),np.ones(12),np.ones(12))


def test_parser_defaults():
    args=parser().parse_args(["--tic","422526868"])
    assert args.cadence=="both" and args.sigma is None and args.flatten_window is None


@pytest.mark.parametrize("args",[
    ["--tic","-1"], ["--tic","2","--dec","5"],
    ["--ra","400","--dec","5"], ["--ra","0"],
    ["--tic","2","--sigma","0"], ["--tic","2","--flatten-window","8"],
    ["--tic","2","--frequencies","-10"], ["--tic","2","--fmin","20","--fmax","10"],
])
def test_invalid_cli_stops_before_archive(args):
    with pytest.raises(SystemExit) as exc:main(args)
    assert exc.value.code==2
