from django import forms
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios, Sexos, EstadoPedidos
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


class PedidosForm(forms.ModelForm):
    class Meta:
        model = Pedidos
        fields = ['ped_id','usu', 'ped_fecha_pedido', 'ped_total', 'ped_direccion_envio', 'ped_notas', 'ped_estado']
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

        self.fields['ped_estado'].queryset = EstadoPedidos.objects.all()
        self.fields['ped_estado'].label_from_instance = lambda obj: f"{obj.est_nombre}"
        self.fields['ped_estado'].initial = 1

        for field in self.fields.values():
            field.widget.attrs.update({'placeholder': ' '})
        

class PedidosProductosForm(forms.ModelForm):
    class Meta:
        model = PedidosProductos
        fields = ['ped', 'prod', 'pped_cantidad', 'pped_precio_unitario', 'pped_descuento', 'pped_estado']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ped'].queryset = Pedidos.objects.all()
        self.fields['ped'].label_from_instance = lambda obj: f"Pedido {obj.ped_id}"
        self.fields['prod'].queryset = Productos.objects.all()
        self.fields['prod'].label_from_instance = lambda obj: f"{obj.prod_nombre} (ID: {obj.prod_id})"
        self.fields['pped_precio_unitario'].widget.attrs['readonly'] = True
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['pped_cantidad'].widget.attrs.update({'min': 1})

        self.fields['pped_descuento'].widget.attrs['readonly'] = True
        self.fields['pped_estado'].queryset = EstadoPedidos.objects.all()
        self.fields['pped_estado'].label_from_instance = lambda obj: f"{obj.est_nombre}"
        self.fields['pped_estado'].initial = 1


class UsuariosForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = [
            'id_usuario', 'nombre', 'primer_apellido', 'segundo_apellido',
            'fecha_nacimiento', 'password_hash', 'usuario_id_sexo', 'usuario_id_rol', 'activo'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'password_hash': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuario_id_sexo'].queryset = Sexos.objects.all()
        self.fields['usuario_id_sexo'].label_from_instance = lambda obj: obj.nombre_sexo
        self.fields['usuario_id_rol'].queryset = Roles.objects.all()
        self.fields['usuario_id_rol'].label_from_instance = lambda obj: obj.nombre
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