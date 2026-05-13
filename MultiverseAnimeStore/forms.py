from django import forms
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios, Sexos, EstadoPedidos, Perfiles, Consultas_Dinamicas, EstadoPedidos, Config_Contacto
from datetime import date as Date
from django.db import connection, transaction
from django.db.models import Max


def next_int_id(model, field_name):
    """
    Devuelve max(CAST(field AS INTEGER)) + 1.
    Envuelto en transacción con select_for_update para evitar race conditions en PostgreSQL.
    """
    table = model._meta.db_table
    sql = f"""
        SELECT MAX(
            CASE WHEN {field_name} ~ '^[0-9]+$' THEN {field_name}::integer ELSE NULL END
        ) FROM {table}
    """
    try:
        with transaction.atomic():
            model.objects.select_for_update().first()
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
                maxval = row[0] if row else None
                return int(maxval or 0) + 1
    except Exception:
        return model.objects.count() + 1


def next_consecutive_id(model, field):
    ids = list(model.objects.order_by(field).values_list(field, flat=True))
    expected = 1

    for id_val in ids:
        if id_val != expected:
            return expected
        expected += 1

    return expected


def get_next_id(value):
    import re
    match = re.search(r'(\d+)$', value)
    if match:
        return int(match.group(1)) + 1
    return 1


def get_next_id_model_name(model, field_name):
    """
    Recibe un modelo y el nombre del campo, obtiene el último valor del campo
    con select_for_update para evitar race conditions en PostgreSQL.
    """
    with transaction.atomic():
        last_obj = model.objects.select_for_update().order_by(f'-{field_name}').first()
        if last_obj:
            value = getattr(last_obj, field_name)
            return get_next_id(value)
        else:
            return 1


class PedidosForm(forms.ModelForm):
    class Meta:
        model = Pedidos
        fields = ['ped_id','usu', 'ped_fecha_pedido', 'ped_total', 'ped_direccion_envio', 'ped_notas']
        widgets = {
            'ped_fecha_pedido': forms.DateInput(attrs={'type': 'date'}),
            'ped_notas': forms.Textarea(attrs={'rows': 4}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usu'].queryset = Usuarios.objects.all()
        self.fields['usu'].label_from_instance = lambda obj: f"{obj.nombre} {obj.primer_apellido}"
        self.fields['usu'].required = True
        self.fields['ped_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['ped_id'].initial = next_int_id(Pedidos, 'ped_id')
        self.fields['ped_total'].widget.attrs['readonly'] = True
        self.fields['ped_total'].initial = 0.00
        self.fields['ped_direccion_envio'].widget.attrs.update({'placeholder': 'Ingrese la dirección de envío'})
        self.fields['ped_direccion_envio'].required = True
        self.fields['ped_notas'].widget.attrs.update({'placeholder': 'Ingrese notas adicionales (opcional)'})
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['ped_fecha_pedido'].widget.attrs.update({'class': 'form-control datepicker'})
        self.fields['ped_notas'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        self.fields['ped_total'].widget.attrs.update({'class': 'form-control', 'step': '0.01'})
        self.fields['ped_fecha_pedido'].initial = Date.today()
        self.fields['ped_notas'].required = False

        self.fields['ped_id'].label = "* ID del Pedido"
        self.fields['usu'].label = "* Usuario"
        self.fields['ped_fecha_pedido'].label = "* Fecha del Pedido"
        self.fields['ped_total'].label = "* Total del Pedido"
        self.fields['ped_direccion_envio'].label = "* Dirección de Envío"
        self.fields['ped_notas'].label = "Notas Adicionales"

        self.fields['ped_id'].widget.attrs['required'] = True
        self.fields['usu'].widget.attrs['required'] = True
        self.fields['ped_fecha_pedido'].widget.attrs['required'] = True
        self.fields['ped_total'].widget.attrs['required'] = True
        self.fields['ped_direccion_envio'].widget.attrs['required'] = True


        
        # self.fields['ped_estado'].initial = 1
        # self.fields['ped_notas'].widget.attrs.update({'class': 'form-control', 'rows': 4})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})
        

class PedidosProductosForm(forms.ModelForm):
    class Meta:
        model = PedidosProductos
        fields = ['ped', 'prod', 'pped_cantidad', 'pped_precio_unitario', 'pped_total', 'pped_descuento', 'pped_estado']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ped'].queryset = Pedidos.objects.all()
        self.fields['ped'].label_from_instance = lambda obj: f"Pedido {obj.ped_id}"
        self.fields['prod'].queryset = Productos.objects.all()
        self.fields['prod'].label_from_instance = lambda obj: f"{obj.prod_nombre} (ID: {obj.prod_id})"
        self.fields['pped_precio_unitario'].widget.attrs['readonly'] = True
        self.fields['pped_total'].widget.attrs['readonly'] = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['pped_cantidad'].widget.attrs.update({'min': 1})

        self.fields['pped_descuento'].widget.attrs['readonly'] = True
        self.fields['pped_estado'].queryset = EstadoPedidos.objects.all()
        self.fields['pped_estado'].label_from_instance = lambda obj: f"{obj.est_nombre}"
        self.fields['pped_estado'].initial = 1

        self.fields['ped'].label = "* Pedido"
        self.fields['prod'].label = "* Producto"
        self.fields['pped_cantidad'].label = "* Cantidad"
        self.fields['pped_precio_unitario'].label = "* Precio Unitario"
        self.fields['pped_descuento'].label = "Descuento"
        self.fields['pped_total'].label = "* Total"
        self.fields['pped_fecha_entrega'].label = "Fecha de Entrega"
        self.fields['pped_estado'].label = "* Estado"

        self.fields['ped'].widget.attrs['required'] = True
        self.fields['prod'].widget.attrs['required'] = True
        self.fields['pped_cantidad'].widget.attrs['required'] = True
        self.fields['pped_precio_unitario'].widget.attrs['required'] = True
        self.fields['pped_total'].widget.attrs['required'] = True
        self.fields['pped_estado'].widget.attrs['required'] = True

class PedidoProductoUpdateForm(forms.ModelForm):
    class Meta:
        model = PedidosProductos
        fields = [
            'ped',                 # solo lectura
            'prod',                # solo lectura
            'pped_cantidad',       # solo lectura
            'pped_precio_unitario',# solo lectura
            'pped_descuento',      # solo lectura
            'pped_total',          # solo lectura
            'pped_fecha_entrega',  # editable
            'pped_estado',         # editable
        ]
        widgets = {
            'pped_fecha_entrega': forms.DateInput(attrs={'type': 'date'}),
        }

    # Campos que deben mostrarse pero no deben poder modificarse
    read_only_fields = [
        'ped',
        'prod',
        'pped_cantidad',
        'pped_precio_unitario',
        'pped_descuento',
        'pped_total'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hacer los campos solo lectura
        for field_name in self.read_only_fields:
            field = self.fields[field_name]
            field.disabled = True 

        self.fields['ped'].label = "* Pedido"
        self.fields['prod'].label = "* Producto"
        self.fields['pped_cantidad'].label = "* Cantidad"
        self.fields['pped_precio_unitario'].label = "* Precio Unitario"
        self.fields['pped_descuento'].label = "Descuento"
        self.fields['pped_total'].label = "* Total"
        self.fields['pped_fecha_entrega'].label = "Fecha de Entrega"
        self.fields['pped_estado'].label = "* Estado"

        self.fields['ped'].widget.attrs['required'] = True
        self.fields['prod'].widget.attrs['required'] = True
        self.fields['pped_cantidad'].widget.attrs['required'] = True
        self.fields['pped_precio_unitario'].widget.attrs['required'] = True
        self.fields['pped_total'].widget.attrs['required'] = True
        self.fields['pped_estado'].widget.attrs['required'] = True


class UsuariosForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = [
            'id_usuario', 'nombre', 'primer_apellido', 'segundo_apellido',
            'fecha_nacimiento', 'password_hash', 'usuario_id_sexo', 'usuario_id_perfil', 'activo'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'password_hash': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario_id_sexo'].queryset = Sexos.objects.all()
        self.fields['usuario_id_sexo'].label_from_instance = lambda obj: obj.nombre_sexo
        self.fields['usuario_id_perfil'].queryset = Perfiles.objects.all()
        self.fields['usuario_id_perfil'].label_from_instance = lambda obj: obj.nombre
        self.fields['id_usuario'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['id_usuario'].initial = "USR-" + str(get_next_id_model_name(Usuarios, 'id_usuario'))
        self.fields['activo'].widget.attrs.update({'min': 0, 'max': 1, 'step': '1'})
        # Forzar required en campos obligatorios del usuario
        self.fields['nombre'].required = True
        self.fields['primer_apellido'].required = True
        self.fields['password_hash'].required = True
        self.fields['usuario_id_sexo'].required = True
        self.fields['usuario_id_perfil'].required = False
        self.fields['segundo_apellido'].required = False
        self.fields['fecha_nacimiento'].required = False
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget.attrs.update({'class': 'form-control datepicker'})
        self.fields['password_hash'].widget.attrs.update({'placeholder': 'Contraseña'})
        self.fields['activo'].required = False

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['id_usuario'].label = "* ID de Usuario"
        self.fields['nombre'].label = "* Nombre"
        self.fields['primer_apellido'].label = "Primer Apellido"
        self.fields['segundo_apellido'].label = "Segundo Apellido"
        self.fields['fecha_nacimiento'].label = "* Fecha de Nacimiento"
        self.fields['password_hash'].label = "* Contraseña"
        self.fields['usuario_id_sexo'].label = "* Sexo"
        self.fields['usuario_id_perfil'].label = "Perfil"
        self.fields['activo'].label = "* Activo (1 para sí, 0 para no)"

        self.fields['id_usuario'].widget.attrs['required'] = True
        self.fields['nombre'].widget.attrs['required'] = True
        self.fields['fecha_nacimiento'].widget.attrs['required'] = True
        self.fields['password_hash'].widget.attrs['required'] = True
        self.fields['usuario_id_sexo'].widget.attrs['required'] = True
        self.fields['activo'].widget.attrs['required'] = True



class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['cat_id', 'cat_nombre', 'cat_descripcion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cat_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id (cat_id es char; la función maneja solo valores numéricos)...
        self.fields['cat_id'].initial = "CAT-" + str(get_next_id_model_name(Categoria, 'cat_id'))
        self.fields['cat_nombre'].required = True
        self.fields['cat_descripcion'].required = False
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['cat_id'].label = "* ID de Categoría"
        self.fields['cat_nombre'].label = "* Nombre de Categoría"
        self.fields['cat_descripcion'].label = "Descripción de Categoría"

        self.fields['cat_id'].widget.attrs['required'] = True
        self.fields['cat_nombre'].widget.attrs['required'] = True


class ProductosForm(forms.ModelForm):
    class Meta:
        model = Productos
        fields = ['prod_id', 'prod_nombre', 'prod_descripcion', 'prod_precio_venta', 'prod_stock','prod_imagen_url','prod_descuento', 'cat']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cat'].queryset = Categoria.objects.all()
        self.fields['cat'].label_from_instance = lambda obj: obj.cat_nombre
        self.fields['cat'].required = True
        self.fields['prod_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        "usr-" + str(get_next_id_model_name(Usuarios, 'id_usuario'))

        self.fields['prod_id'].initial = "PROD-" + str(get_next_id_model_name(Productos, 'prod_id'))
        # Forzar required en campos que deben tener valor
        self.fields['prod_nombre'].required = True
        self.fields['prod_precio_venta'].required = False
        self.fields['prod_stock'].required = False
        self.fields['prod_descripcion'].required = False
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['prod_precio_venta'].widget.attrs.update({'step': '0.01'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['prod_id'].label = "* ID de Producto"
        self.fields['prod_nombre'].label = "* Nombre de Producto"
        self.fields['prod_descripcion'].label = "* Descripción de Producto"
        self.fields['prod_precio_venta'].label = "* Precio de Venta"
        self.fields['prod_stock'].label = "* Stock"
        self.fields['prod_imagen_url'].label = "URL de Imagen"
        self.fields['prod_descuento'].label = "* Descuento"
        self.fields['cat'].label = "Categoría"

        self.fields['prod_id'].widget.attrs['required'] = True
        self.fields['prod_nombre'].widget.attrs['required'] = True
        self.fields['prod_descripcion'].widget.attrs['required'] = True
        self.fields['prod_precio_venta'].widget.attrs['required'] = True
        self.fields['prod_stock'].widget.attrs['required'] = True
        self.fields['prod_descuento'].widget.attrs['required'] = True
    def clean_prod_precio_venta(self):
        valor = self.cleaned_data.get('prod_precio_venta')
        if valor is None or valor == '':
            return 0.00
        return valor

    def clean_prod_stock(self):
        valor = self.cleaned_data.get('prod_stock')
        if valor is None or valor == '':
            return 0
        return valor


class RolesForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ['id_rol', 'nombre', 'descripcion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_rol'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['id_rol'].initial = next_int_id(Roles, 'id_rol')
        self.fields['nombre'].required = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['id_rol'].label = "* ID de Rol"
        self.fields['nombre'].label = "* Nombre de Rol"
        self.fields['descripcion'].label = "Descripción de Rol"

        self.fields['id_rol'].widget.attrs['required'] = True
        self.fields['nombre'].widget.attrs['required'] = True

class PerfilesForm(forms.ModelForm):
    class Meta:
        model = Perfiles
        fields = ['id_perfil', 'nombre','rol_id', 'descripcion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # roles = Roles.objects.values('id_rol', 'nombre')
        self.fields['rol_id'].queryset = Roles.objects.all()
        self.fields['rol_id'].label_from_instance = lambda obj: obj.nombre
        self.fields['id_perfil'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['id_perfil'].initial = next_int_id(Perfiles, 'id_perfil')
        self.fields['nombre'].required = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['id_perfil'].label = "* ID de Perfil"
        self.fields['nombre'].label = "* Nombre de Perfil" 
        self.fields['rol_id'].label = "* Rol"
        self.fields['descripcion'].label = "Descripción de Perfil"

        self.fields['id_perfil'].widget.attrs['required'] = True
        self.fields['nombre'].widget.attrs['required'] = True
        self.fields['rol_id'].widget.attrs['required'] = True


class EstadoPedidosForm(forms.ModelForm):
    class Meta:
        model = EstadoPedidos
        fields = ['est_id', 'est_nombre']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['est_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        # self.fields['est_id'].initial = next_int_id(EstadoPedidos, 'est_id') # cambio aca
        self.fields['est_id'].initial = next_consecutive_id(EstadoPedidos, 'est_id')
        self.fields['est_id'].widget.attrs.update({'title': 'La id del estado de Entregado debe ser la mayor de todas' })
        self.fields['est_nombre'].required = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


        self.fields['est_id'].label = "* ID de Estado de Pedido"
        self.fields['est_nombre'].label = "* Nombre de Estado de Pedido"

        self.fields['est_id'].widget.attrs['required'] = True
        self.fields['est_nombre'].widget.attrs['required'] = True
        
class SexosForm(forms.ModelForm):
    class Meta:
        model = Sexos
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_sexo'].widget.attrs['readonly'] = True
        self.fields['id_sexo'].initial = next_int_id(Sexos, 'id_sexo')
        self.fields['nombre_sexo'].required = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


class ConsultasDinamicasForm(forms.ModelForm):
    class Meta:
        model = Consultas_Dinamicas
        fields = ['cons_id', 'cons_nombre', 'cons_descripcion', 'cons_sql']
        widgets = {
            'cons_sql': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['cons_id'].widget.attrs['readonly'] = True
        
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['cons_id'].initial = next_int_id(Consultas_Dinamicas, 'cons_id')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['cons_sql'].widget.attrs.update({'class': 'form-control', 'rows': 5})

        self.fields['cons_id'].label = "* ID de Consulta Dinámica"
        self.fields['cons_nombre'].label = "* Nombre de Consulta Dinámica"
        self.fields['cons_descripcion'].label = "Descripción de Consulta Dinámica"
        self.fields['cons_sql'].label = "* Consulta SQL"

        self.fields['cons_id'].widget.attrs['required'] = True
        self.fields['cons_nombre'].widget.attrs['required'] = True
        self.fields['cons_sql'].widget.attrs['required'] = True

    def clean_sql_consulta(self):
        sql = self.cleaned_data['cons_sql']
        # Aquí podrías agregar validaciones adicionales para la consulta SQL si es necesario
        return sql


 
class ConfigContactoForm(forms.ModelForm):
    class Meta:
        model = Config_Contacto
        fields = ['id_regla', 'nombre_contacto', 'descripcion', 'regex_val', 'min_length', 'max_length', 'mensaje_error']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_regla'].widget.attrs['readonly'] = True
        self.fields['id_regla'].initial = next_int_id(Contactos, 'id_regla')
        self.fields['nombre_contacto'].required = True
        self.fields['mensaje_error'].required = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})
        self.fields['id_regla'].label = "* ID de Regla de Contacto"
        self.fields['nombre_contacto'].label = "* Nombre de Regla de Contacto"
        self.fields['descripcion'].label = "Descripción de Regla de Contacto"
        self.fields['regex_val'].label = "Expresión Regular de Validación"
        self.fields['min_length'].label = "Longitud Mínima"
        self.fields['max_length'].label = "Longitud Máxima"
        self.fields['mensaje_error'].label = "* Mensaje de Error"
    