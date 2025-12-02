# Portfolio ETL/Reporting API

Pequeño backend FastAPI que expone un pipeline ETL modular, scheduler estilo cola y renderizado a HTML/PDF para datasets CSV de ejemplo.

## Características
- Endpoints REST para subir archivos, iniciar jobs y revisar estado/resultados.
- Pipeline `ingest` → `validate` → `metrics` → `render` con reglas de negocio y validación de esquema.
- Scheduler/cola con worker en segundo plano, cron configurable y reintentos registrados en SQLite.
- Renderizado de HTML (Jinja2) y PDF (fpdf2); almacenamiento local simulando filesystem/S3.
- Autenticación básica por token y límites de tamaño en uploads.
- Dataset de ejemplo incluido y scripts de arranque.

## Requisitos previos
- Python 3.11+

## Instalación rápida
```bash
make install
```

## Ejecutar API
```bash
API_TOKEN=secret-token make run
```

Endpoints clave (requieren cabecera `token: <API_TOKEN>`):
- `POST /upload` (multipart `file`)
- `POST /jobs/start` cuerpo `{ "input_path": "backend/data/sample_dataset.csv" }`
- `GET /jobs/{id}` estado/metricas
- `GET /jobs/{id}/preview` HTML renderizado
- `GET /jobs/{id}/download` PDF generado

## Scheduler y reintentos
El scheduler levanta un worker en segundo plano y soporta cron expresado en formato estándar (`0 * * * *` por defecto). Puede configurarse programáticamente desde `JobScheduler.schedule_cron` para reingestar el dataset de ejemplo.

## Scripts útiles
- `backend/scripts/bootstrap.sh`: crea entorno virtual e instala dependencias.
- `backend/scripts/run_server.sh`: lanza la API con recarga en caliente.

## Dataset de ejemplo
`backend/data/sample_dataset.csv` contiene transacciones con columnas `id, customer, amount, category, timestamp` que cumplen el esquema mínimo de validación.

## Estructura
```
backend/
  app.py              # FastAPI + endpoints REST
  etl/                # ingest, validate, metrics y render
  jobs/               # scheduler, cola y persistencia de jobs
  storage/            # abstracción de almacenamiento local/S3 mock
  templates/          # report.html (HTML para previsualización)
  data/               # sample_dataset.csv y jobs.db (runtime)
```
