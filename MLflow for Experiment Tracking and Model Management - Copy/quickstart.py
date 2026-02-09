import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("SENTIMENT ANALYSIS - QUICK START MENU")
    print("=" * 80)
    
    options = {
        "1": ("Train Models with MLflow", "python scripts/train_with_mlflow.py"),
        "2": ("Add Tags and Register Model", "python scripts/add_tags_and_register.py"),
        "3": ("Run Prefect Workflow", "python scripts/prefect_flow.py"),
        "4": ("View MLflow Dashboard", "mlflow ui --host 127.0.0.1 --port 5000"),
        "5": ("Run Streamlit App", "streamlit run app/streamlit_app.py"),
        "6": ("Run Tests", "pytest tests/"),
        "0": ("Exit", None)
    }
    
    while True:
        print("\nOptions:")
        for key, (name, _) in options.items():
            print(f"  {key}. {name}")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
        
        if choice in options:
            name, cmd = options[choice]
            if cmd:
                print(f"\n{'=' * 80}")
                print(f"Running: {name}")
                print(f"{'=' * 80}\n")
                os.system(cmd)
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
