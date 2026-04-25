# 🌌 PPIMultiverse - Anime Store

Plataforma de ventas de mercancía de anime. Proyecto universitario - Tecnología en Sistematización de Datos.

## 🚀 Stack

- **Backend:** Django 5.2.6 (Python 3.12)
- **Base de datos:** PostgreSQL 17
- **Frontend:** HTML, CSS, JavaScript + FontAwesome

## ⚡ Inicio rápido

```bash
# Clonar
git clone https://github.com/SebastianGutierrezMontoya/PPIMultiverse.git
cd PPIMultiverse

# Entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Dependencias
pip install -r requirements.txt

# Base de datos (crear BD primero)
createdb ppimultiverse_db
python manage.py migrate
python manage.py seed_data

# Iniciar servidor
python manage.py runserver
```

## 🏗️ Ramas

- `main` — versión estable
- `develop` — desarrollo activo

## 👤 Credenciales

- Admin app: `admin` / `admin123`
- Admin Django: `/admindjango/` (mismas credenciales)

## 📁 Estructura del proyecto

```
PPIMultiverse/
├── MultiverseAnimeStore/    # App principal
│   ├── templates/           # Plantillas HTML
│   ├── static/              # Archivos estáticos CSS/JS
│   ├── models.py            # Modelos de datos
│   ├── views.py             # Vistas y lógica de negocio
│   ├── forms.py             # Formularios Django
│   └── middleware.py         # Autenticación personalizada
├── PPIMultiverse/           # Configuración del proyecto Django
├── scripts/                 # Scripts de gestión (start/stop/status)
├── docs/                    # Documentación del proyecto
└── requirements.txt         # Dependencias Python
```

## 🛠️ Comandos útiles

```bash
# Iniciar servidor
./scripts/start.sh

# Detener servidor
./scripts/stop.sh

# Ver estado
./scripts/status.sh
```
