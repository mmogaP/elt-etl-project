import os
from google.cloud import bigquery
from google.api_core import exceptions as gcp_exceptions

# Configuración del proyecto
PROJECT_ID = "elt-pipeline-473714" 
DATASET_STAGING = "staging"
DATASET_ANALYTICS = "analytics"
TABLE_SOURCE = f"{PROJECT_ID}.{DATASET_STAGING}.users"
TABLE_TARGET = f"{PROJECT_ID}.{DATASET_ANALYTICS}.users_clean"

os.environ['GCLOUD_PROJECT'] = PROJECT_ID

# Inicializar el cliente de BigQuery
try:
    client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"Error al inicializar el cliente de BigQuery: {e}")
    print("Asegúrate de que estás autenticado con 'gcloud auth application-default login'")
    exit()

# 1. SQL de Transformación (Crear o reemplazar la tabla limpia)
# La consulta calcula la edad a partir de la fecha de nacimiento (date_of_birth)
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

# 2. Función para verificar y crear el Dataset de Analytics
def ensure_dataset_exists(dataset_id):
    full_dataset_id = f"{client.project}.{dataset_id}"
    print(f"-> Verificando si el dataset {dataset_id} existe...")
    try:
        # Intenta obtener el dataset. Si no existe, lanza una excepción NotFound.
        client.get_dataset(full_dataset_id)
        print(f"-> Dataset '{dataset_id}' ya existe.")
    except gcp_exceptions.NotFound: # Uso de la excepción importada correctamente
        print(f"-> Dataset '{dataset_id}' no encontrado. Creándolo...")
        dataset = bigquery.Dataset(full_dataset_id)
        dataset.location = "us-central1" 
        client.create_dataset(dataset, timeout=30)
        print(f"-> Dataset '{dataset_id}' creado con éxito.")

# 3. Función para ejecutar la transformación
def run_transformation():
    print("--- Iniciando Proceso de Transformación (T) ---")

    # A. Asegurar que el dataset de destino existe
    ensure_dataset_exists(DATASET_ANALYTICS)

    # B. Configurar y ejecutar el Job de consulta
    job_config = bigquery.QueryJobConfig(
        default_dataset=client.dataset(DATASET_STAGING)
    )

    print(f"\n-> Ejecutando consulta de transformación para crear {TABLE_TARGET}...")
    print("--- SQL ---")
    print(TRANSFORMATION_SQL)
    print("-----------")
    
    # Iniciar el Job de BigQuery
    query_job = client.query(TRANSFORMATION_SQL, job_config=job_config)

    # Esperar que el Job termine
    print("-> Esperando que el Job de BigQuery finalice...")
    query_job.result() # Este método bloquea la ejecución hasta que el Job termina

    print("\n✅ ¡Transformación completada con éxito!")
    print(f"Tabla de destino: {TABLE_TARGET}")
    print(f"Filas procesadas: {query_job.total_bytes_processed / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    run_transformation()
