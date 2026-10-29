from sequence import take_first

def test_take_requested_count():
    assert take_first(['a', 'b', 'c'], 2) == ['a', 'b']

def test_all_items():
    assert take_first(['x'], 1) == ['x']
