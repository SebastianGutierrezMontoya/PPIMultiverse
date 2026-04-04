from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Pedidos, PedidosProductos, Productos, Roles, Perfiles, Perfilpermisos, Modulos, Usuarios, Sexos, EstadoPedidos, Config_Contacto, Productos_Auditoria, Consultas_Dinamicas
from .forms import PedidosForm, UsuariosForm, RolesForm, PerfilesForm, CategoriaForm, ProductosForm, PedidoProductoUpdateForm, ConsultasDinamicasForm, EstadoPedidosForm
from django.db.models import F, ExpressionWrapper, DecimalField, Sum, Q, Max
from django.http import HttpResponseRedirect
from django.db import DatabaseError, transaction, connection
from django.contrib import messages
import re
from functools import wraps
from django.forms import modelform_factory
import psycopg2
import json
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


# def Permisos_Admin(modulo, tipo, redirect_url='admin_home'):
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapper(request, *args, **kwargs):


#             if not getattr(request.user, 'is_authenticated', False):
#                 return redirect(redirect_url)
            


#             return view_func(request, *args, **kwargs)

#         return wrapper

#     return decorator

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

def admin_home(request):
    return render(request, 'admin_home.html')


# contraseña hashing 
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Login
def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        contraseña = request.POST.get('contraseña')

        try:
            user = Usuarios.objects.get(id_usuario=usuario, password_hash=hash_password(contraseña))
            # user = authenticate(request, username=usuario, password=hash_password(contraseña))  # Si usas el sistema de autenticación de Django
            # login(request, user)  # Si usas el sistema de autenticación de Django
            request.session['user_id'] = user.id_usuario
            return redirect('admin_home')
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

            Usuarios.objects.create(
                id_usuario=usuario,
                password_hash=hash_password(contraseña),
                nombre=nombre,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
                fecha_nacimiento=fecha_nacimiento,
                usuario_id_sexo=sexo
            )

            ContactosCreateView(contactos_relacionados, usuario)
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        
    Tipo_Contacto = Config_Contacto.objects.values('id_regla', 'nombre_contacto')
    Sexo = Sexos.objects.values('id_sexo', 'nombre_sexo')

    return render(request, 'Sesion/register.html', {'sidebar': 0, 'Tipo_Contacto': Tipo_Contacto, 'Sexos': Sexo})

# logout
def logout_view(request):
    # Aquí podrías limpiar la sesión o cualquier dato relacionado con el usuario
    # logout(request)  # Si estás usando el sistema de autenticación de Django
    request.session.flush()
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

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

        # VALIDACIÓN FINAL DEL PEDIDO 
        cursor = connection.cursor()
        desactivar_trigger()
        try:
            cursor.execute("CALL sp_cerrar_pedido(%s)", [id_pedido])
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

    return render(request, 'Pedidos/pedidos_productos_form.html', {
        'form': form,
        'objeto': objeto
    })

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

    Estado = None
    
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT fn_estado_pedido(%s)", [pedido.ped_id])
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

    return render(request, 'Pedidos/pedidos_form.html', {
        'form': form,
        'object': pedido,
        'productos_relacionados': productos_relacionados,
        'Estado': Estado,
    })

@Permisos_Admin('Pedidos', 'delete')
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
    fields = '__all__'
    template_name = 'Usuarios/sexos_form.html'
    success_url = reverse_lazy('sexos_list')

@method_decorator(Permisos_Admin('Sexos', 'update'), name='dispatch')
class SexosUpdateView(UpdateView):
    model = Sexos
    fields = '__all__'
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
    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute("SELECT fn_ejecutar_reporte(%s)", [id_reporte])
        cursor.execute('FETCH ALL FROM "<unnamed portal 1>"')

        columnas = [col[0] for col in cursor.description]
        resultados = []

        for fila in cursor.fetchall():
            resultados.append(dict(zip(columnas, fila)))

        cursor.execute("COMMIT")
        return resultados

@Permisos_Admin('Consultas', 'read')
def reporte_view(request, id):
    data = ejecutar_reporte(id)
    return render(request, "ConsultasDinamicas/consultas_reporte.html", {"resultado": data})







def home_view(request):
    return render(request, 'Multiverse/home.html')


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

        if not getattr(request.user, 'is_authenticated', False):
            print("DEBUG: Usuario no autenticado, redirigiendo.")
            messages.error(request, 'Debes iniciar sesión para crear el pedido.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

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
                    usu=request.user,
                    ped_fecha_pedido=date.today(),
                    ped_total=total_calculado,
                    ped_direccion_envio=request.POST.get('ped_direccion_envio', ''),
                    ped_notas=request.POST.get('ped_notas', 'Pedido creado desde carrito público')
                )
                print(f"DEBUG: Pedido creado con ID {pedido.ped_id} para usuario {request.user.id_usuario} con total {total_calculado}")
                PedidosProductosCreateView(productos_seleccionados, pedido.ped_id)

        except DatabaseError as e:
            print(f"Error al crear pedido: {e}")
            messages.error(request, _extract_db_message(e))
            return redirect(request.META.get('HTTP_REFERER', '/'))

        messages.success(request, f'Pedido {pedido.ped_id} creado correctamente.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect(request.META.get('HTTP_REFERER', '/'))


def catalogo_view(request):
    productos = Productos.objects.select_related('cat').all()
    paginate_by = 40
    prod_nombre = request.GET.get('prod_nombre', '')

    if prod_nombre:
        productos = productos.filter(
            Q(prod_nombre__icontains=prod_nombre) | Q(prod_descripcion__icontains=prod_nombre)
        )

    paginator = Paginator(productos, paginate_by)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Multiverse/catalogo.html', {
        'productos': page_obj,
        'prod_nombre': prod_nombre,
    })