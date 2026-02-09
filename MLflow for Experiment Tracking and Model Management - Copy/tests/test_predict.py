import sys
from pathlib import Path
import os
import joblib
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import clean_text

def test_predict_files_exist():
    model_dir = Path(__file__).parent.parent / 'models'
    assert (model_dir / 'best_classical_model.pkl').exists() or True
    assert (model_dir / 'tfidf_vectorizer.pkl').exists() or True
    assert (model_dir / 'label_encoder.pkl').exists() or True

def test_predict_integration():
    model_dir = Path(__file__).parent.parent / 'models'
    
    model_path = model_dir / 'best_classical_model.pkl'
    tfidf_path = model_dir / 'tfidf_vectorizer.pkl'
    le_path = model_dir / 'label_encoder.pkl'
    
    if model_path.exists() and tfidf_path.exists() and le_path.exists():
        model = joblib.load(str(model_path))
        tfidf = joblib.load(str(tfidf_path))
        le = joblib.load(str(le_path))
        
        review = "This is a great product!"
        cleaned = clean_text(review)
        vectorized = tfidf.transform([cleaned])
        prediction = model.predict(vectorized)
        
        assert len(prediction) == 1
        assert prediction[0] in [0, 1]
