# Plan: Proteger borrado de categorías con productos

## Problema
- `Productos.cat = ForeignKey(Categoria, models.DO_NOTHING)` — sin protección
- PostgreSQL: lanza IntegrityError → 500
- SQLite (sin FK enforcement): borra la categoría y los productos quedan huérfanos

## Solución — Opción C (Ocultar + Validar)

### 1. `views.py`
- **Línea 8**: Agregar `Count` al import: `from django.db.models import ..., Count`
- **`panel_categorias_list`**: Cambiar `Categoria.objects.all()` a `Categoria.objects.annotate(productos_count=Count('productos_set'))`
- **`CategoriaDeleteView`**: Agregar método `delete()` que verifica `Productos.objects.filter(cat=categoria).exists()` antes de borrar

### 2. `Admin/panel_categorias.html`
- Si `c.productos_count > 0`: mostrar "N productos" en gris en vez del botón Eliminar
- Si `c.productos_count == 0`: mostrar botón Eliminar (modal)
