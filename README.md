# IA Responde - Documentación Técnica

## Inicio Rápido

### Levantar sin ngrok (desarrollo local)

```bash
# Terminal 1: Backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd ia-responde-frontend
npm start
```

### Levantar con Ngrok (acceso público)

**1. Iniciar el backend:**
```bash
uvicorn main:app --reload
```
El backend estará disponible en `http://localhost:8000`

**2. Exponer el backend con ngrok:**
```bash
npx ngrok http 8000
```
Copiá la URL pública generada (ej: `https://abc123.ngrok-free.app`)

**3. Configurar el frontend:**
Creá o editá el archivo `ia-responde-frontend/.env`:
```env
REACT_APP_API_URL=https://abc123.ngrok-free.app/ask
```
Reemplazá `https://abc123.ngrok-free.app` con tu URL de ngrok.

**4. Iniciar el frontend:**
```bash
cd ia-responde-frontend
npm start
```
El frontend estará disponible en `http://localhost:3000`

**5. (Opcional) Exponer el frontend con ngrok:**
Si querés que otras personas accedan a la interfaz web (además de vos en localhost:3000):
```bash
npx ngrok http 3000
```
Esto generará una URL pública adicional (ej: `https://xyz456.ngrok-free.app`) que podés compartir.
El frontend seguirá funcionando en `http://localhost:3000` para vos simultáneamente.

**Nota:** Recordá actualizar el archivo `.env` del frontend cada vez que reinicies ngrok, ya que la URL pública cambia (a menos que uses un dominio estático de ngrok con plan pago).

### Opción Híbrida: Frontend en Vercel + Backend local con Ngrok

Esta opción es ideal para compartir la aplicación sin tener que exponer el frontend con ngrok.

**1. Iniciar el backend:**
```bash
uvicorn main:app --reload
```

**2. Exponer el backend con ngrok:**
```bash
npx ngrok http 8000
```
Copiá la URL pública generada (ej: `https://abc123.ngrok-free.app`)

**3. Deploy del frontend en Vercel:**

```bash
cd ia-responde-frontend

# Crear archivo .env con la URL de ngrok
echo "REACT_APP_API_URL=https://abc123.ngrok-free.app/ask" > .env

# Deploy a Vercel (requiere cuenta gratuita)
npx vercel
```

Seguí las instrucciones del CLI de Vercel. Al finalizar te dará una URL permanente (ej: `https://ia-responde-mvp.vercel.app`)

**4. Configurar CORS en el backend:**

El backend ya está configurado para aceptar requests desde Vercel. Si usás otro dominio, editá `main.py` línea 165:

```python
allow_origins=[
    "http://localhost:3000",
    "https://tu-app.vercel.app"  # Agregá tu URL de Vercel
]
```

**Ventajas:**
- ✅ URL del frontend permanente (no cambia)
- ✅ No necesitás tener el frontend corriendo en tu máquina
- ✅ Ideal para demos o compartir con otros

**Desventajas:**
- ⚠️ La URL del backend (ngrok) sigue cambiando cada vez que reiniciás
- ⚠️ Tenés que actualizar el `.env` y re-deployar a Vercel cada vez que cambie la URL de ngrok

**Tip:** Para evitar re-deploys constantes, podés usar variables de entorno en Vercel Dashboard y solo actualizar ahí la URL cuando cambie.

---

Sistema de RAG local multi-cloud para consulta inteligente sobre documentos PDF usando LLMs y embeddings avanzados.

## Arquitectura

- **FastAPI**: API REST principal.
- **LangChain**: Orquestación de cadenas QA y procesamiento de texto.
- **ChromaDB**: Base vectorial local persistente.
- **Embeddings**: AWS Bedrock (cloud) o HuggingFace (local).
- **LLM**: AWS Bedrock (Claude 3) o Azure OpenAI (GPT-3.5/4).
- **PyMuPDF**: Extracción de texto de PDFs.
- **Pipeline automatizado**: Un solo comando para procesar, clasificar y levantar el sistema.
- **Fallback automático**: Si el proveedor cloud falla, se usa el siguiente disponible o embeddings locales.

## Estructura de Archivos

```
ia-responde-mvp/
├── pdfs/                # PDFs fuente
├── chroma_db/           # Base vectorial persistente
├── chunks.json          # Chunks procesados
├── .env                 # Configuración cloud/local
├── config.py            # Lógica multi-cloud
├── ingest.py            # Procesa PDFs y genera chunks
├── build_db.py          # Crea base vectorial con embeddings
├── clasifica_llm.py     # Clasifica chunks usando LLM vía API
├── main.py              # API REST
├── pipeline.py          # Pipeline automatizado
├── requirements.txt     # Dependencias
└── README.md            # Documentación técnica
```

## Flujo de Procesamiento Automatizado

Puedes ejecutar todo el pipeline con un solo comando:

```bash
python pipeline.py
```

Esto realiza automáticamente:
1. Procesa los PDFs y genera chunks (`ingest.py`)
2. Construye la base vectorial inicial (`build_db.py`)
3. Inicia el backend FastAPI (`main.py`)
4. Clasifica los chunks usando LLM (`clasifica_llm.py`)
5. Ejecuta nuevamente `build_db.py` para actualizar la base vectorial con los tipos clasificados
6. Detiene el backend al finalizar

## Flujo Manual (alternativo)

1. Procesar PDFs (`ingest.py`)
2. Construir base vectorial (`build_db.py`)
3. Iniciar API REST (`main.py`)
4. Clasificar chunks (`clasifica_llm.py`)
5. Ejecutar `build_db.py` nuevamente

## Configuración

- `.env`: Define credenciales y proveedor principal (`PRIMARY_CLOUD_PROVIDER=aws|azure`)
- AWS: Requiere configuración previa con `aws configure`
- Azure: Requiere endpoint, API key y deployment

## Dependencias

Ver `requirements.txt` para versiones y librerías requeridas.

**Instalación de dependencias Python:**
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

**Instalación de dependencias Frontend:**
```bash
cd ia-responde-frontend
npm install
```

## Configuración de Ngrok

**Primera vez:**
```bash
npm install -g ngrok
ngrok config add-authtoken TU_TOKEN_AQUI
```

Obtené tu token gratis en: https://dashboard.ngrok.com/get-started/your-authtoken

## Ejemplo de Uso - Pipeline Automatizado

```bash
# Pipeline automatizado (procesa PDFs, construye base vectorial, clasifica)
python pipeline.py

# Flujo manual
python ingest.py
python build_db.py
uvicorn main:app --reload
python clasifica_llm.py
python build_db.py
```

## Troubleshooting

- Verifica logs en nivel DEBUG para detalles de errores.
- Si `chunks.json` o `chroma_db/` no existen, ejecuta el pipeline o los scripts en orden.
- Revisa configuración cloud en `.env` y credenciales AWS/Azure.
- Para PDFs escaneados, se recomienda AWS Textract (no implementado en ingest.py actual).
- Si interrumpes el pipeline, los subprocesos se cierran limpiamente.

## Licencia

MIT
