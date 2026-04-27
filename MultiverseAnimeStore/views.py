from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Perfiles, Perfilpermisos, Modulos, Usuarios, Sexos, EstadoPedidos, Config_Contacto, Productos_Auditoria, Consultas_Dinamicas
from .forms import PedidosForm, UsuariosForm, RolesForm, PerfilesForm, CategoriaForm, ProductosForm, PedidoProductoUpdateForm, ConsultasDinamicasForm, EstadoPedidosForm, SexosForm
from django.db.models import F, ExpressionWrapper, DecimalField, Sum, Q, Max
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction, connection
from django.contrib import messages
import re
from functools import wraps
from django.forms import modelform_factory
import psycopg2
import json
import secrets
from datetime import date
from decimal import Decimal
from django.core.paginator import Paginator
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# @method_decorator(Permisos_Admin, name='dispatch')

def Permisos_Admin(modulo, tipo, redirect_url='admin_home'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):


            if not getattr(request.user, 'is_authenticated', False):
                return redirect('login')
            
            

            usuario = Usuarios.objects.filter(id_usuario=request.user.id_usuario).first()
            if not usuario or not usuario.usuario_id_perfil:
                messages.error(request, 'No tienes perfil asignado. Contacta al administrador.')
                return redirect(redirect_url)

            perfil = usuario.usuario_id_perfil
            modulo_obj = Modulos.objects.filter(nombre_mod__iexact=modulo).first()
            if not modulo_obj:
                messages.error(request, f'Módulo "{modulo}" no configurado.')
                return redirect(redirect_url)

            permiso_obj = Perfilpermisos.objects.filter(perfil_id=perfil, mod_id=modulo_obj).first()
            if not permiso_obj:
                messages.error(request, 'No tienes permiso para acceder a este módulo.')
                return redirect(redirect_url)

            permiso_value = getattr(permiso_obj, f'can_{tipo}', None)
            if permiso_value != 'Y':
                messages.error(request, f'No tienes permiso para {tipo} en este módulo.')
                return redirect(redirect_url)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def Login_requerido():
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):



            if not getattr(request.user, 'is_authenticated', False):
                return redirect('login')
            


            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

# Función para extraer mensajes de error de BD (compatible PostgreSQL y otros)
def _extract_db_message(exc):
    """Extrae el mensaje amigable de una excepción de base de datos."""
    text = str(exc) or ''
    
    # PostgreSQL: buscar después de "DETAIL:" o "HINT:" o "ERROR:"
    for prefix in ['DETAIL:  ', 'HINT:  ', 'ERROR:  ', 'CONTEXT:  ']:
        if prefix in text:
            idx = text.find(prefix) + len(prefix)
            end = text.find('\n', idx)
            return text[idx:end].strip() if end > 0 else text[idx:].strip()
    
    # Fallback: primera línea no vacía que no parezca traceback
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('[') and not line.startswith('Traceback'):
            if len(line) > 10 and line[0].isupper():  # parece un mensaje real
                return line
    
    # Último recurso
    return text.strip() or 'Error de base de datos.'

def admin_home(request):
    return render(request, 'admin_home.html')


# contraseña hashing 
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Login
def login_view(request):
    # Si ya está autenticado, redirigir al catálogo (no mostrar login)
    if request.user.is_authenticated:
        return redirect('catalogo')

    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')

        try:
            user = Usuarios.objects.get(id_usuario=usuario, password_hash=hash_password(contraseña))
            request.session['user_id'] = user.id_usuario
            # Los administradores van al panel; los clientes al catálogo
            destino = request.POST.get('next', 'catalogo')
            return redirect(destino)
        except Usuarios.DoesNotExist:
            messages.error(request, 'Credenciales inválidas. Inténtalo de nuevo.')

    return render(request, 'Sesion/login.html', {'sidebar': 0})

# registro 
def register_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')
        nombre = request.POST.get('nombre')
        primer_apellido = request.POST.get('primer_apellido')
        segundo_apellido = request.POST.get('segundo_apellido')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        sexo_id = request.POST.get('sexo')

        contactos_relacionados = request.POST.getlist('contactos_relacionados')


        if Usuarios.objects.filter(id_usuario=usuario).exists():
            messages.error(request, 'El nombre de usuario ya existe. Elige otro.')
        else:

            sexo = get_object_or_404(Sexos, pk=sexo_id)

            # Asignar perfil Cliente por defecto (id_perfil=2)
            perfil_cliente = Perfiles.objects.filter(id_perfil=2).first()

            Usuarios.objects.create(
                id_usuario=usuario,
                password_hash=hash_password(contraseña),
                nombre=nombre,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
                fecha_nacimiento=fecha_nacimiento,
                usuario_id_sexo=sexo,
                usuario_id_perfil=perfil_cliente,
                activo=1
            )

            ContactosCreateView(contactos_relacionados, usuario)
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        
    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')
    Sexo = Sexos.objects.values('id_sexo', 'nombre_sexo')

    return render(request, 'Sesion/register.html', {'sidebar': 0, 'Tipo_Contacto': Tipo_Contacto, 'Sexos': Sexo})

# logout
def logout_view(request):
    request.session.flush()
    messages.success(request, 'Has cerrado sesión. ¡Vuelve pronto!')
    return redirect('home')

#Categorias

@method_decorator(Permisos_Admin('Categoria', 'read'), name='dispatch')
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'Categoria/categoria_list.html'

@method_decorator(Permisos_Admin('Categoria', 'read'), name='dispatch')
class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'Categoria/categoria_detail.html'

@method_decorator(Permisos_Admin('Categoria', 'delete'), name='dispatch')
class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'Categoria/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')

@Permisos_Admin('Categoria', 'create')
def CategoriaCreateView(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm()
    return render(request, 'Categoria/categoria_form.html', {'form': form})

@Permisos_Admin('Categoria', 'update')
def CategoriaUpdateView(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'Categoria/categoria_form.html', {'form': form, 'object': categoria})


def desactivar_trigger():
    # with connection.cursor() as cursor:
    #     cursor.execute("SET LOCAL disable_auditoria_producto = true")
    print("DEBUG: Trigger de auditoría desactivado para esta sesión.")

def activar_trigger():
    # with connection.cursor() as cursor:
    #     cursor.execute("SET LOCAL disable_auditoria_producto = false")
    print("DEBUG: Trigger de auditoría activado para esta sesión.")


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

        # VALIDACIÓN FINAL DEL PEDIDO (reemplazo de sp_cerrar_pedido de Oracle)
        # Calcular total actualizado del pedido basado en productos
        total_real = PedidosProductos.objects.filter(ped=pedido).aggregate(
            total=Sum('pped_total')
        )['total'] or 0
        Pedidos.objects.filter(pk=id_pedido).update(ped_total=total_real)
        


def PedidoProductoUpdateFormView(request, ped_id, prod_id):
    objeto = get_object_or_404(PedidosProductos, ped_id=ped_id, prod_id=prod_id)

    if request.method == 'POST':
        form = PedidoProductoUpdateForm(request.POST, instance=objeto)
        if form.is_valid():
            form.save()
            return redirect('pedidos_update', pk=ped_id)  # ajusta a tu URL final
    else:
        form = PedidoProductoUpdateForm(instance=objeto)

    return render(request, 'Pedidos/pedidos_productos_form.html', {
        'form': form,
        'objeto': objeto
    })

@Permisos_Admin('Pedidos', 'delete')
def PedidoProductoDeleteView(request, ped_id):
    

    for p in PedidosProductos.objects.filter(ped_id=ped_id):
        producto = get_object_or_404(Productos, pk=p.prod_id)
        producto.prod_stock = F('prod_stock') + p.pped_cantidad
        producto.save()
        p.delete()

    return redirect('pedidos_list')

#Pedidos

@method_decorator(Permisos_Admin('Pedidos', 'read'), name='dispatch')
class PedidosListView(ListView):
    model = Pedidos
    template_name = 'Pedidos/pedidos_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = Pedidos.objects.all().order_by('ped_id')
        pedido_id = self.request.GET.get('pedido_id')

        if pedido_id:
            try:
                pedido_id_int = int(pedido_id)
                queryset = queryset.filter(ped_id=pedido_id_int)
            except ValueError:
                queryset = queryset.none()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pedido_id'] = self.request.GET.get('pedido_id', '')
        return context

@method_decorator(Permisos_Admin('Pedidos', 'read'), name='dispatch')
class PedidosDetailView(DetailView):
    model = Pedidos
    template_name = 'Pedidos/pedidos_detail.html'

@Permisos_Admin('Pedidos', 'create')
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
    
    return render(request, 'Pedidos/pedidos_form.html', Json )

@Permisos_Admin('Pedidos', 'update')
def PedidosUpdateView(request, pk):
    pedido = get_object_or_404(Pedidos, pk=pk)
    productos_relacionados = PedidosProductos.objects.filter(ped=pedido)

    # Obtener estado del pedido (reemplazo de fn_estado_pedido de Oracle)
    Estado = pedido.ped_estado
        


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

    return render(request, 'Pedidos/pedidos_form.html', {
        'form': form,
        'object': pedido,
        'productos_relacionados': productos_relacionados,
        'Estado': Estado,
    })

@Permisos_Admin('Pedidos', 'delete')
def PedidosDeleteView(request, pk):
    pedido = get_object_or_404(Pedidos, pk=pk)
    # pedidos_productos_relacionados = PedidosProductos.objects.filter(ped=pedido)
    
    try:
        # pedidos_productos_relacionados.delete()
        PedidoProductoDeleteView(request, pedido.ped_id)
        pedido.delete()
    except DatabaseError as e:
        messages.error(request, _extract_db_message(e))
        return redirect('pedidos_list')
    return redirect('pedidos_list')


#Productos
@method_decorator(Permisos_Admin('Productos', 'read'), name='dispatch')
class ProductosListView(ListView):
    model = Productos
    template_name = 'Productos/productos_list.html'


    paginate_by = 10

    def get_queryset(self):
        queryset = Productos.objects.all().order_by('prod_id')
        producto_id = self.request.GET.get('producto_id')

        if producto_id:
            # try:
            #     producto_id_int = int(producto_id)
            #     queryset = queryset.filter(prod_id=producto_id_int)
            # except ValueError:
            #     queryset = queryset.none()
            queryset = queryset.filter(prod_nombre__icontains=producto_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['producto_id'] = self.request.GET.get('producto_id', '')
        return context

@method_decorator(Permisos_Admin('Productos', 'read'), name='dispatch')
class ProductosDetailView(DetailView):
    model = Productos
    template_name = 'productos_detail.html'

@Permisos_Admin('Productos', 'create')
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
    return render(request, 'Productos/productos_form.html', {'form': form})

@Permisos_Admin('Productos', 'update')
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
    return render(request, 'Productos/productos_form.html', {'form': form, 'object': producto})

@method_decorator(Permisos_Admin('Productos', 'delete'), name='dispatch')
class ProductosDeleteView(DeleteView):
    model = Productos
    template_name = 'productos_confirm_delete.html'
    success_url = reverse_lazy('productos_list')




#productos auditoria
@Permisos_Admin('Productos', 'read')
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

       # Parsear el JSON de auditoria
       try:
           parsed = json.loads(p.auditoria)
           p.auditoria_parsed = parsed

           

           producto_info = parsed.get('old') if isinstance(parsed, dict) else None
           
           
        #    p.product_name = None
           if isinstance(producto_info, dict):
               
               p.product_name = producto_info.get('prod_nombre') or producto_info.get('nombre')
           elif isinstance(parsed, dict):
               p.product_name = parsed.get('prod_nombre') or parsed.get('nombre')

        #    print("DEBUG: Nombre del producto extraído:", p.product_name)
           
           if p.au_type == 2:  # Modificación
               old = parsed.get('old', {})
               new = parsed.get('new', {})
               differences = []
               for key in set(old.keys()) | set(new.keys()):
                   if old.get(key) != new.get(key):
                       differences.append({
                           'field': key,
                           'old': old.get(key, 'N/A'),
                           'new': new.get(key, 'N/A')
                       })
               p.differences = differences
           else:
               p.differences = []
       except json.JSONDecodeError:
           p.auditoria_parsed = None
           p.product_name = None
           p.differences = []

       productos_auditoria.append(p)

    return render(request, 'Productos/productos_auditoria.html', {'productos_auditoria': productos_auditoria})

#Usuarios
@method_decorator(Permisos_Admin('Usuarios', 'read'), name='dispatch')
class UsuariosListView(ListView):
    model = Usuarios
    template_name = 'Usuarios/usuarios_list.html'

    paginate_by = 10

    def get_queryset(self):
        queryset = Usuarios.objects.all().order_by('id_usuario')
        usuario_id = self.request.GET.get('usuario_id')
        match_id = self.request.GET.get('match_id')

        if usuario_id:
            # try:
            #     producto_id_int = int(producto_id)
            #     queryset = queryset.filter(prod_id=producto_id_int)
            # except ValueError:
            #     queryset = queryset.none()
            if match_id:
                queryset = queryset.filter(id_usuario__iexact=usuario_id)
            else:
                queryset = queryset.filter(Q(nombre__icontains=usuario_id) | Q(id_usuario__icontains=usuario_id))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuario_id'] = self.request.GET.get('usuario_id', '')
        context['match_id'] = self.request.GET.get('match_id', '')
        return context

@method_decorator(Permisos_Admin('Usuarios', 'read'), name='dispatch')
class UsuariosDetailView(DetailView):
    model = Usuarios
    template_name = 'Usuarios/usuarios_detail.html'

@Permisos_Admin('Usuarios', 'create')
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
    return render(request, 'Usuarios/usuarios_form.html', Json )

@Permisos_Admin('Usuarios', 'update')
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
    
    return render(request, 'Usuarios/usuarios_form.html', {
        'form': form,
        'object': usuario,
        'contactos_relacionados': contactos_relacionados,
        'Tipo_Contacto': Tipo_Contacto,
    })

@Permisos_Admin('Usuarios', 'delete')
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
    return render(request, 'Usuarios/usuarios_confirm_delete.html', {'object': usuario})

#Contactos
@method_decorator(Permisos_Admin('Contactos', 'read'), name='dispatch')
class ContactosListView(ListView):
    model = Contactos
    template_name = 'Contactos/contactos_list.html'

@method_decorator(Permisos_Admin('Contactos', 'read'), name='dispatch')
class ContactosDetailView(DetailView):
    model = Contactos
    template_name = 'Contactos/contactos_detail.html'

# @Permisos_Admin('Contactos', 'create')
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

@Permisos_Admin('Contactos', 'update')
def ContactosUpdateView(contactos_actualizar):
    errors = []
    for contacto_data in contactos_actualizar:
        try:
            id_contacto = contacto_data['id_contacto']
            tipo_contacto_id = contacto_data['tipo_contacto']
            dato_contacto = contacto_data['dato_contacto']
            
            print(f"DEBUG ContactosUpdateView: id={id_contacto}, tipo_id={tipo_contacto_id}, dato={dato_contacto}")
            
            # Verificar que el contacto existe
            contacto = get_object_or_404(Contactos, pk=id_contacto)
            print(f"DEBUG: Contacto encontrado: {contacto.id_contacto}")
            
            # Intentar deshabilitar auditorías/triggers a nivel de sesión
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL disable_auditoria_contactos = true")
                    cursor.execute("SET LOCAL disable_auditoria = true")

                    # Usar queryset.update() para forzar UPDATE sin insertar
                    resultado = Contactos.objects.filter(pk=id_contacto).update(
                        tipo_contacto_id=tipo_contacto_id,
                        dato_contacto=dato_contacto
                    )
            finally:
                # Restaurar el contexto de sesión
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL disable_auditoria_contactos = false")
                    cursor.execute("SET LOCAL disable_auditoria = false")

            print(f"DEBUG: Registros actualizados: {resultado}")
            
        except DatabaseError as e:
            errors.append(_extract_db_message(e))
        except Exception as e:
            errors.append(str(e))
    if errors:
        raise DatabaseError('; '.join(errors))

@Permisos_Admin('Contactos', 'delete')
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
@method_decorator(Permisos_Admin('Roles', 'read'), name='dispatch')
class RolesListView(ListView):
    model = Roles
    template_name = 'Roles/roles_list.html'

@method_decorator(Permisos_Admin('Roles', 'read'), name='dispatch')
class RolesDetailView(DetailView):
    model = Roles
    template_name = 'roles_detail.html'

@Permisos_Admin('Roles', 'create')
def RolesCreateView(request):
    if request.method == 'POST':
        form = RolesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolesForm()
    return render(request, 'Roles/roles_form.html', {'form': form})

@Permisos_Admin('Roles', 'update')
def RolesUpdateView(request, pk):
    role = get_object_or_404(Roles, pk=pk)
    if request.method == 'POST':
        form = RolesForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolesForm(instance=role)
    return render(request, 'Roles/roles_form.html', {'form': form, 'object': role})

@method_decorator(Permisos_Admin('Roles', 'delete'), name='dispatch')
class RolesDeleteView(DeleteView):
    model = Roles
    template_name = 'roles_confirm_delete.html'
    success_url = reverse_lazy('roles_list')


#perfiles 

@method_decorator(Permisos_Admin('Perfiles', 'read'), name='dispatch')
class PerfilesListView(ListView):
    model = Perfiles
    template_name = 'Perfiles/perfiles_list.html'

@method_decorator(Permisos_Admin('Perfiles', 'read'), name='dispatch')
class PerfilesDetailView(DetailView):
    model = Perfiles
    template_name = 'Perfiles/perfiles_detail.html'

@Permisos_Admin('Perfiles', 'create')
def PerfilesCreateView(request):
    if request.method == 'POST':
        form = PerfilesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('perfiles_list')
    else:
        form = PerfilesForm()
    return render(request, 'Perfiles/perfiles_form.html', {'form': form})

@Permisos_Admin('Perfiles', 'update')
def PerfilesUpdateView(request, pk):
    perfil = get_object_or_404(Perfiles, pk=pk)
    if request.method == 'POST':
        form = PerfilesForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('perfiles_list')
    else:
        form = PerfilesForm(instance=perfil)
    return render(request, 'Perfiles/perfiles_form.html', {'form': form, 'object': perfil})

@method_decorator(Permisos_Admin('Perfiles', 'delete'), name='dispatch')
class PerfilesDeleteView(DeleteView):
    model = Perfiles
    template_name = 'perfiles_confirm_delete.html'
    success_url = reverse_lazy('perfiles_list')


@Permisos_Admin('Perfiles', 'update')
def PerfilPermisosUpdateView(request, pk):
    perfil = get_object_or_404(Perfiles, pk=pk)
    modulos = Modulos.objects.all()

    if request.method == 'POST':
        # Para cada módulo, actualizar o crear el permiso
        for modulo in modulos:
            permiso_obj, created = Perfilpermisos.objects.get_or_create(
                perfil_id=perfil,
                mod_id=modulo
            )
            
            for tipo in ['read', 'create', 'update', 'delete']:
                field_name = f'perm_{modulo.nombre_mod}_{tipo}'
                setattr(permiso_obj, f'can_{tipo}', 'Y' if request.POST.get(field_name) == 'on' else 'N')
            
            permiso_obj.save()
        
        return redirect('perfiles_list')

    # Preparar datos para mostrar todos los módulos
    permisos_asignados = {}
    modulo_permisos = Perfilpermisos.objects.filter(perfil_id=perfil).select_related('mod_id')
    
    # Crear un diccionario de permisos existentes para búsqueda rápida
    permisos_dict = {mp.mod_id.id_mod: mp for mp in modulo_permisos}
    
    # Para cada módulo, obtener sus permisos (o valores por defecto)
    for modulo in modulos:
        if modulo.id_mod in permisos_dict:
            permiso = permisos_dict[modulo.id_mod]
            permisos_asignados[modulo.nombre_mod] = {
                'read': permiso.can_read == 'Y',
                'create': permiso.can_create == 'Y',
                'update': permiso.can_update == 'Y',
                'delete': permiso.can_delete == 'Y',
            }
        else:
            # Valores por defecto si no existe el permiso
            permisos_asignados[modulo.nombre_mod] = {
                'read': False,
                'create': False,
                'update': False,
                'delete': False,
            }

    return render(request, 'Perfiles/perfiles_permisos.html', {
        'perfil': perfil,
        'permisos_asignados': permisos_asignados,
    })



# Sexos
@method_decorator(Permisos_Admin('Sexos', 'read'), name='dispatch')
class SexosListView(ListView):
    model = Sexos
    template_name = 'Usuarios/sexos_list.html'

@method_decorator(Permisos_Admin('Sexos', 'read'), name='dispatch')
class SexosDetailView(DetailView):
    model = Sexos
    template_name = 'Usuarios/sexos_detail.html'

@method_decorator(Permisos_Admin('Sexos', 'create'), name='dispatch')
class SexosCreateView(CreateView):
    model = Sexos
    form_class = SexosForm
    template_name = 'Usuarios/sexos_form.html'
    success_url = reverse_lazy('sexos_list')

@method_decorator(Permisos_Admin('Sexos', 'update'), name='dispatch')
class SexosUpdateView(UpdateView):
    model = Sexos
    form_class = SexosForm
    template_name = 'Usuarios/sexos_form.html'
    success_url = reverse_lazy('sexos_list')

@method_decorator(Permisos_Admin('Sexos', 'delete'), name='dispatch')
class SexosDeleteView(DeleteView):
    model = Sexos
    template_name = 'Usuarios/sexos_confirm_delete.html'
    success_url = reverse_lazy('sexos_list')


#EstadoPedidos
@method_decorator(Permisos_Admin('EstadoPedidos', 'read'), name='dispatch')
class EstadoPedidosListView(ListView):
    model = EstadoPedidos
    template_name = 'Pedidos/estado_pedidos_list.html'

@method_decorator(Permisos_Admin('EstadoPedidos', 'read'), name='dispatch')
class EstadoPedidosDetailView(DetailView):
    model = EstadoPedidos
    template_name = 'estado_pedidos_detail.html'

@method_decorator(Permisos_Admin('EstadoPedidos', 'create'), name='dispatch')
class EstadoPedidosCreateView(CreateView):
    model = EstadoPedidos
    form_class = EstadoPedidosForm
    template_name = 'Pedidos/estado_pedidos_form.html'
    success_url = reverse_lazy('estado_pedidos_list')

@method_decorator(Permisos_Admin('EstadoPedidos', 'update'), name='dispatch')
class EstadoPedidosUpdateView(UpdateView):
    model = EstadoPedidos
    fields = '__all__'
    template_name = 'Pedidos/estado_pedidos_form.html'
    success_url = reverse_lazy('estado_pedidos_list')

@method_decorator(Permisos_Admin('EstadoPedidos', 'delete'), name='dispatch')
class EstadoPedidosDeleteView(DeleteView):
    model = EstadoPedidos
    template_name = 'Pedidos/estado_pedidos_confirm_delete.html'
    success_url = reverse_lazy('estado_pedidos_list')


# Config_Contacto CRUD
@method_decorator(Permisos_Admin('Config_Contactos', 'read'), name='dispatch')
class ConfigContactoListView(ListView):
    model = Config_Contacto
    template_name = 'Contactos/config_contacto_list.html'

@method_decorator(Permisos_Admin('Config_Contactos', 'read'), name='dispatch')
class ConfigContactoDetailView(DetailView):
    model = Config_Contacto
    template_name = 'Contactos/config_contacto_detail.html'

# Reemplaza la clase ConfigContactoCreateView por función que prellena id_regla
@Permisos_Admin('Config_Contactos', 'create')
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
    return render(request, 'Contactos/config_contacto_form.html', {'form': form})

@method_decorator(Permisos_Admin('Config_Contactos', 'update'), name='dispatch')
class ConfigContactoUpdateView(UpdateView):
    model = Config_Contacto
    fields = '__all__'
    template_name = 'Contactos/config_contacto_form.html'
    success_url = reverse_lazy('config_contacto_list')

@method_decorator(Permisos_Admin('Config_Contactos', 'delete'), name='dispatch')
class ConfigContactoDeleteView(DeleteView):
    model = Config_Contacto
    template_name = 'Contactos/config_contacto_confirm_delete.html'
    success_url = reverse_lazy('config_contacto_list')


#Consultas_Dinamicas
@method_decorator(Permisos_Admin('Consultas', 'read'), name='dispatch')
class ConsultasDinamicasListView(ListView):
    model = Consultas_Dinamicas
    template_name = 'ConsultasDinamicas/consultas_dinamicas_list.html'

@method_decorator(Permisos_Admin('Consultas', 'read'), name='dispatch')
class ConsultasDinamicasDetailView(DetailView):
    model = Consultas_Dinamicas
    template_name = 'ConsultasDinamicas/consultas_dinamicas_detail.html'

@Permisos_Admin('Consultas', 'create')
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

@method_decorator(Permisos_Admin('Consultas', 'update'), name='dispatch')
class ConsultasDinamicasUpdateView(UpdateView):
    model = Consultas_Dinamicas
    form_class = ConsultasDinamicasForm
    template_name = 'ConsultasDinamicas/consultas_dinamicas_form.html'
    success_url = reverse_lazy('consultas_dinamicas_list')

@method_decorator(Permisos_Admin('Consultas', 'delete'), name='dispatch')
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

@Permisos_Admin('Consultas', 'read')
def ejecutar_reporte(id_reporte):
    """
    Ejecuta una consulta dinámica guardada en Consultas_Dinamicas.
    Reemplazo de fn_ejecutar_reporte de Oracle.
    """
    try:
        consulta = Consultas_Dinamicas.objects.get(cons_id=id_reporte)
        sql = consulta.cons_sql

        # Validar que solo sea SELECT
        if not sql.strip().upper().startswith('SELECT'):
            raise Exception('Solo se permiten consultas SELECT')

        with connection.cursor() as cursor:
            cursor.execute(sql)
            columnas = [col[0] for col in cursor.description]
            resultados = []
            for fila in cursor.fetchall():
                resultados.append(dict(zip(columnas, fila)))
            return resultados
    except Consultas_Dinamicas.DoesNotExist:
        return []
    except Exception as e:
        print(f"Error ejecutando reporte {id_reporte}: {e}")
        return []

@Permisos_Admin('Consultas', 'read')
def reporte_view(request, id):
    data = ejecutar_reporte(id)
    return render(request, "ConsultasDinamicas/consultas_reporte.html", {"resultado": data})







def home_view(request):
    """Landing page: hero, categorías destacadas, últimos productos, redes sociales."""
    categorias = Categoria.objects.all()

    # Contar productos por categoría (para mostrar el badge)
    from django.db.models import Count
    categorias_conteo = Categoria.objects.annotate(
        productos_count=Count('productos')
    )

    # Top 4 categorías para hero cards (las que más productos tienen)
    hero_categories = categorias_conteo.order_by('-productos_count')[:4]

    # Últimos 8 productos agregados
    ultimos_productos = Productos.objects.select_related('cat').order_by('-prod_id')[:8]

    return render(request, 'Multiverse/landing.html', {
        'categorias': categorias_conteo,
        'hero_categories': hero_categories,
        'ultimos_productos': ultimos_productos,
    })


def checkout_view(request):
    print("DEBUG: checkout_view called with method:", request.method)
    if request.method == 'POST':
        cart_items_json = request.POST.get('cart_items_json', '[]')

        try:
            print("DEBUG: cart_items_json received:", cart_items_json)
            cart_items = json.loads(cart_items_json)
        except json.JSONDecodeError:
            print("DEBUG: Error al decodificar cart_items_json, usando lista vacía.")
            cart_items = []

        if not cart_items:
            print("DEBUG: No hay productos en el carrito.")
            messages.error(request, 'El carrito está vacío. No se creó ningún pedido.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # ── DETERMINAR USUARIO ──────────────────────────────────────
        # Si está autenticado, usamos su usuario.
        # Si NO está autenticado (invitado), creamos un usuario temporal
        # para cumplir con la FK de Pedidos, sin tocar el esquema de la BD.
        # ─────────────────────────────────────────────────────────────
        if request.user.is_authenticated:
            usuario = request.user
        else:
            nombre_invitado = request.POST.get('nombre_invitado', '').strip()
            telefono_invitado = request.POST.get('telefono_invitado', '').strip()
            direccion_envio = request.POST.get('ped_direccion_envio', '').strip()

            # Validar datos mínimos del invitado
            if not nombre_invitado or not telefono_invitado:
                messages.error(request, 'Debes ingresar tu nombre y teléfono para continuar.')
                return redirect(request.META.get('HTTP_REFERER', '/'))

            # Generar ID único para el usuario temporal
            from .forms import get_next_id_model_name
            next_id_num = get_next_id_model_name(Usuarios, 'id_usuario')
            new_id = f"USR-{next_id_num}"

            # Contraseña aleatoria — este usuario nunca va a iniciar sesión
            random_pass = secrets.token_hex(16)
            hashed = hash_password(random_pass)

            # Crear usuario temporal con activo=0 (no puede loguearse)
            sexo_default = Sexos.objects.get(pk=3)  # "Otro"
            perfil_cliente = Perfiles.objects.get(pk=2)  # "Cliente"

            # Separar nombre completo en nombre y primer_apellido
            partes_nombre = nombre_invitado.split(maxsplit=1)
            nombre = partes_nombre[0] if partes_nombre else nombre_invitado
            primer_apellido = partes_nombre[1] if len(partes_nombre) > 1 else "Invitado"

            usuario = Usuarios.objects.create(
                id_usuario=new_id,
                nombre=nombre,
                primer_apellido=primer_apellido,
                password_hash=hashed,
                activo=0,  # No puede iniciar sesión
                usuario_id_sexo=sexo_default,
                usuario_id_perfil=perfil_cliente,
            )

            # Guardar teléfono en la tabla Contactos
            next_contacto_id = get_next_id_model_name(Contactos, 'id_contacto')
            Contactos.objects.create(
                id_contacto=next_contacto_id,
                dato_contacto=telefono_invitado,
                id_usuario=usuario,
                # tipo_contacto se deja null (es nullable en la BD)
            )

            # Marcar ped_notas para identificar pedidos de invitados
            notas_pedido = request.POST.get('ped_notas', '').strip()
            if notas_pedido:
                notas_pedido = f"[INVITADO - {telefono_invitado}] {notas_pedido}"
            else:
                notas_pedido = f"[INVITADO - {telefono_invitado}]"
            request.POST = request.POST.copy()  # mutable copy
            request.POST['ped_notas'] = notas_pedido

        # ── FIN: usuario definido ─────────────────────────────────────

        productos_seleccionados = []
        total_calculado = Decimal('0.00')

        for item in cart_items:
            prod_id = item.get('id')
            qty = int(item.get('qty') or 0)
            if not prod_id or qty <= 0:
                continue

            producto = Productos.objects.filter(pk=prod_id).first()
            if not producto:
                continue

            productos_seleccionados.append(f"{prod_id},{qty}")
            precio_unitario = producto.prod_precio_venta or Decimal('0.00')
            descuento = producto.prod_descuento or Decimal('0.00')
            total_calculado += (precio_unitario - (precio_unitario * (descuento / Decimal('100')))) * qty

        if not productos_seleccionados:
            messages.error(request, 'No hay productos válidos en el carrito.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        next_ped_id = (Pedidos.objects.aggregate(max_id=Max('ped_id'))['max_id'] or 0) + 1

        try:
            with transaction.atomic():
                pedido = Pedidos.objects.create(
                    ped_id=next_ped_id,
                    usu=usuario,
                    ped_fecha_pedido=date.today(),
                    ped_total=total_calculado,
                    ped_direccion_envio=request.POST.get('ped_direccion_envio', ''),
                    ped_notas=request.POST.get('ped_notas', 'Pedido creado desde carrito público'),
                )
                print(f"DEBUG: Pedido creado con ID {pedido.ped_id} para usuario {usuario.id_usuario} con total {total_calculado}")
                PedidosProductosCreateView(productos_seleccionados, pedido.ped_id)

        except DatabaseError as e:
            print(f"Error al crear pedido: {e}")
            messages.error(request, _extract_db_message(e))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        messages.success(request, f'✅ Pedido #{pedido.ped_id} creado correctamente. Te contactaremos pronto.')
        return redirect('catalogo')

    return redirect('catalogo')


def catalogo_view(request):
    """Catálogo público con búsqueda por texto y filtro por categoría."""
    productos = Productos.objects.select_related('cat').all().order_by('prod_id')
    paginate_by = 40
    prod_nombre = request.GET.get('prod_nombre', '')
    cat_id = request.GET.get('cat', '')

    # ── Búsqueda por texto ──
    if prod_nombre:
        productos = productos.filter(
            Q(prod_nombre__icontains=prod_nombre) | Q(prod_descripcion__icontains=prod_nombre)
        )

    # ── Filtro por categoría ──
    if cat_id:
        productos = productos.filter(cat_id=cat_id)

    paginator = Paginator(productos, paginate_by)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Listado de categorías para mostrar como filtros en el catálogo
    categorias = Categoria.objects.all()

    return render(request, 'Multiverse/catalogo.html', {
        'productos': page_obj,
        'prod_nombre': prod_nombre,
        'cat_id': cat_id,
        'categorias': categorias,
    })


# ---------------------------------------------------------------------------
# PERFIL DEL CLIENTE - Mis Pedidos
# ---------------------------------------------------------------------------
@Login_requerido()
def mis_pedidos_view(request):
    """Muestra los pedidos del cliente logueado."""
    pedidos = Pedidos.objects.filter(usu=request.user).order_by('-ped_fecha_pedido')

    for pedido in pedidos:
        # Calcular el estado como texto
        estado_map = {1: 'Pendiente', 2: 'Confirmado', 3: 'En preparación',
                      4: 'Enviado', 5: 'Entregado', 6: 'Cancelado'}
        pedido.estado_texto = estado_map.get(int(pedido.ped_estado or 1), 'Desconocido')
        pedido.productos_count = PedidosProductos.objects.filter(ped=pedido).count()

    return render(request, 'Multiverse/mis_pedidos.html', {
        'pedidos': pedidos,
        'sidebar': 0,
    })


@Login_requerido()
def pedido_detalle_view(request, ped_id):
    """Muestra el detalle de un pedido específico del cliente."""
    pedido = get_object_or_404(Pedidos, pk=ped_id, usu=request.user)

    estado_map = {1: 'Pendiente', 2: 'Confirmado', 3: 'En preparación',
                  4: 'Enviado', 5: 'Entregado', 6: 'Cancelado'}
    pedido.estado_texto = estado_map.get(int(pedido.ped_estado or 1), 'Desconocido')

    productos = PedidosProductos.objects.filter(ped=pedido).select_related('prod', 'pped_estado')

    return render(request, 'Multiverse/pedido_detalle.html', {
        'pedido': pedido,
        'productos': productos,
        'sidebar': 0,
    })


# ─── Panel de Control (visor dark, capa aparte) ───

@Login_requerido()
def panel_dashboard(request):
    # Solo administradores (perfil_id=1) pueden ver el panel
    if not getattr(request.user, 'usuario_id_perfil_id', None) == 1:
        messages.error(request, 'No tienes permiso para acceder al panel de gestión.')
        return redirect('home')
    total_productos = Productos.objects.count()
    total_usuarios = Usuarios.objects.count()
    total_pedidos = Pedidos.objects.count()
    total_categorias = Categoria.objects.count()
    total_perfiles = Perfiles.objects.count()

    estado_map = {1: 'Pendiente', 2: 'Confirmado', 3: 'En preparacion',
                  4: 'Enviado', 5: 'Entregado', 6: 'Cancelado'}
    pedidos_pendientes = Pedidos.objects.filter(ped_estado=1).count()
    pedidos_recientes = Pedidos.objects.select_related('usu').order_by('-ped_fecha_pedido')[:5]
    for p in pedidos_recientes:
        p.estado_texto = estado_map.get(int(p.ped_estado or 1), 'Desconocido')

    context = {
        'total_productos': total_productos,
        'total_usuarios': total_usuarios,
        'total_pedidos': total_pedidos,
        'total_categorias': total_categorias,
        'total_perfiles': total_perfiles,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_recientes': pedidos_recientes,
        'section': 'dashboard',
        'sidebar': 0,
    }
    return render(request, 'Admin/panel_dashboard.html', context)


@Login_requerido()
def panel_productos_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    page = int(request.GET.get('page', 1))
    query = request.GET.get('q', '')
    paginate_by = 10

    queryset = Productos.objects.select_related('cat').all().order_by('prod_id')
    if query:
        queryset = queryset.filter(prod_nombre__icontains=query)

    paginator = Paginator(queryset, paginate_by)
    productos_page = paginator.get_page(page)

    return render(request, 'Admin/panel_productos.html', {
        'productos': productos_page.object_list,
        'page': page,
        'total_paginas': paginator.num_pages,
        'query': query,
        'section': 'productos',
        'sidebar': 0,
    })


@Login_requerido()
def panel_productos_crear(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    if request.method == 'POST':
        form = ProductosForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                messages.success(request, 'Producto creado exitosamente.')
                return redirect('panel_productos')
    else:
        form = ProductosForm()

    return render(request, 'Admin/panel_producto_form.html', {
        'form': form,
        'section': 'productos',
        'sidebar': 0,
    })


@Login_requerido()
def panel_productos_editar(request, pk):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
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
                messages.success(request, 'Producto actualizado exitosamente.')
                return redirect('panel_productos')
    else:
        form = ProductosForm(instance=producto)

    return render(request, 'Admin/panel_producto_form.html', {
        'form': form,
        'producto': producto,
        'section': 'productos',
        'sidebar': 0,
    })


@Login_requerido()
def panel_usuarios_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    page = int(request.GET.get('page', 1))
    query = request.GET.get('q', '')
    paginate_by = 10

    queryset = Usuarios.objects.select_related('usuario_id_sexo', 'usuario_id_perfil').all().order_by('id_usuario')
    if query:
        queryset = queryset.filter(Q(nombre__icontains=query) | Q(id_usuario__icontains=query))

    paginator = Paginator(queryset, paginate_by)
    usuarios_page = paginator.get_page(page)

    return render(request, 'Admin/panel_usuarios.html', {
        'usuarios': usuarios_page.object_list,
        'page': page,
        'total_paginas': paginator.num_pages,
        'query': query,
        'section': 'usuarios',
        'sidebar': 0,
    })


@Login_requerido()
def panel_usuarios_crear(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')

    if request.method == 'POST':
        form = UsuariosForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    usuario = form.save()
                    contactos = request.POST.getlist('contactos_relacionados')
                    if contactos:
                        ContactosCreateView(contactos, usuario.id_usuario)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                messages.success(request, 'Usuario creado exitosamente.')
                return redirect('panel_usuarios')
    else:
        form = UsuariosForm()

    return render(request, 'Admin/panel_usuario_form.html', {
        'form': form,
        'Tipo_Contacto': Tipo_Contacto,
        'section': 'usuarios',
        'sidebar': 0,
    })


@Login_requerido()
def panel_usuarios_editar(request, pk):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    usuario = get_object_or_404(Usuarios, pk=pk)
    contactos = Contactos.objects.filter(id_usuario=usuario)
    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')

    if request.method == 'POST':
        form = UsuariosForm(request.POST, instance=usuario)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    contactos_data = request.POST.getlist('contactos_relacionados_editados')
                    contactos_actualizar = []
                    for item in contactos_data:
                        parts = item.split(',')
                        if len(parts) == 3:
                            contactos_actualizar.append({
                                'id_contacto': parts[2],
                                'tipo_contacto': parts[0],
                                'dato_contacto': parts[1],
                            })
                    if contactos_actualizar:
                        # Reusamos la funcion existente
                        ContactosUpdateView(contactos_actualizar)
            except DatabaseError as e:
                form.add_error(None, _extract_db_message(e))
            else:
                messages.success(request, 'Usuario actualizado exitosamente.')
                return redirect('panel_usuarios')
    else:
        form = UsuariosForm(instance=usuario)

    return render(request, 'Admin/panel_usuario_form.html', {
        'form': form,
        'usuario': usuario,
        'contactos': contactos,
        'Tipo_Contacto': Tipo_Contacto,
        'section': 'usuarios',
        'sidebar': 0,
    })


@Login_requerido()
def panel_pedidos_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    estado_map = {1: 'Pendiente', 2: 'Confirmado', 3: 'En preparacion',
                  4: 'Enviado', 5: 'Entregado', 6: 'Cancelado'}
    pedidos = Pedidos.objects.select_related('usu').all().order_by('-ped_fecha_pedido')[:20]
    for p in pedidos:
        p.estado_texto = estado_map.get(int(p.ped_estado or 1), 'Desconocido')
    return render(request, 'Admin/panel_pedidos.html', {
        'pedidos': pedidos,
        'section': 'pedidos',
        'sidebar': 0,
    })


@Login_requerido()
def panel_categorias_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    categorias = Categoria.objects.all().order_by('cat_id')
    return render(request, 'Admin/panel_categorias.html', {
        'categorias': categorias,
        'section': 'categorias',
        'sidebar': 0,
    })


@Login_requerido()
def panel_roles_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    roles = Roles.objects.all().order_by('id_rol')
    return render(request, 'Admin/panel_roles.html', {
        'roles': roles,
        'section': 'roles',
        'sidebar': 0,
    })


@Login_requerido()
def panel_perfiles_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    perfiles = Perfiles.objects.select_related('rol_id').all().order_by('id_perfil')
    return render(request, 'Admin/panel_perfiles.html', {
        'perfiles': perfiles,
        'section': 'perfiles',
        'sidebar': 0,
    })


@Login_requerido()
def panel_sexos_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    sexos = Sexos.objects.all().order_by('id_sexo')
    return render(request, 'Admin/panel_sexos.html', {
        'sexos': sexos,
        'section': 'sexos',
        'sidebar': 0,
    })


@Login_requerido()
def panel_estados_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    estados = EstadoPedidos.objects.all().order_by('id_estado')
    return render(request, 'Admin/panel_estados.html', {
        'estados': estados,
        'section': 'estados',
        'sidebar': 0,
    })


@Login_requerido()
def panel_consultas_list(request):
    if getattr(request.user, 'usuario_id_perfil_id', None) != 1:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('home')
    consultas = Consultas_Dinamicas.objects.all().order_by('id_consulta')
    return render(request, 'Admin/panel_consultas.html', {
        'consultas': consultas,
        'section': 'consultas',
        'sidebar': 0,
    })