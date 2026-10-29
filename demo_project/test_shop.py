from shop import slugify, apply_discount, median


def test_slugify():
    assert slugify("  Hello World  ") == "hello-world"


def test_discount():
    assert apply_discount(10000, 20) == 8000


def test_median_odd_and_even():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5
