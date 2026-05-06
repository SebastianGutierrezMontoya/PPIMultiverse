# Guía de Despliegue — Multiverse Anime Store

## Requisitos del Sistema

- Python 3.13+
- PostgreSQL 16 (producción) o SQLite 3 (desarrollo)
- Git
- Tailscale (para conectar al servidor TARS)

## Estructura del Proyecto

```
PPIMultiverse/
├── PPIMultiverse/           ← settings, urls, wsgi
│   ├── settings.py          ← Producción (PostgreSQL)
│   └── settings_dev.py      ← Desarrollo (SQLite, en .gitignore)
├── MultiverseAnimeStore/    ← App principal
│   ├── models.py            ← 15 modelos
│   ├── views.py             ← Vistas CRUD + públicas
│   ├── forms.py             ← Formularios + ID generators
│   ├── signals.py           ← Django Signals (reemplazan triggers)
│   ├── middleware.py        ← Auth custom por sesión
│   ├── templates/           ← 68+ templates
│   └── static/              ← CSS, JS, imágenes
├── docs/                    ← Documentación
├── manage.py
└── requirements.txt
```

## Instalación (Desarrollo Local con SQLite)

```bash
# 1. Clonar repositorio
git clone https://github.com/SebastianGutierrezMontoya/PPIMultiverse.git
cd PPIMultiverse

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos (SQLite)
# settings_dev.py ya está configurado con SQLite
# Solo asegúrate de que settings_dev.py esté presente

# 5. Migrar base de datos
python manage.py migrate --settings=PPIMultiverse.settings_dev

# 6. Cargar datos iniciales
python manage.py seed_data --settings=PPIMultiverse.settings_dev

# 7. Iniciar servidor
python manage.py runserver --settings=PPIMultiverse.settings_dev
```

## Instalación (Producción con PostgreSQL)

### 1. Configurar PostgreSQL

```sql
-- Crear base de datos
CREATE DATABASE ppimultiverse_db;

-- Crear usuario
CREATE USER ppimultiverse WITH PASSWORD 'qwer1234';

-- Conceder permisos
GRANT ALL PRIVILEGES ON DATABASE ppimultiverse_db TO ppimultiverse;
```

### 2. Configurar settings.py

Editar `PPIMultiverse/settings.py` con los datos de conexión reales:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ppimultiverse_db',
        'USER': 'ppimultiverse',
        'PASSWORD': 'qwer1234',
        'HOST': 'localhost',     # o IP del servidor PostgreSQL
        'PORT': '5432',
    }
}
```

### 3. Migrar y poblar

```bash
python manage.py migrate
python manage.py seed_data   # Omitir --settings, usa settings.py por defecto
python manage.py createsuperuser
```

### 4. Verificar CHECK Constraints y Migraciones

```bash
python manage.py check
python manage.py showmigrations
```

Los CHECK constraints se crean automáticamente con las migraciones. Verificar en PostgreSQL:

```sql
SELECT conname, convalidated
FROM pg_constraint
WHERE conrelid = 'productos'::regclass;
```

### 5. Poblar base de datos

```bash
python manage.py seed_data
```

### 6. Ejecutar servidor

```bash
# Desarrollo
python manage.py runserver 0.0.0.0:8000

# Producción (usar Gunicorn u otro WSGI)
gunicorn PPIMultiverse.wsgi:application --bind 0.0.0.0:8000
```

## Despliegue en TARS (Servidor Linux con Tailscale)

```bash
# El servidor TARS tiene PostgreSQL 16 instalado.
# Conectar via Tailscale desde tu máquina local:
ssh tars@<tailscale-ip>

# En TARS:
cd /opt/PPIMultiverse
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# PostgreSQL ya está configurado, solo migrar:
python manage.py migrate
python manage.py collectstatic --noinput

# Reiniciar servicio:
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Credenciales por Defecto

| Usuario | Contraseña | Perfil |
|---------|-----------|--------|
| `admin` | `admin123` | Administrador completo |

## Variables de Entorno (Recomendado para Producción)

```bash
export DJANGO_SETTINGS_MODULE=PPIMultiverse.settings
export DATABASE_URL=postgres://ppimultiverse:qwer1234@localhost:5432/ppimultiverse_db
export SECRET_KEY=<random-secret-key>
```

## Tailscale (Red Privada entre Máquinas)

El proyecto se conecta entre 3 máquinas via Tailscale:
- PC Windows (desarrollo)
- Laptop Windows (desarrollo alterno)
- VM Linux + TARS (producción)

Cada máquina tiene SQLite para desarrollo local y PostgreSQL en TARS para producción.

## Notas Importantes

1. **settings.py** tiene config de PostgreSQL (producción) — NO se modifica
2. **settings_dev.py** tiene SQLite (desarrollo) — está en .gitignore, no se pushea
3. Las migraciones corren igual en SQLite y PostgreSQL (usar siempre `makemigrations` en local y `migrate` en ambos)
4. El comando `seed_data` es idempotente (usa `get_or_create`) — se puede ejecutar múltiples veces
5. Las Signals en `signals.py` están conectadas vía `apps.py.ready()`
