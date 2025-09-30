import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

PROJECT_ID = "elt-pipeline-473714" # 🔹 pon aquí tu project_id
BUCKET = "elt-demo-bucket"  # 🔹 tu bucket
DATASET = "staging"
TABLE = "users"

# Configuración de Dataflow
options = PipelineOptions(
    runner="DataflowRunner",
    project=PROJECT_ID,
    temp_location=f"gs://{BUCKET}/temp",
    region="us-central1"
)

# Esquema de la tabla en BigQuery
table_schema = {
    "fields": [
        {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "first_name", "type": "STRING", "mode": "NULLABLE"},
        {"name": "last_name", "type": "STRING", "mode": "NULLABLE"},
        {"name": "email", "type": "STRING", "mode": "NULLABLE"},
        {"name": "date_of_birth", "type": "DATE", "mode": "NULLABLE"},
        {"name": "country", "type": "STRING", "mode": "NULLABLE"},
        {"name": "signup_date", "type": "DATE", "mode": "NULLABLE"},
        {"name": "is_active", "type": "BOOL", "mode": "NULLABLE"}
    ]
}

# Función para parsear cada línea del CSV
def parse_csv(line):
    fields = line.split(",")
    return {
        "id": int(fields[0]),
        "first_name": fields[1],
        "last_name": fields[2],
        "email": fields[3],
        "date_of_birth": fields[4],
        "country": fields[5],
        "signup_date": fields[6],
        "is_active": fields[7].lower() in ("true", "1", "yes")
    }

# Definición del pipeline
with beam.Pipeline(options=options) as p:
    (
        p
        | "Leer CSV" >> beam.io.ReadFromText(f"gs://{BUCKET}/users.csv", skip_header_lines=1)
        | "Parsear CSV" >> beam.Map(parse_csv)
        | "Escribir en BigQuery" >> beam.io.WriteToBigQuery(
            table=f"{PROJECT_ID}:{DATASET}.{TABLE}",
            schema=table_schema,
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )
    )
