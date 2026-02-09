import os
import argparse
import sys
import joblib
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import clean_text

def predict_with_classical(review_text, model_dir='models'):
    model_path = os.path.join(model_dir, 'best_classical_model.pkl')
    tfidf_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')
    le_path = os.path.join(model_dir, 'label_encoder.pkl')
    
    if not all(os.path.exists(p) for p in [model_path, tfidf_path, le_path]):
        raise FileNotFoundError(f"Model artifacts not found in {model_dir}")
    
    model = joblib.load(model_path)
    tfidf = joblib.load(tfidf_path)
    le = joblib.load(le_path)
    
    cleaned = clean_text(review_text)
    vectorized = tfidf.transform([cleaned])
    prediction = model.predict(vectorized)[0]
    probability = model.predict_proba(vectorized)[0]
    
    sentiment = le.inverse_transform([prediction])[0]
    confidence = max(probability)
    
    return {
        'sentiment': sentiment,
        'confidence': confidence,
        'probabilities': dict(zip(le.classes_, probability))
    }

def main():
    parser = argparse.ArgumentParser(description='Predict sentiment for a review')
    parser.add_argument('review', help='Review text to analyze')
    parser.add_argument('--model-dir', default='models', help='Path to model directory')
    
    args = parser.parse_args()
    
    try:
        result = predict_with_classical(args.review, args.model_dir)
        print(f"Sentiment: {result['sentiment']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Probabilities: {result['probabilities']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
