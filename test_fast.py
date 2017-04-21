import fast
import pytest

#example of tests setup

@pytest.mark.testrail('C42')
#C42 Corresponds to a test case within the test suite chosen
def test_ret2():
    '''test'''
    assert fast.ret2() == 2

@pytest.mark.testrail('C43')
def test_ret3():
    '''test'''
    assert 3 == 2
