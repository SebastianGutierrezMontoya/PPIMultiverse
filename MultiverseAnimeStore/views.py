from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios
from .forms import PedidosForm, UsuariosForm, RolesForm, CategoriaForm, ProductosForm
from django.db.models import F, ExpressionWrapper, DecimalField, Sum
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction
from django.contrib import messages
import re

# Función para extraer mensajes de error de Oracle
def _extract_db_message(exc):
    """Extrae el mensaje amigable de una excepción Oracle (p. ej. RAISE_APPLICATION_ERROR)."""
    text = str(exc) or ''
    # Busca 'ORA-XXXXX: mensaje...' y captura el 'mensaje' hasta un salto de línea o la siguiente 'ORA-'
    m = re.search(r'ORA-\d{5}:\s*(.+?)(?:\n|ORA-|$)', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Si no hay ORA-... devuelve la primera línea no vacía
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return text.strip() or 'Error de base de datos.'

#Categorias
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'

class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categoria_detail.html'

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')

def CategoriaCreateView(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm()
    return render(request, 'categoria_form.html', {'form': form})

def CategoriaUpdateView(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'categoria_form.html', {'form': form, 'object': categoria})

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
            try:
                with transaction.atomic():
                    pedido = form.save()
                    # crear relaciones dentro de la misma transacción
                    PedidosProductosCreateView(productos_seleccionados, id_pedido)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
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
            try:
                with transaction.atomic():
                    pedido = form.save()
                    # si en edición recibes productos nuevos, manejarlos aquí (opcional)
                    productos_seleccionados = request.POST.getlist('productos_seleccionados')
                    if productos_seleccionados:
                        PedidosProductosCreateView(productos_seleccionados, pedido.ped_id)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
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


#Productos

class ProductosListView(ListView):
    model = Productos
    template_name = 'productos_list.html'

class ProductosDetailView(DetailView):
    model = Productos
    template_name = 'productos_detail.html'


def ProductosCreateView(request):
    if request.method == 'POST':
        form = ProductosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                return redirect('productos_list')
    else:
        form = ProductosForm()
    return render(request, 'productos_form.html', {'form': form})

def ProductosUpdateView(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    if request.method == 'POST':
        form = ProductosForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                return redirect('productos_list')
    else:
        form = ProductosForm(instance=producto)
    return render(request, 'productos_form.html', {'form': form, 'object': producto})

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
        form = UsuariosForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save()
                    # crear contactos dentro de la misma transacción
                    ContactosCreateView(contactos_relacionados, usuario.id_usuario)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                return redirect('usuarios_list')
    else:
        form = UsuariosForm()

    Json['form'] = form
    return render(request, 'usuarios_form.html', Json )

def UsuariosUpdateView(request, pk):
    usuario = get_object_or_404(Usuarios, pk=pk)
    contactos_relacionados = Contactos.objects.filter(id_usuario=usuario)
    
    if request.method == 'POST':
        form = UsuariosForm(request.POST, instance=usuario)
        contactos_relacionados_nuevo = request.POST.getlist('contactos_relacionados')
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    # procesar contactos sólo si el guardado de usuario tuvo éxito
                    contactos_data = request.POST.getlist('contactos_relacionados_editados')
                    contactos_actualizar = []
                    for item in contactos_data:
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
                            contactos_actualizar.append({
                                'tipo_contacto': tipo_contacto,
                                'dato_contacto': dato_contacto,
                            })
                    # actualizar y crear dentro de la transacción
                    if contactos_actualizar:
                        ContactosUpdateView(contactos_actualizar)
                    if contactos_relacionados_nuevo:
                        ContactosCreateView(contactos_relacionados_nuevo, usuario.id_usuario)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
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
    errors = []
    for item in contactos_relacionados:
        try:
            id_con = Contactos.objects.count() + 1
            tipo_contacto, dato_contacto = item.split(',')
            usuario = get_object_or_404(Usuarios, pk=id_usuario)

            Contactos.objects.create(
                id_contacto=id_con,
                tipo_contacto=tipo_contacto,
                dato_contacto=dato_contacto,
                id_usuario=usuario
            )
        except DatabaseError as e:
            errors.append(_extract_db_message(e))
        except Exception as e:
            errors.append(str(e))
    if errors:
        # lanzar un DatabaseError con el mensaje combinado para que lo capture la vista que llamó
        raise DatabaseError('; '.join(errors))

def ContactosUpdateView(contactos_actualizar):
    errors = []
    for contacto_data in contactos_actualizar:
        try:
            contacto = get_object_or_404(Contactos, pk=contacto_data['id_contacto'])
            contacto.tipo_contacto = contacto_data.get('tipo_contacto', contacto.tipo_contacto)
            contacto.dato_contacto = contacto_data.get('dato_contacto', contacto.dato_contacto)
            contacto.save()
        except DatabaseError as e:
            errors.append(_extract_db_message(e))
        except Exception as e:
            errors.append(str(e))
    if errors:
        raise DatabaseError('; '.join(errors))

def ContactosDeleteView(request, pk):
    contacto = get_object_or_404(Contactos, pk=pk)
    user_pk = contacto.id_usuario.pk if contacto.id_usuario else None
    try:
        contacto.delete()
    except DatabaseError as e:
        # mostrar sólo el mensaje del trigger y redirigir de vuelta al usuario (si aplica)
        messages.error(request, _extract_db_message(e))
        if user_pk:
            return redirect('usuarios_update', pk=user_pk)
        return redirect('usuarios_list')
    # si todo ok, volver a la edición del usuario cuando aplique
    if user_pk:
        return redirect('usuarios_update', pk=user_pk)
    return HttpResponseRedirect(reverse_lazy('usuarios_list'))

#Roles

class RolesListView(ListView):
    model = Roles
    template_name = 'roles_list.html'

class RolesDetailView(DetailView):
    model = Roles
    template_name = 'roles_detail.html'


def RolesCreateView(request):
    if request.method == 'POST':
        form = RolesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolesForm()
    return render(request, 'roles_form.html', {'form': form})

def RolesUpdateView(request, pk):
    role = get_object_or_404(Roles, pk=pk)
    if request.method == 'POST':
        form = RolesForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolesForm(instance=role)
    return render(request, 'roles_form.html', {'form': form, 'object': role})

class RolesDeleteView(DeleteView):
    model = Roles
    template_name = 'roles_confirm_delete.html'
    success_url = reverse_lazy('roles_list')

