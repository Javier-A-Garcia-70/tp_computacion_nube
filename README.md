# LoreChat Holmes MVP

Sistema RAG para consulta inteligente sobre el corpus de Sherlock Holmes (Conan Doyle). Las respuestas se generan en primera persona con el estilo deductivo del personaje.

## Stack

| Capa | Tecnología |
|------|-----------|
| LLM | Anthropic API — Claude 3.5 Sonnet |
| Embeddings | Voyage AI — voyage-3 |
| Vector DB | pgvector (DigitalOcean Managed PostgreSQL) |
| API | FastAPI + uvicorn |
| Frontend | React (Vercel) |
| Deploy backend | Docker — DigitalOcean App Platform |

---

## Estructura del proyecto

```
tp_computacion_nube/
├── pdfs/                     # PDFs fuente (no se commitean)
├── .env                      # Variables de entorno locales (no se commitea)
├── .env.example              # Plantilla de variables de entorno
├── config.py                 # Configuración (Anthropic + Voyage AI + pgvector)
├── ingest.py                 # Procesa PDFs → chunks.json
├── build_db.py               # Genera embeddings y carga pgvector
├── main.py                   # API REST (FastAPI)
├── cli_ask.py                # Cliente CLI interactivo
├── pipeline.py               # Pipeline local completo
├── requirements.txt          # Dependencias Python
├── Dockerfile                # Imagen para DO App Platform
├── .dockerignore
└── ia-responde-frontend/     # Frontend React
```

---

## Configuración inicial

### 1. Variables de entorno

Copiá `.env.example` a `.env` y completá los valores:

```env
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
VOYAGE_MODEL=voyage-3
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

### 3. Frontend

```bash
cd ia-responde-frontend
npm install
```

---

## Flujo de uso local

### Procesar PDFs y cargar la base vectorial

```bash
# 1. Poner los PDFs de Holmes en la carpeta /pdfs

# 2. Procesar PDFs → chunks.json
python ingest.py

# 3. Generar embeddings y cargar pgvector
python build_db.py

# 4. Levantar el backend
uvicorn main:app --reload
```

### CLI interactivo

```bash
# Modo Holmes (responde como Sherlock)
python cli_ask.py --holmes

# Modo directo (sin persona)
python cli_ask.py
```

Comandos dentro del CLI:
- `:f` — ver fuentes del último resultado
- `exit` / `salir` — cerrar

---

## Deploy en DigitalOcean

### PostgreSQL + pgvector

1. Panel DO → Databases → Create PostgreSQL cluster
2. Conectarse y ejecutar:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Copiar la `DATABASE_URL` que provee DO

### App Platform (backend)

1. DO detecta el `Dockerfile` automáticamente al conectar el repo
2. Cargar las variables secretas:
   - `ANTHROPIC_API_KEY`
   - `VOYAGE_API_KEY`
   - `DATABASE_URL`
3. Hacer deploy → DO devuelve la URL pública

### Cargar datos en producción

Con `DATABASE_URL` de DO en el `.env` local:

```bash
python ingest.py
python build_db.py
```

### Frontend (Vercel)

Configurar la variable de entorno en el dashboard de Vercel:
```
REACT_APP_API_URL=https://<url-do-app-platform>/ask
```

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del sistema |
| POST | `/ask` | Consulta al corpus |

### Ejemplo `/ask`

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Quién es Irene Adler?"}'
```

---

## Licencia

MIT
