import pytest
from median import median

def test_even_length_averages_middle_values():
    assert median([1, 3, 2, 4]) == 2.5

def test_odd_length():
    assert median([9, 1, 5]) == 5

def test_empty_is_explicit_error():
    with pytest.raises(ValueError):
        median([])
