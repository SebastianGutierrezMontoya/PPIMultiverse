from django import forms
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios, Sexos, EstadoPedidos, Perfiles, Consultas_Dinamicas, EstadoPedidos
from datetime import date as Date
from django.db import connection


def next_int_id(model, field_name):
    """
    Devuelve max(TO_NUMBER(field)) + 1 usando una consulta que solo considera valores totalmente numéricos.
    Fallback: devuelve model.objects.count() + 1 si hay cualquier problema.
    """
    table = model._meta.db_table
    # Consulta compatible con Oracle: toma solo valores que son enteros (regex) y obtiene el máximo
    sql = f"""
        SELECT MAX(
            CASE WHEN REGEXP_LIKE({field_name}, '^[0-9]+$') THEN TO_NUMBER({field_name}) ELSE NULL END
        ) FROM {table}
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            maxval = row[0] if row else None
            return int(maxval or 0) + 1
    except Exception:
        # fallback seguro
        return model.objects.count() + 1


def next_consecutive_id(model, field):
    ids = list(model.objects.order_by(field).values_list(field, flat=True))
    expected = 1

    for id_val in ids:
        if id_val != expected:
            return expected
        expected += 1

    return expected


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
        self.fields['ped_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['ped_id'].initial = next_int_id(Pedidos, 'ped_id')
        self.fields['ped_total'].widget.attrs['readonly'] = True
        self.fields['ped_total'].initial = 0.00
        self.fields['ped_direccion_envio'].widget.attrs.update({'placeholder': 'Ingrese la dirección de envío'})
        self.fields['ped_notas'].widget.attrs.update({'placeholder': 'Ingrese notas adicionales (opcional)'})
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['ped_fecha_pedido'].widget.attrs.update({'class': 'form-control datepicker'})
        self.fields['ped_notas'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        self.fields['ped_total'].widget.attrs.update({'class': 'form-control', 'step': '0.01'})
        self.fields['ped_fecha_pedido'].initial = Date.today()
        self.fields['ped_notas'].required = False

        
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
        self.fields['id_usuario'].initial = next_int_id(Usuarios, 'id_usuario')
        self.fields['activo'].widget.attrs.update({'min': 0, 'max': 1, 'step': '1'})
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget.attrs.update({'class': 'form-control datepicker'})
        self.fields['password_hash'].widget.attrs.update({'placeholder': 'Contraseña'})
        self.fields['activo'].required = False

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['cat_id', 'cat_nombre', 'cat_descripcion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cat_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id (cat_id es char; la función maneja solo valores numéricos)...
        self.fields['cat_id'].initial = str(next_int_id(Categoria, 'cat_id'))
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


class ProductosForm(forms.ModelForm):
    class Meta:
        model = Productos
        fields = ['prod_id', 'prod_nombre', 'prod_descripcion', 'prod_precio_venta', 'prod_stock','prod_descuento', 'cat']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cat'].queryset = Categoria.objects.all()
        self.fields['cat'].label_from_instance = lambda obj: obj.cat_nombre
        self.fields['prod_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['prod_id'].initial = str(next_int_id(Productos, 'prod_id'))
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['prod_precio_venta'].widget.attrs.update({'step': '0.01'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


class RolesForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ['id_rol', 'nombre', 'descripcion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_rol'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['id_rol'].initial = next_int_id(Roles, 'id_rol')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})


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
        self.fields['cons_id'].widget.attrs['readonly'] = True
        # ...cambiado: usar next_int_id en vez de count()+1...
        self.fields['cons_id'].initial = next_int_id(Consultas_Dinamicas, 'cons_id')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})

        self.fields['cons_sql'].widget.attrs.update({'class': 'form-control', 'rows': 5})

    def clean_sql_consulta(self):
        sql = self.cleaned_data['cons_sql']
        # Aquí podrías agregar validaciones adicionales para la consulta SQL si es necesario
        return sql
    
