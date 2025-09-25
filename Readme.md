# ELT Data Pipeline Project

Este proyecto implementa un pipeline de datos ELT (Extract, Load, Transform) usando Apache Airflow, PostgreSQL y dbt. El pipeline extrae datos de una base de datos fuente, los carga en una base de datos destino, y luego los transforma usando dbt.

## Arquitectura del Proyecto

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source DB     │    │ Destination DB  │    │   Transform     │
│  (PostgreSQL)   │───▶│  (PostgreSQL)   │───▶│     (dbt)       │
│   Port: 5433    │    │   Port: 5434    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Airflow      │
                    │  (Orchestrator) │
                    │   Port: 8080    │
                    └─────────────────┘
```

## Componentes del Sistema

### 1. Base de Datos Fuente (Source PostgreSQL)

- **Puerto**: 5433
- **Base de datos**: `source_db`
- **Contenido**: Datos originales con tablas de películas, actores y usuarios
- **Tablas principales**:
  - `films`: Información de películas con ratings y precios
  - `actors`: Lista de actores
  - `film_actors`: Relación many-to-many entre películas y actores
  - `users`: Información básica de usuarios
  - `film_category`: Categorías de películas

### 2. Base de Datos Destino (Destination PostgreSQL)

- **Puerto**: 5434
- **Base de datos**: `destination_db`
- **Propósito**: Almacén de datos donde se cargan los datos extraídos

### 3. Apache Airflow

- **Puerto**: 8080
- **Usuario/Contraseña**: `airflow/password`
- **Función**: Orquestador del pipeline ELT
- **DAG principal**: `elt_and_dbt`

### 4. dbt (Data Build Tool)

- **Propósito**: Transformación de datos (T en ELT)
- **Modelos**: Transformaciones SQL para generar insights de negocio

## Proceso ELT

### E - Extract & Load

El script `elt/elt_script.py` realiza la extracción y carga:

1. **Extracción**: Usa `pg_dump` para extraer todos los datos de `source_db`
2. **Carga**: Usa `psql` para cargar los datos en `destination_db`
3. **Resultado**: Los datos se replican completamente sin transformaciones

**Archivos involucrados**:

- `elt/elt_script.py`: Script principal de extracción y carga
- `airflow/dags/elt_dag.py`: DAG de Airflow que orquesta el proceso

### T - Transform

dbt se encarga de las transformaciones sobre los datos ya cargados:

**Modelos implementados**:

- `films.sql`: Vista básica de películas
- `actors.sql`: Vista básica de actores
- `film_actors.sql`: Vista de relaciones película-actor
- `film_ratings.sql`: **Modelo principal** que agrega:
  - Categorización de ratings (Excellent, Good, Average, Poor)
  - Lista de actores por película
  - Conteo de actores
  - Rating promedio de actores
- `specific_movie.sql`: Consulta específica para una película (ejemplo con 'Dunkirk')

**Macro personalizada**:

- `generate_film_ratings()`: Macro compleja que genera el modelo de ratings agregados

## Estructura de Archivos

```
├── airflow/
│   └── dags/
│       └── elt_dag.py          # DAG principal de Airflow
├── custom_postgres/            # Proyecto dbt
│   ├── models/
│   │   └── example/           # Modelos de transformación
│   ├── macros/                # Macros personalizadas
│   └── dbt_project.yml        # Configuración dbt
├── elt/
│   ├── elt_script.py          # Script ELT principal
│   └── Dockerfile             # Container para ELT
├── source_db_init/
│   └── init.sql               # Datos iniciales
├── docker-compose.yml         # Orquestación de contenedores
└── Dockerfile                 # Imagen Airflow personalizada
```

## Instalación y Ejecución

### Prerrequisitos

- Docker y Docker Compose
- Al menos 4GB de RAM disponible

### Pasos de instalación

1. **Clonar el repositorio**

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Configurar rutas en Windows**

   Editar `airflow/dags/elt_dag.py` y actualizar las rutas en los mounts:

   ```python
   Mount(source=r'C:\Users\TU_USUARIO\ruta\al\proyecto\custom_postgres',
         target='/dbt', type='bind'),
   Mount(source=r'C:\Users\TU_USUARIO\.dbt',
         target='/root', type='bind'),
   ```

3. **Configurar perfil dbt**

   Crear/editar `~/.dbt/profiles.yml`:

   ```yaml
   custom_postgres:
     target: dev
     outputs:
       dev:
         type: postgres
         host: destination_postgres
         user: postgres
         password: secret
         port: 5432
         dbname: destination_db
         schema: public
         threads: 4
   ```

4. **Iniciar servicios**

   ```bash
   docker-compose up -d
   ```

5. **Acceder a Airflow**

   - URL: http://localhost:8080
   - Usuario: `airflow`
   - Contraseña: `password`

6. **Ejecutar el pipeline**
   - En la interfaz de Airflow, activar el DAG `elt_and_dbt`
   - Ejecutar manualmente o esperar la programación automática

## Verificación del Pipeline

### 1. Verificar Extracción y Carga

```bash
# Conectar a la base de datos destino
docker exec -it <destination_postgres_container> psql -U postgres -d destination_db

# Verificar que las tablas existen
\dt

# Verificar datos
SELECT COUNT(*) FROM films;
SELECT COUNT(*) FROM actors;
```

### 2. Verificar Transformaciones dbt

```bash
# Verificar la tabla transformada principal
SELECT * FROM film_ratings LIMIT 5;

# Verificar categorización de ratings
SELECT rating_category, COUNT(*)
FROM film_ratings
GROUP BY rating_category;
```

## Datos de Ejemplo

El proyecto incluye datos de ejemplo con:

- **20 películas** populares con información completa
- **20 actores** asociados a las películas
- **14 usuarios** de ejemplo
- **Múltiples categorías** por película
- **Ratings de usuarios** entre 1-5

## Tecnologías Utilizadas

- **Apache Airflow 2.x**: Orquestación de workflows
- **PostgreSQL 15**: Base de datos fuente y destino
- **dbt 1.4.7**: Transformaciones SQL
- **Docker & Docker Compose**: Containerización
- **Python 3.8+**: Scripts de automatización
