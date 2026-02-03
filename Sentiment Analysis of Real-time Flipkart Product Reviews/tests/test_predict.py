
import pytest
import os
import tempfile
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from scripts.predict import predict_with_classical


class TestClassicalPrediction:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        
        
        tfidf = TfidfVectorizer(max_features=100)
        X = tfidf.fit_transform(['good product', 'bad product'])
        
       
        model = LogisticRegression(random_state=42)
        y = np.array([1, 0]) 
        model.fit(X, y)
        
      
        le = LabelEncoder()
        le.fit(['negative', 'positive'])
        
     
        joblib.dump(model, os.path.join(self.temp_dir, 'best_classical_model.pkl'))
        joblib.dump(tfidf, os.path.join(self.temp_dir, 'tfidf_vectorizer.pkl'))
        joblib.dump(le, os.path.join(self.temp_dir, 'label_encoder.pkl'))
    
    def teardown_method(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_predict_positive_review(self):
        result = predict_with_classical("good product excellent", self.temp_dir)
        assert 'sentiment' in result
        assert 'confidence' in result
        assert result['sentiment'] in ['positive', 'negative']
        assert 0 <= result['confidence'] <= 1
    
    def test_predict_negative_review(self):
        result = predict_with_classical("bad poor quality", self.temp_dir)
        assert 'sentiment' in result
        assert 'confidence' in result
    
    def test_predict_returns_all_scores(self):
        result = predict_with_classical("test review", self.temp_dir)
        assert 'all_scores' in result
        assert 'negative' in result['all_scores']
        assert 'positive' in result['all_scores']
    
    def test_predict_missing_model_raises_error(self):
        with pytest.raises(FileNotFoundError):
            predict_with_classical("test", 'nonexistent_dir')


class TestPredictionInputs:
    
    def test_empty_review(self):
        pass
    
    def test_very_long_review(self):
        long_text = "word " * 10000
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
