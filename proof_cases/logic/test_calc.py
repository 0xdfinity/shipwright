from calc import apply_discount

def test_discount():
    assert apply_discount(10000, 20) == 8000

def test_zero_percent():
    assert apply_discount(145, 0) == 145
