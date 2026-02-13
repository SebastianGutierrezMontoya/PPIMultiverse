from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Usuarios, Sexos, EstadoPedidos, Config_Contacto, Productos_Auditoria, Consultas_Dinamicas
from .forms import PedidosForm, UsuariosForm, RolesForm, CategoriaForm, ProductosForm, PedidoProductoUpdateForm, ConsultasDinamicasForm, EstadoPedidosForm
from django.db.models import F, ExpressionWrapper, DecimalField, Sum
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction, connection
from django.contrib import messages
import re
from django.forms import modelform_factory
import pyodbc


# Función para extraer mensajes de error de SQL Server
def _extract_db_message(exc):
    """Extrae el mensaje amigable de una excepción SQL Server."""
    text = str(exc) or ''
    # print("DEBUG: Mensaje de error completo:", text)
    
    # Buscar patrón: [SQL Server]mensaje(código)(SQLExecDirectW)
    m = re.search(r'\[SQL Server\](.+?)\s*\(\d+\)\s*\(SQLExecDirectW\)', text)
    if m:
        return m.group(1).strip()
    
    # Si no encuentra el patrón anterior, busca [SQL Server]mensaje(código)
    m = re.search(r'\[SQL Server\](.+?)\s*\(\d+\)', text)
    if m:
        return m.group(1).strip()
    
    # Fallback: primera línea no vacía
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('['):
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


def desactivar_trigger():
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_set_session_context @key=N'disable_auditoria_producto', @value=1"
        )

def activar_trigger():
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC sp_set_session_context @key=N'disable_auditoria_producto', @value=NULL"
        )


#PedidosProductos
def PedidosProductosCreateView(productos_seleccionados, id_pedido):

    with transaction.atomic():

        for item in productos_seleccionados:
            prod_id, cantidad = item.split(',')
            producto = get_object_or_404(Productos, pk=prod_id)
            pedido = get_object_or_404(Pedidos, pk=id_pedido)

            pped_precio_unitario = producto.prod_precio_venta
            pped_descuento = producto.prod_descuento
            pped_cantidad = int(cantidad)
            pped_total = (pped_precio_unitario - (pped_precio_unitario * (pped_descuento/100))) * pped_cantidad

            pped_estado = get_object_or_404(EstadoPedidos, pk=1)  

            PedidosProductos.objects.create(
                ped=pedido,
                prod=producto,
                pped_cantidad=pped_cantidad,
                pped_precio_unitario=pped_precio_unitario,
                pped_total=pped_total,
                pped_descuento=pped_descuento,
                pped_estado=pped_estado
            )

        # VALIDACIÓN FINAL DEL PEDIDO 
        cursor = connection.cursor()
        desactivar_trigger()
        try:
            cursor.execute("EXEC sp_cerrar_pedido @id_pedido=?", [id_pedido])
        except Exception as e:
            # Esto fuerza rollback de toda la transacción
            raise DatabaseError(e)
        finally:
            activar_trigger()
        


def PedidoProductoUpdateFormView(request, ped_id, prod_id):
    objeto = get_object_or_404(PedidosProductos, ped_id=ped_id, prod_id=prod_id)

    if request.method == 'POST':
        form = PedidoProductoUpdateForm(request.POST, instance=objeto)
        if form.is_valid():
            form.save()
            return redirect('pedidos_update', pk=ped_id)  # ajusta a tu URL final
    else:
        form = PedidoProductoUpdateForm(instance=objeto)

    return render(request, 'pedidos_productos_form.html', {
        'form': form,
        'objeto': objeto
    })

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
        Prod = Productos.objects.values('prod_id', 'prod_nombre', 'prod_precio_venta', 'prod_stock', 'prod_descuento')
        Json['Productos'] = Prod
        form = PedidosForm()
    # success_url = reverse_lazy('pedidos_list')
    
    Json['form'] = form
    
    return render(request, 'pedidos_form.html', Json )

def PedidosUpdateView(request, pk):
    pedido = get_object_or_404(Pedidos, pk=pk)
    productos_relacionados = PedidosProductos.objects.filter(ped=pedido)

    Estado = None
    
    cursor = connection.cursor()
    try:
        cursor.execute("EXEC sp_obtener_estado_pedido @id_pedido=?", [pedido.ped_id])
        resultado = cursor.fetchone()
        Estado = resultado[0] if resultado else None

    except Exception as e:
        # Esto fuerza rollback de toda la transacción
        raise DatabaseError(e)
        


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
        'Estado': Estado,
    })

def PedidosDeleteView(request, pk):
    pedido = get_object_or_404(Pedidos, pk=pk)
    pedidos_productos_relacionados = PedidosProductos.objects.filter(ped=pedido)
    
    try:
        pedidos_productos_relacionados.delete()
        pedido.delete()
    except DatabaseError as e:
        messages.error(request, _extract_db_message(e))
        return redirect('pedidos_list')
    return redirect('pedidos_list')


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




#productos auditoria
def ProductosAuditoriaView(request):
    # productos_auditoria = Productos_Auditoria.objects.all()
    # productos_auditoria_raw = Productos_Auditoria.objects.raw(
    # "SELECT rownum AS id, creation_date, au_type, auditoria FROM productos_auditoria"
    # )

    productos_auditoria_raw = Productos_Auditoria.objects.raw("""
    SELECT 
        ROW_NUMBER() OVER (ORDER BY creation_date DESC) AS id,
        creation_date,
        au_type,
        auditoria
    FROM productos_auditoria
    """)


# Convertimos los objetos y reemplazamos au_type por texto
    productos_auditoria = []
    for p in productos_auditoria_raw:
       if p.au_type == 1:
           p.au_type_text = "Creación"
       elif p.au_type == 2:
           p.au_type_text = "Modificación"
       elif p.au_type == 3:
           p.au_type_text = "Eliminación"
       else:
           p.au_type_text = "Desconocido"

       productos_auditoria.append(p)

    return render(request, 'productos_auditoria.html', {'productos_auditoria': productos_auditoria})

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
        
    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')
    Json['Tipo_Contacto'] = Tipo_Contacto
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

    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')
    
    return render(request, 'usuarios_form.html', {
        'form': form,
        'object': usuario,
        'contactos_relacionados': contactos_relacionados,
        'Tipo_Contacto': Tipo_Contacto,
    })

def UsuariosDeleteView(request, pk):
    usuario = get_object_or_404(Usuarios, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # eliminar contactos ligados al usuario
                Contactos.objects.filter(id_usuario=usuario).delete()
                usuario.delete()
        except DatabaseError as e:
            messages.error(request, _extract_db_message(e))
            return redirect('usuarios_detail', pk=pk)
        return redirect('usuarios_list')
    # GET: mostrar confirmación
    return render(request, 'usuarios_confirm_delete.html', {'object': usuario})

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
            tipo_contacto = get_object_or_404(Config_Contacto, pk=tipo_contacto)
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
            # contacto.tipo_contacto = contacto_data.get('tipo_contacto', contacto.tipo_contacto)
            contacto.tipo_contacto = get_object_or_404(Config_Contacto, pk=contacto.tipo_contacto.pk)
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


# Sexos
class SexosListView(ListView):
    model = Sexos
    template_name = 'sexos_list.html'

class SexosDetailView(DetailView):
    model = Sexos
    template_name = 'sexos_detail.html'

class SexosCreateView(CreateView):
    model = Sexos
    fields = '__all__'
    template_name = 'sexos_form.html'
    success_url = reverse_lazy('sexos_list')

class SexosUpdateView(UpdateView):
    model = Sexos
    fields = '__all__'
    template_name = 'sexos_form.html'
    success_url = reverse_lazy('sexos_list')

class SexosDeleteView(DeleteView):
    model = Sexos
    template_name = 'sexos_confirm_delete.html'
    success_url = reverse_lazy('sexos_list')


#EstadoPedidos
class EstadoPedidosListView(ListView):
    model = EstadoPedidos
    template_name = 'estado_pedidos_list.html'

class EstadoPedidosDetailView(DetailView):
    model = EstadoPedidos
    template_name = 'estado_pedidos_detail.html'

class EstadoPedidosCreateView(CreateView):
    model = EstadoPedidos
    form_class = EstadoPedidosForm
    template_name = 'estado_pedidos_form.html'
    success_url = reverse_lazy('estado_pedidos_list')

class EstadoPedidosUpdateView(UpdateView):
    model = EstadoPedidos
    fields = '__all__'
    template_name = 'estado_pedidos_form.html'
    success_url = reverse_lazy('estado_pedidos_list')

class EstadoPedidosDeleteView(DeleteView):
    model = EstadoPedidos
    template_name = 'estado_pedidos_confirm_delete.html'
    success_url = reverse_lazy('estado_pedidos_list')


# Config_Contacto CRUD
class ConfigContactoListView(ListView):
    model = Config_Contacto
    template_name = 'config_contacto_list.html'

class ConfigContactoDetailView(DetailView):
    model = Config_Contacto
    template_name = 'config_contacto_detail.html'

# Reemplaza la clase ConfigContactoCreateView por función que prellena id_regla
def ConfigContactoCreateView(request):
    FormClass = modelform_factory(Config_Contacto, fields='__all__')
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                return redirect('config_contacto_list')
    else:
        initial = {'id_regla': Config_Contacto.next_id()}
        form = FormClass(initial=initial)
    return render(request, 'config_contacto_form.html', {'form': form})

class ConfigContactoUpdateView(UpdateView):
    model = Config_Contacto
    fields = '__all__'
    template_name = 'config_contacto_form.html'
    success_url = reverse_lazy('config_contacto_list')

class ConfigContactoDeleteView(DeleteView):
    model = Config_Contacto
    template_name = 'config_contacto_confirm_delete.html'
    success_url = reverse_lazy('config_contacto_list')


#Consultas_Dinamicas

class ConsultasDinamicasListView(ListView):
    model = Consultas_Dinamicas
    template_name = 'ConsultasDinamicas/consultas_dinamicas_list.html'

class ConsultasDinamicasDetailView(DetailView):
    model = Consultas_Dinamicas
    template_name = 'ConsultasDinamicas/consultas_dinamicas_detail.html'

def ConsultasDinamicasCreateView(request):
    if request.method == 'POST':
        # form = modelform_factory(ConsultasDinamicasForm, fields='__all__')(request.POST)
        form = ConsultasDinamicasForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('consultas_dinamicas_list')
    else:
        # form = modelform_factory(ConsultasDinamicasForm, fields='__all__')()
        form = ConsultasDinamicasForm(request.POST)
    return render(request, 'ConsultasDinamicas/consultas_dinamicas_form.html', {'form': form})

# def ConsultasDinamicasUpdateView(request, pk):
#     consulta = get_object_or_404(Consultas_Dinamicas, pk=pk)
#     if request.method == 'POST':
#         # form = modelform_factory(ConsultasDinamicasForm, fields='__all__')(request.POST, instance=consulta)
#         form = ConsultasDinamicasForm(request.POST, instance=consulta)
#         if form.is_valid():
#             form.save()
#             return redirect('consultas_dinamicas_list')
#     else:
#         # form = modelform_factory(ConsultasDinamicasForm, fields='__all__')(instance=consulta)
#         form = ConsultasDinamicasForm(request.POST, instance=consulta)
#     return render(request, 'ConsultasDinamicas/consultas_dinamicas_form.html', {'form': form, 'object': consulta})

class ConsultasDinamicasUpdateView(UpdateView):
    model = Consultas_Dinamicas
    form_class = ConsultasDinamicasForm
    template_name = 'ConsultasDinamicas/consultas_dinamicas_form.html'
    success_url = reverse_lazy('consultas_dinamicas_list')

class ConsultasDinamicasDeleteView(DeleteView):
    model = Consultas_Dinamicas
    template_name = 'ConsultasDinamicas/consultas_dinamicas_confirm_delete.html'
    success_url = reverse_lazy('consultas_dinamicas_list')


# def ejecutar_reporte(id_reporte):

#     with connection.cursor() as cursor:

#         # Cursor que recibirá el refcursor
#         out_cursor = cursor.connection.cursor()

#         # Llamar la función (retorna un refcursor)
#         ref = cursor.callfunc(
#             "pkg_reportes.fn_ejecutar_reporte",
#             oracledb.CURSOR,
#             [id_reporte]
#         )

#         columnas = [col[0] for col in ref.description]
#         resultados = []

#         for fila in ref:
#             resultados.append(dict(zip(columnas, fila)))

#         return resultados

def ejecutar_reporte(id_reporte):
    with connection.cursor() as cursor:
        cursor.execute("EXEC sp_ejecutar_reporte @id_consulta=%s", [id_reporte])

        columnas = [col[0] for col in cursor.description]
        resultados = []

        for fila in cursor.fetchall():
            resultados.append(dict(zip(columnas, fila)))

        return resultados
    
def reporte_view(request, id):
    data = ejecutar_reporte(id)
    return render(request, "ConsultasDinamicas/consultas_reporte.html", {"resultado": data})