import os
import mlflow
from mlflow.tracking import MlflowClient

def main():
    mlflow.set_tracking_uri(f"file:{os.path.abspath('mlruns')}")
    client = MlflowClient()
    
    experiment = mlflow.get_experiment_by_name("Sentiment Analysis - Classical Models")
    if not experiment:
        print("Experiment not found.")
        return
    
    experiment_id = experiment.experiment_id
    
    runs = mlflow.search_runs(
        experiment_ids=[experiment_id],
        order_by=["metrics.test_f1_score DESC"]
    )
    
    if runs.empty:
        print("No runs found.")
        return
    
    print(f"Found {len(runs)} runs. Adding tags...\n")
    
    # Tag mappings for each model
    tag_configs = {
        'LogisticRegression_GridSearch': {
            'algorithm': 'LogisticRegression',
            'model_type': 'linear',
            'best_model': 'no'
        },
        'SVM_GridSearch': {
            'algorithm': 'SVM',
            'model_type': 'svm',
            'best_model': 'no'
        },
        'RandomForest_GridSearch': {
            'algorithm': 'RandomForest',
            'model_type': 'ensemble',
            'best_model': 'no'
        }
    }
    
    best_run = runs.iloc[0]
    best_run_id = best_run['run_id']
    best_f1 = best_run['metrics.test_f1_score']
    best_run_name = best_run['tags.mlflow.runName']
    best_model_type = best_run_name.split('_')[0]
    
    # Add tags to all runs
    for idx, row in runs.iterrows():
        run_id = row['run_id']
        run_name = row['tags.mlflow.runName']
        f1_score = row['metrics.test_f1_score']
        
        # Determine model type from run name
        model_type = run_name.split('_')[0]
        
        # Base tags
        tags = {
            'dataset': 'badminton_reviews',
            'task': 'sentiment_analysis',
            'vectorizer': 'tfidf',
            'preprocessing': 'cleaned_lemmatized',
            'test_set_size': '0.2'
        }
        
        # Add model-specific tags
        if model_type in tag_configs:
            tags.update(tag_configs[model_type])
        
        # Mark best model
        if run_id == best_run_id:
            tags['best_model'] = 'yes'
            tags['status'] = 'registered'
        else:
            tags['status'] = 'candidate'
        
        # Add F1 score as tag
        tags['f1_score'] = f"{f1_score:.4f}"
        tags['ranking'] = str(idx + 1)
        
        # Apply tags
        for tag_key, tag_value in tags.items():
            client.set_tag(run_id, tag_key, tag_value)
        
        print(f"[OK] Tagged run: {run_name} (ID: {run_id[:8]}...)")
        print(f"  F1-Score: {f1_score:.4f}")
        if run_id == best_run_id:
            print(f"  ** BEST MODEL **")
        print()
    
    # Register best model
    print("\n" + "="*80)
    print("REGISTERING BEST MODEL")
    print("="*80 + "\n")
    
    model_uri = f"runs:/{best_run_id}/{best_model_type.lower()}_model"
    model_name = "Flipkart_Sentiment_Model"
    
    print(f"Model: {best_model_type}")
    print(f"Run ID: {best_run_id}")
    print(f"F1 Score: {best_f1:.4f}")
    print(f"Model URI: {model_uri}")
    print(f"Registry Name: {model_name}\n")
    
    try:
        # Check if model already exists
        try:
            existing = client.get_registered_model(model_name)
            print(f"[WARNING] Model '{model_name}' already exists. Getting latest version...")
            mv = existing
            version = len(existing.latest_versions) + 1
        except:
            # Register new model
            mv = mlflow.register_model(model_uri, model_name)
            version = mv.version
            print(f"[OK] Model registered successfully!")
        
        print(f"  Model Name: {model_name}")
        print(f"  Version: {version}")
        
        # Transition to Staging
        client.transition_model_version_stage(
            name=model_name,
            version=str(version),
            stage="Staging"
        )
        print(f"[OK] Model transitioned to 'Staging' stage")
        
        # Add model-level tags
        model_tags = {
            'algorithm': best_model_type,
            'dataset': 'badminton_reviews',
            'task': 'sentiment_classification',
            'cv_folds': '5',
            'production_ready': 'pending_validation'
        }
        
        for tag_key, tag_value in model_tags.items():
            client.set_model_version_tag(model_name, str(version), tag_key, tag_value)
        
        print(f"[OK] Tags added to model version")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n[OK] Tagged {len(runs)} runs")
    print(f"[OK] Registered model: {model_name}")
    print(f"[OK] Current stage: Staging")
    print(f"\nTo view in MLflow UI:")
    print(f"  Open: http://127.0.0.1:5000")
    print(f"  Navigate to: Models -> {model_name}")
    print(f"\nTo promote to Production:")
    print(f"  Models -> {model_name} -> Click Version -> Promote to Production")


if __name__ == '__main__':
    main()
