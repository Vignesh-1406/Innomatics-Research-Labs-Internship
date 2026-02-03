
import os
import argparse
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, GridSearchCV, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score, precision_score, recall_score, confusion_matrix,
    classification_report, ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
from scripts.preprocess import load_data, preprocess_dataframe


def main(args):
   
    print("Loading data...")
    df = load_data(args.data_path)
    df = preprocess_dataframe(df)
    
  
    texts = df['clean_text'].astype(str).tolist()
    le = LabelEncoder()
    y = le.fit_transform(df['sentiment'].tolist())
    print(f"Classes: {le.classes_}")
    print(f"Class distribution:\n{pd.Series(y, dtype=int).value_counts()}")
    
    X_texts_train, X_texts_test, y_train, y_test = train_test_split(
        texts, y, test_size=0.2, random_state=42, stratify=y
    )
    

    print("Vectorizing with TF-IDF...")
    tfidf = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2))
    X_train = tfidf.fit_transform(X_texts_train)
    X_test = tfidf.transform(X_texts_test)
    print(f"TF-IDF shape: {X_train.shape}")
    

    models_grid = {
        'LogisticRegression': {
            'model': LogisticRegression(max_iter=1000, random_state=42),
            'grid': {
                'C': [0.001, 0.01, 0.1, 1, 10],
                'penalty': ['l2'],
                'solver': ['lbfgs']
            }
        },
        'SVM': {
            'model': LinearSVC(random_state=42, max_iter=2000),
            'grid': {
                'C': [0.01, 0.1, 1, 10, 100],
                'loss': ['squared_hinge', 'hinge']
            }
        },
        'RandomForest': {
            'model': RandomForestClassifier(random_state=42, n_jobs=-1),
            'grid': {
                'n_estimators': [100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5]
            }
        }
    }
    
    best_model = None
    best_score = -1
    best_name = None
    results = []
    
    for name, config in models_grid.items():
        print(f"\n{'='*50}")
        print(f"Training {name}...")
        print(f"{'='*50}")
        
       
        gs = GridSearchCV(config['model'], config['grid'], cv=5, scoring='f1_weighted', n_jobs=-1)
        gs.fit(X_train, y_train)
        
        print(f"Best params: {gs.best_params_}")
        print(f"CV F1-score: {gs.best_score_:.4f}")
        
      
        y_pred = gs.best_estimator_.predict(X_test)
        
  
        f1 = f1_score(y_test, y_pred, average='weighted')
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        
        print(f"\nTest metrics:")
        print(f"  F1-score (weighted): {f1:.4f}")
        print(f"  Precision (weighted): {prec:.4f}")
        print(f"  Recall (weighted): {rec:.4f}")
        print(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=le.classes_)}")
        print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
        
        results.append({
            'model': name,
            'f1_train': gs.best_score_,
            'f1_test': f1,
            'precision': prec,
            'recall': rec
        })
        
   
        if f1 > best_score:
            best_score = f1
            best_model = gs.best_estimator_
            best_name = name
    
   
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    print(f"\nBest model: {best_name} with F1-score: {best_score:.4f}")
    
 
    os.makedirs(args.output_dir, exist_ok=True)
    
    model_path = os.path.join(args.output_dir, f'best_classical_model.pkl')
    tfidf_path = os.path.join(args.output_dir, 'tfidf_vectorizer.pkl')
    le_path = os.path.join(args.output_dir, 'label_encoder.pkl')
    results_path = os.path.join(args.output_dir, 'classical_results.csv')
    
    joblib.dump(best_model, model_path)
    joblib.dump(tfidf, tfidf_path)
    joblib.dump(le, le_path)
    results_df.to_csv(results_path, index=False)
    
    print(f"\nSaved artifacts:")
    print(f"  Model: {model_path}")
    print(f"  Vectorizer: {tfidf_path}")
    print(f"  Label encoder: {le_path}")
    print(f"  Results: {results_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train classical ML models on reviews.')
    parser.add_argument(
        '--data_path',
        default=os.path.join('reviews_badminton', 'data.csv'),
        help='Path to reviews CSV'
    )
    parser.add_argument(
        '--max_features',
        type=int,
        default=20000,
        help='Max TF-IDF features'
    )
    parser.add_argument(
        '--output_dir',
        default='models',
        help='Output directory for models'
    )
    args = parser.parse_args()
    main(args)
