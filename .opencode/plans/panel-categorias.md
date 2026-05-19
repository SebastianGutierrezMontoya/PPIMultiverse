# Plan: Panel Crear/Editar Categoría

## Archivos a modificar/crear

### 1. `views.py` — Agregar después de `panel_categorias_list` (line 1697)

- `panel_categorias_crear(request)`: GET → `CategoriaForm()` vacío, POST → valida + guarda + redirect
- `panel_categorias_editar(request, pk)`: GET → `CategoriaForm(instance=categoria)`, POST → actualiza + redirect
- Ambas con `@Login_requerido()` + check `perfil_id != 1`
- Template: `'Admin/panel_categoria_form.html'`
- Context: `form`, `section='categorias'`, `sidebar=0`, y si edita `object=categoria`

### 2. `urls.py` — Importar + rutas

```python
panel_categorias_crear,
panel_categorias_editar,

path('panel/categorias/crear/', panel_categorias_crear, name='panel_categorias_crear'),
path('panel/categorias/<str:pk>/editar/', panel_categorias_editar, name='panel_categorias_editar'),
```

### 3. Template `Admin/panel_categoria_form.html`

- Extiende `Admin/panel_base.html`
- Mismo estilo que `Admin/panel_producto_form.html` pero solo campos `cat_nombre` + `cat_descripcion`
- Header: "Crear Categoría" o "Editar: {nombre}"
- Botón Guardar + Cancelar

### 4. `Admin/panel_categorias.html`

- Botón "+ Nueva Categoría" (panel-btn-primary) en panel-actions
- Columna "Acciones" con Editar (link a panel_categorias_editar) + Eliminar (modal inline como productos_list.html)
