import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import clean_text, rating_to_sentiment, load_data

def test_clean_text():
    text = "This is a GREAT product! Check it out <link>"
    result = clean_text(text)
    assert isinstance(result, str)
    assert len(result) > 0
    assert result.islower()

def test_rating_to_sentiment():
    assert rating_to_sentiment(5) == 'positive'
    assert rating_to_sentiment(4) == 'positive'
    assert rating_to_sentiment(3) == 'neutral'
    assert rating_to_sentiment(2) == 'negative'
    assert rating_to_sentiment(1) == 'negative'

def test_load_data():
    data_path = Path(__file__).parent.parent / 'reviews_badminton' / 'data.csv'
    if data_path.exists():
        df = load_data(str(data_path))
        assert df is not None
        assert len(df) > 0
