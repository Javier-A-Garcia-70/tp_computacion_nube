uvicorn main:app --reload
cd ia-responde-frontend && npm start

# 📚 IA Responde - Guía Paso a Paso para el Usuario

¿Querés preguntarle a tus PDFs usando inteligencia artificial? Seguí estos pasos y tendrás tu propio sistema de consulta en minutos.

---

## 1. Instalación rápida

1. **Descargá el proyecto**
   ```bash
   git clone <URL-del-repo>
   cd ia-responde-mvp
   ```

2. **Instalá las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. Configuración inicial

### Elegí tu proveedor de IA

- **AWS (recomendado para PDFs escaneados y mayor compatibilidad)**
  1. Configurá tus credenciales:
     ```bash
     aws configure
     ```
  2. Completá los datos que te pide (Access Key, Secret, región).

- **Azure (opcional, para usar GPT de OpenAI)**
  1. Conseguí tu endpoint, API key y nombre de deployment en Azure OpenAI.
  2. Copiá el archivo de ejemplo y editá tus datos:
     ```bash
     cp .env.example .env
     ```
  3. Editá el archivo `.env` con tus datos de Azure y/o AWS.

### Configurá el proveedor principal

En el archivo `.env`, pon:
```
PRIMARY_CLOUD_PROVIDER=aws
```
o
```
PRIMARY_CLOUD_PROVIDER=azure
```

---

## 3. Prepará tus documentos

1. Creá la carpeta `pdfs` si no existe:
   ```bash
   mkdir pdfs
   ```
2. Copiá ahí todos los PDFs que quieras consultar.

---

## 4. Pipeline automatizado (recomendado)

Podés ejecutar todo el proceso con un solo comando:

```bash
python pipeline.py
```

Esto realiza automáticamente:
1. Procesa los PDFs y genera chunks
2. Construye la base de conocimiento
3. Inicia la API
4. Clasifica los chunks usando IA
5. Actualiza la base de conocimiento con los tipos clasificados
6. Detiene la API al finalizar

---

## 5. Flujo manual (alternativo)

Si preferís hacerlo paso a paso:

```bash
python ingest.py
python build_db.py
uvicorn main:app --reload
python clasifica_llm.py
python build_db.py
```

---

## 6. Hacé tu primera pregunta
Levanta el servidor para que puedas hacer preguntas:
```bash
uvicorn main:app --reload
Usá `curl`, Postman o cualquier cliente HTTP para preguntar. Ejemplo con curl:
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "¿Qué dice el manual sobre vacaciones?"}'
```

**¿Qué vas a recibir?**
```json
{
  "answer": "Según el Manual del Empleado, tienes 21 días hábiles anuales...",
  "sources": [
    {
      "source": "Manual_Empleado.pdf",
      "chunk_id": 3,
      "tipo": "desconocido",
      "preview": "Según el Manual del Empleado, tienes 21 días hábiles..."
    }
  ],
  "llm_provider": "aws",
  "embedding_provider": "aws"
}
```
- **answer**: la respuesta generada por la IA.
- **sources**: fragmentos de tus PDFs usados para responder.
- **llm_provider**: proveedor de IA usado (aws o azure).
- **embedding_provider**: proveedor de embeddings usado.

---

## 7. Cambiá de proveedor de IA (opcional)

Podés cambiar entre AWS y Azure en cualquier momento:
```bash
curl -X POST "http://localhost:8000/switch-provider?provider=azure"
```

---

## 8. Agregá más PDFs cuando quieras

1. Copiá los nuevos PDFs a la carpeta `pdfs/`.
2. Volvé a correr el pipeline o los pasos manuales.

---

## 9. ¿Cómo sé si todo funciona?

- Si la API responde a `/health` con status "healthy", está OK:
  ```bash
  curl localhost:8000/health
  ```
- Si recibís respuestas a tus preguntas, ¡ya está listo!
- Si hay errores, revisá los mensajes en la terminal.

---

## Preguntas frecuentes

**¿Mis PDFs se suben a internet?**  
No, todo el procesamiento es local. Solo si usás AWS Textract (no implementado por defecto) se suben temporalmente.

**¿Qué PDFs funcionan mejor?**  
Los PDFs digitales (Word, Excel, etc.) funcionan perfecto. Los escaneados requieren AWS y configuración extra.

**¿Puedo usarlo sin internet?**  
No, necesitás conexión para la IA (AWS/Azure).

**¿Puedo agregar más documentos después?**  
Sí, solo agregalos a `pdfs/` y repetí el pipeline o los pasos manuales.

**¿Qué hago si algo falla?**  
- Revisá la carpeta `pdfs/` y que los archivos sean válidos.
- Verificá tu configuración en `.env`.
- Consultá los logs en la terminal para más detalles.

---

## Resumen rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env y proveedor

# 3. Agregar PDFs a pdfs/

# 4. Ejecutar pipeline automatizado
python pipeline.py

# 5. Hacer preguntas
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "¿Qué dice el manual sobre vacaciones?"}'
```

---

¡Listo! Ahora podés preguntarle a tus PDFs usando IA, de forma local y segura.
