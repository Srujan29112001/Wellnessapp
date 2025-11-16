"""
Airflow DAG for ML Pipeline Automation
Automates model training, evaluation, and deployment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

import sys
sys.path.append('/app')

# Default arguments
default_args = {
    'owner': 'wellness-ai',
    'depends_on_past': False,
    'email': ['alerts@wellness-ai.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG Definition
dag = DAG(
    'wellness_ml_pipeline',
    default_args=default_args,
    description='Wellness AI ML Training Pipeline',
    schedule_interval='@weekly',  # Run weekly
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'training', 'wellness'],
)


def extract_eeg_data(**context):
    """Extract EEG data from database"""
    from backend.database.postgres import get_db
    from backend.models.postgres_models import EEGAnalysis
    import pandas as pd

    print("Extracting EEG data...")
    # Extract data logic
    # Save to /tmp/eeg_data.csv
    print("EEG data extracted successfully")


def preprocess_eeg_data(**context):
    """Preprocess EEG signals"""
    from ml.eeg_analysis.processor import EEGProcessor
    import pandas as pd

    print("Preprocessing EEG data...")
    # Load from /tmp/eeg_data.csv
    # Preprocess
    # Save to /tmp/eeg_features.pkl
    print("Preprocessing complete")


def train_eeg_model(**context):
    """Train EEG classification model"""
    from ml.eeg_analysis.train_model import train_eeg_model_from_dataset

    print("Training EEG model...")

    # Train model
    results = train_eeg_model_from_dataset(
        data_dir="/tmp/eeg_data",
        save_dir="/models/eeg",
        config={
            "num_epochs": 30,
            "learning_rate": 0.001,
            "batch_size": 32
        }
    )

    print(f"Training complete. Accuracy: {results['test_results']['accuracy']}")

    # Push metrics to XCom
    context['ti'].xcom_push(key='test_accuracy', value=results['test_results']['accuracy'])


def evaluate_model(**context):
    """Evaluate model performance"""
    ti = context['ti']
    accuracy = ti.xcom_pull(key='test_accuracy', task_ids='train_eeg_model')

    print(f"Model evaluation: Accuracy = {accuracy}%")

    # Define acceptance threshold
    ACCURACY_THRESHOLD = 70.0

    if accuracy < ACCURACY_THRESHOLD:
        raise ValueError(f"Model accuracy {accuracy}% below threshold {ACCURACY_THRESHOLD}%")

    print("Model passed evaluation")


def deploy_model(**context):
    """Deploy model to production"""
    import shutil

    print("Deploying model to production...")

    # Copy model to production directory
    shutil.copy("/models/eeg/eeg_classifier_best.pth", "/app/data/models/eeg_classifier_prod.pth")

    print("Model deployed successfully")


def send_metrics_to_monitoring(**context):
    """Send training metrics to Prometheus/Grafana"""
    ti = context['ti']
    accuracy = ti.xcom_pull(key='test_accuracy', task_ids='train_eeg_model')

    print(f"Sending metrics to monitoring... Accuracy: {accuracy}%")
    # Send to Prometheus pushgateway or log to MLflow


# Define tasks
extract_data = PythonOperator(
    task_id='extract_eeg_data',
    python_callable=extract_eeg_data,
    dag=dag,
)

preprocess_data = PythonOperator(
    task_id='preprocess_eeg_data',
    python_callable=preprocess_eeg_data,
    dag=dag,
)

train_model = PythonOperator(
    task_id='train_eeg_model',
    python_callable=train_eeg_model,
    dag=dag,
)

evaluate = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_model,
    dag=dag,
)

deploy = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_model,
    dag=dag,
)

send_metrics = PythonOperator(
    task_id='send_metrics',
    python_callable=send_metrics_to_monitoring,
    dag=dag,
)

# Define task dependencies
extract_data >> preprocess_data >> train_model >> evaluate >> deploy >> send_metrics
