import os
import argparse
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score, precision_score, recall_score, confusion_matrix,
    classification_report, ConfusionMatrixDisplay, accuracy_score
)
import matplotlib.pyplot as plt
import mlflow
from mlflow.models import infer_signature
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import load_data, preprocess_dataframe

def create_visualizations(y_test, y_pred, model_name, le, artifact_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    ConfusionMatrixDisplay.from_predictions(
        y_test, y_pred, display_labels=le.classes_, ax=ax, cmap='Blues'
    )
    plt.title(f'Confusion Matrix - {model_name}')
    plt.tight_layout()
    cm_path = os.path.join(artifact_dir, f'{model_name}_confusion_matrix.png')
    plt.savefig(cm_path, dpi=100, bbox_inches='tight')
    plt.close()
    return cm_path

def main(args):
    mlflow.set_tracking_uri(f"file:{os.path.abspath('mlruns')}")
    
    experiment_name = "Sentiment Analysis - Classical Models"
    
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(experiment_name)
    
    mlflow.set_experiment(experiment_name)
    
    print("Loading data...")
    df = load_data(args.data_path)
    df = preprocess_dataframe(df)
    
    # Prepare data
    texts = df['clean_text'].astype(str).tolist()
    le = LabelEncoder()
    y = le.fit_transform(df['sentiment'].tolist())
    print(f"Classes: {le.classes_}")
    print(f"Class distribution:\n{pd.Series(y, dtype=int).value_counts()}")
    
    X_texts_train, X_texts_test, y_train, y_test = train_test_split(
        texts, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )
    
    # Vectorization
    print("Vectorizing with TF-IDF...")
    tfidf = TfidfVectorizer(max_features=args.max_features, ngram_range=(1, 2))
    X_train = tfidf.fit_transform(X_texts_train)
    X_test = tfidf.transform(X_texts_test)
    print(f"TF-IDF shape: {X_train.shape}")
    
    # Define models and hyperparameter grids
    models_grid = {
        'LogisticRegression': {
            'model': LogisticRegression(max_iter=1000, random_state=args.random_state),
            'grid': {
                'C': [0.001, 0.01, 0.1, 1, 10],
                'penalty': ['l2'],
                'solver': ['lbfgs']
            }
        },
        'SVM': {
            'model': LinearSVC(random_state=args.random_state, max_iter=2000),
            'grid': {
                'C': [0.01, 0.1, 1, 10, 100],
                'loss': ['squared_hinge', 'hinge']
            }
        },
        'RandomForest': {
            'model': RandomForestClassifier(random_state=args.random_state, n_jobs=-1),
            'grid': {
                'n_estimators': [100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5]
            }
        }
    }
    
    best_model_info = {
        'model': None,
        'score': -1,
        'name': None,
        'run_id': None,
        'best_params': None
    }
    results = []
    
    # Create artifact directory
    artifact_base_dir = 'mlflow_artifacts'
    os.makedirs(artifact_base_dir, exist_ok=True)
    
    for model_name, config in models_grid.items():
        print(f"\n{'='*60}")
        print(f"Training {model_name}...")
        print(f"{'='*60}")
        
        # Create custom run name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{model_name}_GridSearch_{timestamp}"
        
        with mlflow.start_run(run_name=run_name):
            # Log dataset metadata
            mlflow.log_param("dataset_size", len(df))
            mlflow.log_param("train_test_split", args.test_size)
            mlflow.log_param("random_state", args.random_state)
            mlflow.log_param("tfidf_max_features", args.max_features)
            mlflow.log_param("tfidf_ngram_range", "1-2")
            mlflow.log_param("num_classes", len(le.classes_))
            
            # Log class distribution
            class_dist = pd.Series(y).value_counts().to_dict()
            for class_label, count in class_dist.items():
                mlflow.log_param(f"class_distribution_{le.classes_[class_label]}", count)
            
            # Perform GridSearchCV
            gs = GridSearchCV(
                config['model'], config['grid'], cv=5, 
                scoring='f1_weighted', n_jobs=-1, verbose=1
            )
            gs.fit(X_train, y_train)
            
            # Log best hyperparameters
            best_params = gs.best_params_
            mlflow.log_params(best_params)
            mlflow.log_metric("cv_best_f1_score", gs.best_score_)
            
            print(f"Best params: {best_params}")
            print(f"CV F1-score: {gs.best_score_:.4f}")
            
            # Make predictions
            y_pred = gs.best_estimator_.predict(X_test)
            
            # Calculate metrics
            f1 = f1_score(y_test, y_pred, average='weighted')
            prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            acc = accuracy_score(y_test, y_pred)
            
            # Log metrics
            mlflow.log_metric("test_f1_score", f1)
            mlflow.log_metric("test_precision", prec)
            mlflow.log_metric("test_recall", rec)
            mlflow.log_metric("test_accuracy", acc)
            
            print(f"\nTest metrics:")
            print(f"  F1-score (weighted): {f1:.4f}")
            print(f"  Precision (weighted): {prec:.4f}")
            print(f"  Recall (weighted): {rec:.4f}")
            print(f"  Accuracy: {acc:.4f}")
            
            # Log classification report
            class_report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
            for class_name, metrics_dict in class_report.items():
                if isinstance(metrics_dict, dict):
                    for metric_name, value in metrics_dict.items():
                        if isinstance(value, float):
                            mlflow.log_metric(f"{class_name}_{metric_name}", value)
            
            print(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=le.classes_)}")
            print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
            
            # Create visualizations and log artifacts
            artifact_dir = os.path.join(artifact_base_dir, run_name)
            os.makedirs(artifact_dir, exist_ok=True)
            
            cm_path = create_visualizations(y_test, y_pred, model_name, le, artifact_dir)
            mlflow.log_artifact(cm_path)
            
            # Save detailed metrics to JSON
            detailed_metrics = {
                'model': model_name,
                'best_params': best_params,
                'cv_f1_score': float(gs.best_score_),
                'test_metrics': {
                    'f1_score': float(f1),
                    'precision': float(prec),
                    'recall': float(rec),
                    'accuracy': float(acc)
                },
                'classification_report': classification_report(y_test, y_pred, target_names=le.classes_),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
            }
            
            metrics_json_path = os.path.join(artifact_dir, 'detailed_metrics.json')
            with open(metrics_json_path, 'w') as f:
                json.dump(detailed_metrics, f, indent=2)
            mlflow.log_artifact(metrics_json_path)
            
            # Log model signature
            signature = infer_signature(X_test, y_pred)
            
            # Log the model
            mlflow.sklearn.log_model(
                gs.best_estimator_,
                artifact_path=f"{model_name.lower()}_model",
                signature=signature,
                input_example=X_test[:5]
            )
            
            # Get run ID and update best model
            run_id = mlflow.active_run().info.run_id
            
            results.append({
                'model': model_name,
                'f1_train': gs.best_score_,
                'f1_test': f1,
                'precision': prec,
                'recall': rec,
                'accuracy': acc,
                'run_id': run_id
            })
            
            if f1 > best_model_info['score']:
                best_model_info['model'] = gs.best_estimator_
                best_model_info['score'] = f1
                best_model_info['name'] = model_name
                best_model_info['run_id'] = run_id
                best_model_info['best_params'] = best_params
            
            print(f"Run ID: {run_id}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    print(f"\nBest model: {best_model_info['name']} with F1-score: {best_model_info['score']:.4f}")
    print(f"Best model Run ID: {best_model_info['run_id']}")
    
    # Save artifacts
    os.makedirs(args.output_dir, exist_ok=True)
    
    model_path = os.path.join(args.output_dir, 'best_classical_model.pkl')
    tfidf_path = os.path.join(args.output_dir, 'tfidf_vectorizer.pkl')
    le_path = os.path.join(args.output_dir, 'label_encoder.pkl')
    results_path = os.path.join(args.output_dir, 'classical_results_mlflow.csv')
    
    joblib.dump(best_model_info['model'], model_path)
    joblib.dump(tfidf, tfidf_path)
    joblib.dump(le, le_path)
    results_df.to_csv(results_path, index=False)
    
    print(f"\nSaved artifacts:")
    print(f"  Model: {model_path}")
    print(f"  Vectorizer: {tfidf_path}")
    print(f"  Label encoder: {le_path}")
    print(f"  Results: {results_path}")
    
    return best_model_info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train classical ML models with MLflow tracking.')
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
        '--test_size',
        type=float,
        default=0.2,
        help='Test size for train-test split'
    )
    parser.add_argument(
        '--random_state',
        type=int,
        default=42,
        help='Random state for reproducibility'
    )
    parser.add_argument(
        '--output_dir',
        default='models',
        help='Output directory for models'
    )
    args = parser.parse_args()
    main(args)
