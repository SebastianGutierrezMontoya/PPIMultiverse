from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios
from .forms import PedidosForm, PedidosProductosForm, UsuariosForm
from django.db.models import F, ExpressionWrapper, DecimalField, Sum
from django.http import HttpResponseRedirect

#Categorias
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'

class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categoria_detail.html'

class CategoriaCreateView(CreateView):
    model = Categoria
    fields = '__all__'
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    fields = '__all__'
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_list')

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')



#Pedidos

class PedidosListView(ListView):
    model = Pedidos
    template_name = 'pedidos_list.html'

class PedidosDetailView(DetailView):
    model = Pedidos
    template_name = 'pedidos_detail.html'

def PedidosCreateView(request):
    Json = {}

    if request.method == 'POST':
        productos_seleccionados = request.POST.getlist('productos_seleccionados')
        id_pedido = request.POST.get('ped_id')

        form = PedidosForm(request.POST)
        if form.is_valid():
            
            form.save()
            PedidosProductosCreateView(productos_seleccionados, id_pedido)
            return redirect('pedidos_list')
    else:
        Prod = Productos.objects.values('prod_id', 'prod_nombre', 'prod_precio_venta', 'prod_stock')
        Json['Productos'] = Prod
        form = PedidosForm()
    # success_url = reverse_lazy('pedidos_list')
    
    Json['form'] = form
    
    return render(request, 'pedidos_form.html', Json )

def PedidosUpdateView(request, pk):
    pedido = get_object_or_404(Pedidos, pk=pk)
    productos_relacionados = PedidosProductos.objects.filter(ped=pedido).aggregate()

    productos_relacionados = (
    PedidosProductos.objects
    .filter(ped=pedido)
    .annotate(
        total=ExpressionWrapper(
            F('pped_precio_unitario') * F('pped_cantidad'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )
)

    if request.method == 'POST':
        form = PedidosForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            return redirect('pedidos_list')
    else:
        form = PedidosForm(instance=pedido)

    return render(request, 'pedidos_form.html', {
        'form': form,
        'object': pedido,
        'productos_relacionados': productos_relacionados,
    })

class PedidosDeleteView(DeleteView):
    model = Pedidos
    template_name = 'pedidos_confirm_delete.html'
    success_url = reverse_lazy('pedidos_list')

#PedidosProductos

def PedidosProductosCreateView(productos_seleccionados, id_pedido):

    for item in productos_seleccionados:
        prod_id, cantidad = item.split(',')
        producto = get_object_or_404(Productos, pk=prod_id)
        pedido = get_object_or_404(Pedidos, pk=id_pedido)
        pped_precio_unitario = producto.prod_precio_venta
        pped_cantidad = int(cantidad)

        PedidosProductos.objects.create(

            ped=pedido,
            prod=producto,
            pped_cantidad=pped_cantidad,
            pped_precio_unitario=pped_precio_unitario
        )

    

def PedidosProductosUpdateView(request, id_pedido):

    obj = get_object_or_404(PedidosProductos, id_pedido=id_pedido)

    if request.method == 'POST':
        form = PedidosProductosForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('pedidos_productos_list')  # o la vista a la que quieras volver
    else:
        form = PedidosProductosForm(instance=obj)

    return render(request, 'pedidos_productos_form.html', {'form': form})

class PedidosProductosDeleteView(DeleteView):
    model = PedidosProductos
    template_name = 'pedidos_productos_confirm_delete.html'
    success_url = reverse_lazy('pedidos_productos_list')

class PedidosProductosListView(ListView):
    model = PedidosProductos
    template_name = 'pedidos_productos_list.html'

class PedidosProductosDetailView(DetailView):
    model = PedidosProductos
    template_name = 'pedidos_productos_detail.html'

#Productos

class ProductosListView(ListView):
    model = Productos
    template_name = 'productos_list.html'

class ProductosDetailView(DetailView):
    model = Productos
    template_name = 'productos_detail.html'

class ProductosCreateView(CreateView):
    model = Productos
    fields = '__all__'
    template_name = 'productos_form.html'
    success_url = reverse_lazy('productos_list')
    

class ProductosUpdateView(UpdateView):
    model = Productos
    fields = '__all__'
    template_name = 'productos_form.html'
    success_url = reverse_lazy('productos_list')

class ProductosDeleteView(DeleteView):
    model = Productos
    template_name = 'productos_confirm_delete.html'
    success_url = reverse_lazy('productos_list')


#Usuarios

class UsuariosListView(ListView):
    model = Usuarios
    template_name = 'usuarios_list.html'

class UsuariosDetailView(DetailView):
    model = Usuarios
    template_name = 'usuarios_detail.html'

def UsuariosCreateView(request):
    Json = {}

    if request.method == 'POST':
        contactos_relacionados = request.POST.getlist('contactos_relacionados')
        id_usuario = request.POST.get('id_usuario')

        form = UsuariosForm(request.POST)
        if form.is_valid():
            form.save()
            ContactosCreateView(contactos_relacionados, id_usuario)
            return redirect('usuarios_list')
    else:
        form = UsuariosForm()

    Json['form'] = form
    return render(request, 'usuarios_form.html', Json )

def UsuariosUpdateView(request, pk):
   
    usuario = get_object_or_404(Usuarios, pk=pk)
    contactos_relacionados = Contactos.objects.filter(id_usuario=usuario)
    # contactos_relacionados_editados = request.POST.getlist('contactos_relacionados_editados')
    

    if request.method == 'POST':
        form = UsuariosForm(request.POST, instance=usuario)
        contactos_relacionados_nuevo = request.POST.getlist('contactos_relacionados')
        print("Contactos nuevos recibidos:", contactos_relacionados_nuevo)
        if form.is_valid():
            form.save()
            # Recibe los datos como lista de strings tipo "tipo_contacto,dato_contacto,id_contacto"
            contactos_data = request.POST.getlist('contactos_relacionados_editados')
            contactos_actualizar = []
            for item in contactos_data:
                # Si envías el id_contacto también, separa por coma
                # Ejemplo: "c,nuevo@email.com,1"
                parts = item.split(',')
                if len(parts) == 3:
                    tipo_contacto, dato_contacto, id_contacto = parts
                    contactos_actualizar.append({
                        'id_contacto': id_contacto,
                        'tipo_contacto': tipo_contacto,
                        'dato_contacto': dato_contacto,
                    })
                elif len(parts) == 2:
                    tipo_contacto, dato_contacto = parts
                    # Si no hay id_contacto, omite o busca por otro criterio
                    contactos_actualizar.append({
                        'tipo_contacto': tipo_contacto,
                        'dato_contacto': dato_contacto,
                    })
            ContactosUpdateView(contactos_actualizar)
            if contactos_relacionados_nuevo:
                ContactosCreateView(contactos_relacionados_nuevo, usuario.id_usuario)
            return redirect('usuarios_list')
    else:
   
        form = UsuariosForm(instance=usuario)

    return render(request, 'usuarios_form.html', {
        'form': form,
        'object': usuario,
        'contactos_relacionados': contactos_relacionados,
    })

class UsuariosDeleteView(DeleteView):
    model = Usuarios
    template_name = 'usuarios_confirm_delete.html'
    success_url = reverse_lazy('usuarios_list')

#Contactos

class ContactosListView(ListView):
    model = Contactos
    template_name = 'contactos_list.html'

class ContactosDetailView(DetailView):
    model = Contactos
    template_name = 'contactos_detail.html'

def ContactosCreateView(contactos_relacionados, id_usuario):
    print("Contactos a crear:", contactos_relacionados)
    for item in contactos_relacionados:
        id_con = Contactos.objects.count() + 1
        tipo_contacto, dato_contacto = item.split(',')
        usuario = get_object_or_404(Usuarios, pk=id_usuario)

        Contactos.objects.create(
            id_contacto=id_con,
            tipo_contacto=tipo_contacto,
            dato_contacto=dato_contacto,
            id_usuario=usuario
        )
    

def ContactosUpdateView(contactos_actualizar):
    print("Contactos a actualizar:", contactos_actualizar)
    """
    contactos_actualizar: lista de diccionarios con los campos a actualizar, por ejemplo:
    [
        {'id_contacto': 1, 'tipo_contacto': 'c', 'dato_contacto': 'nuevo@email.com'},
        {'id_contacto': 2, 'tipo_contacto': 't', 'dato_contacto': '123456789'},
        ...
    ]
    """
    for contacto_data in contactos_actualizar:
        contacto = get_object_or_404(Contactos, pk=contacto_data['id_contacto'])
        contacto.tipo_contacto = contacto_data.get('tipo_contacto', contacto.tipo_contacto)
        contacto.dato_contacto = contacto_data.get('dato_contacto', contacto.dato_contacto)
        contacto.save()

    

def ContactosDeleteView(request, pk):
    contacto = get_object_or_404(Contactos, pk=pk)
    contacto.delete()
    return HttpResponseRedirect(reverse_lazy('usuarios_list'))