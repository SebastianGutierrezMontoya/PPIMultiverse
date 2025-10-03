from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios
from .forms import PedidosForm, PedidosProductosForm

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

#Contactos

class ContactosListView(ListView):
    model = Contactos
    template_name = 'contactos_list.html'

class ContactosDetailView(DetailView):
    model = Contactos
    template_name = 'contactos_detail.html'

class ContactosCreateView(CreateView):
    model = Contactos
    fields = '__all__'
    template_name = 'contactos_form.html'
    success_url = reverse_lazy('contactos_list')

class ContactosUpdateView(UpdateView):
    model = Contactos
    fields = '__all__'
    template_name = 'contactos_form.html'
    success_url = reverse_lazy('contactos_list')

class ContactosDeleteView(DeleteView):
    model = Contactos
    template_name = 'contactos_confirm_delete.html'
    success_url = reverse_lazy('contactos_list')

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

class PedidosUpdateView(UpdateView):
    model = Pedidos
    fields = '__all__'
    template_name = 'pedidos_form.html'
    success_url = reverse_lazy('pedidos_list')

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

    

def PedidosProductosUpdateView(request, id_pedido, id_producto):

    obj = get_object_or_404(PedidosProductos, id_pedido=id_pedido, id_producto=id_producto)

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

class UsuariosCreateView(CreateView):
    model = Usuarios
    fields = '__all__'
    template_name = 'usuarios_form.html'
    success_url = reverse_lazy('usuarios_list')

class UsuariosUpdateView(UpdateView):
    model = Usuarios
    fields = '__all__'
    template_name = 'usuarios_form.html'
    success_url = reverse_lazy('usuarios_list')

class UsuariosDeleteView(DeleteView):
    model = Usuarios
    template_name = 'usuarios_confirm_delete.html'
    success_url = reverse_lazy('usuarios_list')

#Roles