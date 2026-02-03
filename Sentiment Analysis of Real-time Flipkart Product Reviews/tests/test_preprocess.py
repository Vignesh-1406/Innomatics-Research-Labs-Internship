"""
Unit tests for preprocessing module.
"""

import pytest
import os
import tempfile
import pandas as pd
from scripts.preprocess import (
    clean_text, expand_contractions, rating_to_sentiment,
    load_data, preprocess_dataframe
)


class TestTextCleaning:
    """Test text cleaning utilities."""
    
    def test_clean_text_removes_read_more(self):
        """Test that READ MORE tokens are removed."""
        text = "Great product READ MORE"
        cleaned = clean_text(text)
        assert "read more" not in cleaned.lower()
    
    def test_clean_text_lowercases(self):
        """Test that text is lowercased."""
        text = "GREAT PRODUCT"
        cleaned = clean_text(text)
        assert cleaned == cleaned.lower()
    
    def test_clean_text_removes_punctuation(self):
        """Test that punctuation is removed."""
        text = "Great product! Really good."
        cleaned = clean_text(text)
        assert "!" not in cleaned
        assert "." not in cleaned
    
    def test_clean_text_removes_stopwords(self):
        """Test that common stopwords are removed."""
        text = "this is a great product"
        cleaned = clean_text(text)
        # 'is', 'a' should be removed
        assert "is" not in cleaned.split()
        assert "a" not in cleaned.split()
    
    def test_clean_text_empty_input(self):
        """Test handling of empty/None input."""
        assert clean_text("") == ""
        assert clean_text(None) == ""
    
    def test_expand_contractions(self):
        """Test contraction expansion."""
        text = "don't you'll we're"
        expanded = expand_contractions(text)
        assert "do not" in expanded or "don" in expanded
        assert "you will" in expanded or "you" in expanded


class TestRatingConversion:
    """Test rating to sentiment conversion."""
    
    def test_positive_rating(self):
        """Test that ratings >= 4 are positive."""
        assert rating_to_sentiment(5) == 'positive'
        assert rating_to_sentiment(4) == 'positive'
    
    def test_negative_rating(self):
        """Test that ratings <= 2 are negative."""
        assert rating_to_sentiment(1) == 'negative'
        assert rating_to_sentiment(2) == 'negative'
    
    def test_neutral_rating(self):
        """Test that rating 3 is neutral."""
        assert rating_to_sentiment(3) == 'neutral'
    
    def test_invalid_rating(self):
        """Test handling of invalid ratings."""
        assert rating_to_sentiment("invalid") is None
        assert rating_to_sentiment(None) is None


class TestDataLoading:
    """Test data loading and preprocessing."""
    
    def test_load_data(self):
        """Test loading CSV data."""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,value\ntest,1\n")
            temp_path = f.name
        
        try:
            df = load_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == ['name', 'value']
            assert len(df) == 1
        finally:
            os.unlink(temp_path)
    
    def test_preprocess_dataframe(self):
        """Test dataframe preprocessing."""
        df = pd.DataFrame({
            'Review text': ['Great product', 'Terrible quality'],
            'Ratings': [5.0, 1.0]
        })
        
        processed = preprocess_dataframe(df, text_col='Review text', drop_neutral=True)
        
        assert 'sentiment' in processed.columns
        assert 'clean_text' in processed.columns
        assert len(processed) == 2
        assert processed['sentiment'].iloc[0] == 'positive'
        assert processed['sentiment'].iloc[1] == 'negative'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
