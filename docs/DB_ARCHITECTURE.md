# Arquitectura de Base de Datos — Multiverse Anime Store

## Stack

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Base de datos | PostgreSQL 16 | Producción (TARS server) |
| Base de datos (dev) | SQLite 3 | Desarrollo local (portable) |
| ORM | Django 5.2.6 | Abstracción de BD, migraciones |
| Capa de validación | Django Models + Forms | Reglas de negocio |
| Capa de aplicación | Python 3.13 | Lógica de negocio |

## Diagrama Relacional

Ver archivo: `DIAGRAMA RELACIONAL BD MULTIVERSE PROYECTO.png` (carpeta raíz del proyecto)

## Estructura de Conexión

### Producción (settings.py)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ppimultiverse_db',
        'USER': 'ppimultiverse',
        'PASSWORD': 'qwer1234',
        'HOST': 'localhost',  # o IP del servidor TARS via Tailscale
        'PORT': '5432',
    }
}
```

### Desarrollo local (settings_dev.py)
```python
from .settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
`settings_dev.py` hereda todo de `settings.py` y solo sobrescribe DATABASES. Está en `.gitignore` para no pushear config de SQLite.

### ¿Por qué PostgreSQL?

- **Gratuito y open source** — sin costos de licencia
- **Soporte nativo en Django** — `django.db.backends.postgresql`
- **Características robustas** — CHECK constraints, serial isolation, triggers PL/pgSQL
- **Ideal para producción** — manejo de concurrencia, rendimiento, seguridad
- **Transición desde Oracle** — PostgreSQL es el heredero natural de Oracle en el mundo open source

## Capas de Validación

### 1. Frontend (JavaScript)
- `register.js`: Valida nombre, teléfono, campos de dirección antes de enviar
- `cart-sidebar.js`: Valida nombre, teléfono, dirección en checkout modal
- La dirección se concatena con `" | "` antes de enviar: `"Calle 123 | Bogotá | Colombia | Chapinero"`

### 2. Backend (Django Views)
- `register_view`: Valida teléfono no vacío, nombre de usuario único
- `checkout_view`: Valida nombre y teléfono no vacíos, productos en carrito válidos
- `PedidosProductosCreateView`: Calcula totales con descuento

### 3. Señales (Signals)
- `validar_stock` (pre_save, PedidosProductos): Verifica stock suficiente contra la BD
- `validar_datos_pedido_producto` (pre_save, PedidosProductos): Verifica cantidad > 0, precio >= 0
- `descontar_stock_y_actualizar_total` (post_save, PedidosProductos): Decrementa stock y recalcula total del pedido

### 4. Base de Datos (PostgreSQL)
- **CHECK constraints**: Precio > 0, stock >= 0, descuento <= 99, total >= 0, activo IN (0,1)
- **Unique constraints**: Contactos (usuario, tipo_contacto)
- **Foreign Keys**: Todas las relaciones entre tablas

## Modelo de Contactos (Dirección Estructurada)

Los contactos de tipo "Dirección" almacenan la dirección como un texto estructurado:

```python
dato_contacto = "Calle 123 #45-67 | Bogotá | Colombia | Chapinero"
```

Separador: ` | ` (espacio-pipe-espacio). Para extraer con pandas:
```python
df['dato_contacto'].str.split(' \\| ', expand=True)
```

Campos: `calle | ciudad | país | barrio` (barrio opcional).

## Restricciones Implementadas

### CHECK Constraints
```sql
-- Productos
ALTER TABLE productos ADD CONSTRAINT ck_precio_positivo CHECK (prod_precio_venta > 0);
ALTER TABLE productos ADD CONSTRAINT ck_stock_no_negativo CHECK (prod_stock >= 0);
ALTER TABLE productos ADD CONSTRAINT ck_descuento_maximo CHECK (prod_descuento <= 99);

-- Pedidos
ALTER TABLE pedidos ADD CONSTRAINT ck_total_no_negativo CHECK (ped_total >= 0);

-- Usuarios
ALTER TABLE usuarios ADD CONSTRAINT ck_activo_valido CHECK (activo IN (0, 1));
```

### Unique Constraints
```sql
ALTER TABLE contactos ADD CONSTRAINT uq_usuario_tipo_contacto UNIQUE (id_usuario, tipo_contacto);
```

## Reemplazo de Triggers Oracle → Django Signals

| Trigger Oracle | Equivalente Django |
|---------------|-------------------|
| `trg_pedidos_productos` (valida stock) | `validar_stock` (Signal pre_save) |
| `trg_actualizar_stock` (decrementa) | `descontar_stock_y_actualizar_total` (Signal post_save) |
| `trg_actualizar_total_pedido` (recalcula) | `descontar_stock_y_actualizar_total` (Signal post_save) |
| `trg_validar_productos` (precio, stock, desc.) | CHECK constraints en BD |
| `trg_validar_usuarios` (edad, activo) | CHECK constraint + validación en form |
| `trg_validar_contactos` (regex, longitud) | Validación en frontend + form |
| `trg_validar_pedidos` (fecha futura) | Validación en form |
| `trg_actualizar_estado_pedido_padre` | No implementado (futuro) |

## IDs y Auto-increment

Actualmente los IDs de las tablas principales son manuales:

| Tabla | Formato ID | Ejemplo |
|-------|-----------|---------|
| Usuarios | `USR-{n}` | `USR-15` |
| Productos | `PROD{n}` | `PROD040` |
| Pedidos | `{n}` (entero) | `42` |
| Categorías | `CAT-{n}` | `CAT-1` |
| Contactos | `{n}` (entero) | `7` |

Para evitar race conditions, las funciones de generación de IDs (`get_next_id_model_name`, `next_int_id`) están envueltas en `transaction.atomic()` con `select_for_update()`. Esto serializa el acceso concurrente en PostgreSQL.

**En una versión futura**, se recomienda migrar a `AutoField` / `BigAutoField` de Django, que PostgreSQL implementa con `GENERATED AS IDENTITY`.

## Ejecución de Migraciones

```bash
# Generar migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado
python manage.py showmigrations
```

## Seed Data

El comando `seed_data` carga datos iniciales (ejecutable múltiples veces):
```bash
python manage.py seed_data --settings=PPIMultiverse.settings_dev
```

Carga:
- Sexos (3), Roles (2), Perfiles (2), Módulos (11)
- Perfilpermisos (11), EstadoPedidos (6)
- Config_Contacto (3), Categorías (7), Productos (22)
- Usuario admin: `admin` / `admin123`
