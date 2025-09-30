from __future__ import annotations

import datetime

from airflow.models.dag import DAG
# Se elimina DataflowStartFlexTemplateOperator ya que usamos BashOperator para el script de Python.
# CAMBIO CLAVE: Se usa BigQueryInsertJobOperator para ejecutar consultas.
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator 
from airflow.operators.bash import BashOperator

# --- CONFIGURACIÓN DE TU PROYECTO ---
PROJECT_ID = "elt-pipeline-473714" 
BUCKET = "elt-demo-bucket" 
REGION = "us-central1"
DATASET_STAGING = "staging"
DATASET_ANALYTICS = "analytics"
TABLE_SOURCE = f"{PROJECT_ID}.{DATASET_STAGING}.users"
TABLE_TARGET = f"{PROJECT_ID}.{DATASET_ANALYTICS}.users_clean"
# La ruta del script de Dataflow. Debe ser accesible por el worker de Composer.
# Asume que dataflow_users.py fue subido a la misma carpeta donde se ejecuta el DAG.
GCS_DF_SCRIPT = "./dataflow_users.py" 
# --- FIN CONFIGURACIÓN ---

# 1. SQL de Transformación
TRANSFORMATION_SQL = f"""
CREATE OR REPLACE TABLE `{TABLE_TARGET}`
AS
SELECT
  id,
  first_name,
  last_name,
  email,
  DATE_DIFF(CURRENT_DATE(), DATE(date_of_birth), YEAR) AS age,
  country,
  signup_date,
  is_active
FROM `{TABLE_SOURCE}`;
"""

# 2. Definición del DAG
with DAG(
    dag_id="elt_users_pipeline",
    start_date=datetime.datetime(2023, 1, 1),
    schedule=None, # Deja en 'None' para ejecución manual
    catchup=False,
    tags=["elt", "bigquery", "dataflow"],
) as dag:
    
    # 2.1. Tarea de Ejecución de Dataflow (EL - Extract & Load)
    # Ejecuta tu script de Python, que internamente inicia el job de Dataflow.
    # NOTA: Requiere que el entorno de Airflow tenga instalados apache-beam y las librerías de GCP.
    run_dataflow_job = BashOperator(
        task_id="run_dataflow_el_step",
        bash_command=f"python {GCS_DF_SCRIPT}", 
    )


    # 2.2. Tarea de Transformación (T - Transform)
    # Ejecuta la consulta SQL de BigQuery (CREATE OR REPLACE TABLE).
    transform_data = BigQueryInsertJobOperator(
        task_id="transform_data_to_analytics",
        configuration={
            "query": {
                "query": TRANSFORMATION_SQL,
                "useLegacySql": False,
                # Definición de la tabla de destino
                "destinationTable": {
                    "projectId": PROJECT_ID,
                    "datasetId": DATASET_ANALYTICS,
                    "tableId": "users_clean",
                },
                # Estos son redundantes con el SQL, pero buena práctica de Airflow
                "createDisposition": "CREATE_IF_NEEDED", 
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
        gcp_conn_id="google_cloud_default", 
    )

    # 2.3. Tarea de Limpieza (Opcional)
    # Limpia la carpeta temporal de Dataflow en Cloud Storage
    cleanup_temp = BashOperator(
        task_id="cleanup_cloud_storage_temp",
        bash_command=f"gsutil -m rm -r gs://{BUCKET}/temp/*",
    )

    # 3. Definición de las dependencias
    run_dataflow_job >> transform_data >> cleanup_temp