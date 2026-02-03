
import os
import argparse
import sys
import joblib
import numpy as np
from pathlib import Path
import torch


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
    

    vec = tfidf.transform([cleaned])
    

    pred = model.predict(vec)[0]
    

    try:
        proba = model.predict_proba(vec)[0]
        confidence = np.max(proba)
        all_scores = {le.classes_[i]: float(proba[i]) for i in range(len(le.classes_))}
    except AttributeError:
       
        decision = model.decision_function(vec)[0]
        confidence = 1.0 / (1.0 + np.exp(-decision))  
        all_scores = {
            'negative': 1.0 - confidence if pred == 1 else confidence,
            'positive': confidence if pred == 1 else 1.0 - confidence
        }
    
    sentiment = le.inverse_transform([pred])[0]
    
    return {
        'sentiment': sentiment,
        'confidence': float(confidence),
        'all_scores': all_scores
    }


def predict_with_bert(review_text, model_dir='models'):
    bert_dir = os.path.join(model_dir, 'bert_model')
    le_path = os.path.join(model_dir, 'label_encoder.pkl')
    
    if not os.path.exists(bert_dir) or not os.path.exists(le_path):
        raise FileNotFoundError(f"BERT artifacts not found in {model_dir}")
    
    try:
        from transformers import pipeline
    except ImportError:
        raise ImportError("transformers library required for BERT prediction")
    
    le = joblib.load(le_path)
    device = 0 if torch.cuda.is_available() else -1
    classifier = pipeline(
        "text-classification",
        model=bert_dir,
        tokenizer=bert_dir,
        device=device
    )
    
    result = classifier(review_text[:512])
    
    label = result[0]['label']
    score = result[0]['score']
    

    sentiment = 'positive' if label == 'LABEL_1' else 'negative'
    
    return {
        'sentiment': sentiment,
        'confidence': float(score),
        'all_scores': {
            'negative': 1 - float(score) if label == 'LABEL_1' else float(score),
            'positive': float(score) if label == 'LABEL_1' else 1 - float(score)
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Predict sentiment of a review.')
    parser.add_argument('review', type=str, help='Review text to classify')
    parser.add_argument(
        '--model',
        choices=['classical', 'bert'],
        default='classical',
        help='Model to use for prediction'
    )
    parser.add_argument(
        '--model_dir',
        default='models',
        help='Directory containing model artifacts'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed output'
    )
    
    args = parser.parse_args()
    
    try:
        if args.model == 'classical':
            result = predict_with_classical(args.review, args.model_dir)
        else:
            result = predict_with_bert(args.review, args.model_dir)
        
        if args.verbose:
            print(f"Review: {args.review[:100]}...")
            print(f"Model: {args.model}")
            print(f"\nSentiment: {result['sentiment'].upper()}")
            print(f"Confidence: {result['confidence']:.4f}")
            print(f"Scores: {result['all_scores']}")
        else:
            print(f"{result['sentiment'].upper()},{result['confidence']:.4f}")
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
