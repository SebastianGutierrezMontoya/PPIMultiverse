from django import forms
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios
from datetime import date as Date


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
        self.fields['ped_id'].initial = Pedidos.objects.count() + 1
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
        

class PedidosProductosForm(forms.ModelForm):
    class Meta:
        model = PedidosProductos
        fields = ['ped', 'prod', 'pped_cantidad', 'pped_precio_unitario']
        
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