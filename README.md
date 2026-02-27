# ChatPyme / AgenteIA

Repositorio **monorepo** que agrupa el backend en **FastAPI** y un frontend en **React**, diseñado para un ERP conversacional orientado a pymes colombianas. El backend expone APIs para inventarios y finanzas, mientras que la UI consume esos endpoints.

## 📂 Estructura Principal

```text
agenteia/
├─ Backend/            # Código Python + FastAPI
│  ├─ app.py           # Servidor Uvicorn
│  ├─ routes/          # Routers (inventory, financial, etc.)
│  └─ requirements.txt
├─ Frontend/           # Aplicación React (CRA)
│  ├─ src/             # Componentes y estilos
│  └─ package.json
└─ docker-compose.yml  # Orquesta DB, Backend y Frontend

```

## ✨ Funcionalidad Destacada

* **API REST**: Desarrollada con FastAPI y SQLAlchemy sobre PostgreSQL.
* **Módulos Iniciales**: Rutas preparadas para inventario y finanzas.
* **Seguridad**: CORS configurable mediante la variable `ALLOWED_ORIGINS`.
* **Interfaz**: UI en React con dashboard financiero e inventarios.
* **Extensibilidad**: Arquitectura de routers modulares en `app.py`.

---

## 🐳 Dockerización

Se proveen **Dockerfiles** separados y un archivo `docker-compose.yml` para levantar el stack completo de forma automática.

### Levantamiento rápido (Desarrollo)

```bash
# Desde la carpeta raíz: agenteia
docker-compose build   # Construye imágenes de backend y frontend
docker-compose up      # Inicia DB (5432), Backend (8000) y Frontend (3000)

```

> [!IMPORTANT]
> * El **Backend** monta el código local para permitir la recarga automática (*hot-reload*).
> * **Accesos**: Frontend en `http://localhost:3000` | API en `http://localhost:8000`.
> 
> 

#### Variables de entorno clave:

* `ENV`: `development` / `production`
* `DATABASE_URL`: Ejemplo: `postgresql://user:pass@db:5432/chatpyme`
* `ALLOWED_ORIGINS`: Lista blanca para CORS.

### Construir imágenes individuales

```bash
docker build -t chatpyme-backend:latest ./Backend
docker build -t chatpyme-frontend:latest ./Frontend

```

---

## 🚀 Despliegue en Producción

Para llevar el proyecto a la nube (GCP, AWS, Azure):

1. **Imágenes**: Sube las imágenes construidas a un registro (GCR, DockerHub).
2. **Configuración**:
* Elimina los `volumes` de desarrollo en el archivo compose.
* Cambia `ENV=production`.
* Ajusta `ALLOWED_ORIGINS` con el dominio real.


3. **Base de Datos**: Conecta el backend a una instancia gestionada (Cloud SQL, RDS, etc.).

---

## 🛠️ Scripts Útiles

### Backend (Local sin Docker)

Requiere Python 3.12 o superior.

```bash
cd Backend
env ENV=development python app.py

```

### Frontend (Local sin Docker)

```bash
cd Frontend
npm install
npm start          # Modo desarrollo
npm run build      # Genera carpeta build/ para producción

```

## 📝 Notas Adicionales

* **Seguridad**: El archivo `.env` en la carpeta `Backend` contiene secretos y **no debe versionarse**.
* **Base de Datos**: Se inicializa automáticamente; en modo `development` carga un *seed* de datos de prueba.
* **Proxy**: El `package.json` del frontend incluye un proxy hacia el backend para simplificar el flujo de desarrollo.
