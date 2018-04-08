from ..builder import repo


def test_repo():
    test_val = repo('test')
    assert 'https://github.com/test/scipy_proceedings.git' == test_val
