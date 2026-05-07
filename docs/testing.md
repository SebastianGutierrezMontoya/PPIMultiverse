# Testing Guide — PPI Multiverse

## Stack

| Capa | Framework | Archivos |
|------|-----------|----------|
| Backend | Django TestCase (unittest) | `MultiverseAnimeStore/tests/test_*.py` |
| Frontend | (pendiente) | `MultiverseAnimeStore/static/Js/*.js` |

## Setup del entorno

Siempre usar `settings_dev.py` (SQLite local). **NUNCA correr tests sin `--settings`** o se cae por PostgreSQL.

### Opción 1: Variable de entorno (recomendada, una vez por terminal)

```powershell
$env:DJANGO_SETTINGS_MODULE="PPIMultiverse.settings_dev"
```

Después ya podés correr:

```powershell
venv\Scripts\python manage.py test MultiverseAnimeStore.tests
```

### Opción 2: Manual (cada comando)

```powershell
venv\Scripts\python manage.py test <ruta> --settings=PPIMultiverse.settings_dev
```

## Comandos frecuentes

```powershell
# Todos los tests
venv\Scripts\python manage.py test MultiverseAnimeStore.tests

# Solo un archivo
venv\Scripts\python manage.py test MultiverseAnimeStore.tests.test_models

# Solo una clase
venv\Scripts\python manage.py test MultiverseAnimeStore.tests.test_signals.ValidarStockSignalTest

# Solo un test específico
venv\Scripts\python manage.py test MultiverseAnimeStore.tests.test_signals.ValidarStockSignalTest.test_stock_insuficiente_rechazado

# Verboso (muestra nombre de cada test)
venv\Scripts\python manage.py test MultiverseAnimeStore.tests -v 2
```

## Estructura de tests

```
MultiverseAnimeStore/tests/
├── __init__.py
├── test_models.py       # CHECK constraints, UniqueConstraint
├── test_signals.py      # validar_stock, descontar_stock, validar_datos
├── test_helpers.py      # (próximamente) hash_password, get_next_id, _extract_db_message
├── test_views.py        # (próximamente) register, checkout, login
└── test_forms.py        # (próximamente) validaciones de formularios
```

## Ciclo de test

### Ley de hierro (para código NUEVO)

> No escribir código de producción sin un test fallando primero.

Para features nuevas el ciclo es:

1. **RED** → Escribís el test (sin implementar la feature)
2. **Verificás que falla** → `python manage.py test ...` → FALLA
3. **GREEN** → Escribís el código mínimo para que pase
4. **Verificás que pasa** → `python manage.py test ...` → PASA
5. **REFACTOR** → Limpiás, mantenés verde

### Para código existente (nuestro caso ahora)

1. Escribís el test que describe comportamiento actual
2. Lo corrés → debe pasar si el código funciona
3. Si **falla** → o el código tiene un bug (lo arreglás) o el test está mal (lo corregís)
4. Si **pasa** → el comportamiento está verificado

## Anatomía de un test

```python
from django.test import TestCase
from django.db import IntegrityError
from ..models import Productos, Categoria

class ProductosConstraintsTest(TestCase):
    def setUp(self):
        """Corre ANTES de cada test (crea datos)"""
        self.cat = Categoria.objects.create(cat_id="CAT-TEST", cat_nombre="Test")

    def test_descripcion_dice_que_prueba(self):
        """Los docstrings explican qué regla se prueba"""
        with self.assertRaises(IntegrityError):
            Productos.objects.create(
                prod_id="PROD-1", cat=self.cat, prod_precio_venta=0
            )
```

### Métodos clave de TestCase

| Método | Qué hace |
|--------|----------|
| `self.assertRaises(Excepcion)` | Espera que el bloque lance una excepción |
| `self.assertEqual(a, b)` | Verifica que a == b |
| `self.assertIsNone(x)` | Verifica que x is None |
| `self.assertTrue(x)` | Verifica que x es True |
| `self.assertIn(a, b)` | Verifica que a está en b |
| `self.client.get('/url/')` | Hace una petición GET de prueba |
| `self.client.post('/url/', data)` | Hace una petición POST de prueba |

## setUp vs setUpTestData

```python
class MiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Corre UNA VEZ antes de todos los tests de la clase.
           Usar para datos compartidos (más rápido)."""
        cls.usuario = Usuarios.objects.create(...)

    def setUp(self):
        """Corre ANTES de CADA test.
           Usar si cada test necesita datos frescos."""
        self.producto = Productos.objects.create(...)
```

## Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'psycopg2'` | Falta `--settings=PPIMultiverse.settings_dev` | Usar variable de entorno o flag |
| `IntegrityError` no se lanza cuando esperás | SQLite a veces no valida CHECK constraints al hacer `.save()` si el valor ya está en el objeto | Forzar `.full_clean()` o verificar con `select *` |
| Test pasa pero feature no funciona | El test no prueba lo correcto | Revisar qué valores se están comparando |
| `django.db.utils.OperationalError: no such table` | Migraciones no aplicadas | Django TestCase las aplica automáticamente |
