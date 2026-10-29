from text_tools import normalize_words

def test_normalize():
    assert normalize_words('  Red  BLUE ') == ['red', 'blue']
