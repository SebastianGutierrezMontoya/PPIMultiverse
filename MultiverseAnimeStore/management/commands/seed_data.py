from django.core.management.base import BaseCommand
from MultiverseAnimeStore.models import (
    Sexos, Roles, Perfiles, Modulos, Perfilpermisos,
    EstadoPedidos, Usuarios, Config_Contacto
)
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class Command(BaseCommand):
    help = 'Seed initial data: sexos, roles, perfiles, modulos, permisos, estado_pedidos, usuario admin'

    def handle(self, *args, **kwargs):
        self.seed_sexos()
        self.seed_estado_pedidos()
        self.seed_roles()
        self.seed_perfiles()
        self.seed_modulos()
        self.seed_perfilpermisos()
        self.seed_admin_user()
        self.seed_config_contacto()
        self.stdout.write(self.style.SUCCESS('Seed completado exitosamente.'))

    def seed_sexos(self):
        created = 0
        for pk, nombre in [(1, 'Hombre'), (2, 'Mujer'), (3, 'Otro')]:
            _, c = Sexos.objects.get_or_create(id_sexo=pk, defaults={'nombre_sexo': nombre})
            created += c
        self.stdout.write(f'Sexos: {created} creados, resto ya existían.')

    def seed_estado_pedidos(self):
        estados = [
            (1, 'Pendiente'), (2, 'Confirmado'), (3, 'En preparación'),
            (4, 'Enviado'), (5, 'Entregado'), (6, 'Cancelado'),
        ]
        created = 0
        for pk, nombre in estados:
            _, c = EstadoPedidos.objects.get_or_create(est_id=pk, defaults={'est_nombre': nombre})
            created += c
        self.stdout.write(f'EstadoPedidos: {created} creados.')

    def seed_roles(self):
        created = 0
        for pk, nombre, desc in [
            (1, 'Administrador', 'Acceso total al sistema'),
            (2, 'Cliente', 'Usuario comprador'),
        ]:
            _, c = Roles.objects.get_or_create(id_rol=pk, defaults={'nombre': nombre, 'descripcion': desc})
            created += c
        self.stdout.write(f'Roles: {created} creados.')

    def seed_perfiles(self):
        created = 0
        for pk, nombre, desc, rol_id in [
            (1, 'Admin', 'Perfil administrador con todos los permisos', 1),
            (2, 'Cliente', 'Perfil cliente con permisos básicos', 2),
        ]:
            rol = Roles.objects.get(id_rol=rol_id)
            _, c = Perfiles.objects.get_or_create(
                id_perfil=pk,
                defaults={'nombre': nombre, 'descripcion': desc, 'rol_id': rol}
            )
            created += c
        self.stdout.write(f'Perfiles: {created} creados.')

    def seed_modulos(self):
        modulos = [
            ('Categoria', 'Gestión de categorías de productos', '/AdminMultiverse/categorias/'),
            ('Productos', 'Gestión de productos del catálogo', '/AdminMultiverse/productos/'),
            ('Pedidos', 'Gestión de pedidos de clientes', '/AdminMultiverse/pedidos/'),
            ('Usuarios', 'Gestión de usuarios del sistema', '/AdminMultiverse/usuarios/'),
            ('Contactos', 'Gestión de datos de contacto', '/AdminMultiverse/contactos/'),
            ('Roles', 'Gestión de roles de usuario', '/AdminMultiverse/roles/'),
            ('Perfiles', 'Gestión de perfiles y permisos', '/AdminMultiverse/perfiles/'),
            ('Sexos', 'Gestión de sexos', '/AdminMultiverse/sexos/'),
            ('EstadoPedidos', 'Gestión de estados de pedido', '/AdminMultiverse/estado_pedidos/'),
            ('Config_Contactos', 'Configuración de tipos de contacto', '/AdminMultiverse/config_contacto/'),
            ('Consultas', 'Consultas dinámicas SQL', '/AdminMultiverse/consultas_dinamicas/'),
        ]
        created = 0
        for nombre, desc, url in modulos:
            _, c = Modulos.objects.get_or_create(
                nombre_mod=nombre,
                defaults={'descripcion': desc, 'url_mod': url}
            )
            created += c
        self.stdout.write(f'Módulos: {created} creados.')

    def seed_perfilpermisos(self):
        perfil_admin = Perfiles.objects.get(id_perfil=1)
        modulos = Modulos.objects.all()
        created = 0
        for modulo in modulos:
            _, c = Perfilpermisos.objects.get_or_create(
                perfil_id=perfil_admin,
                mod_id=modulo,
                defaults={'can_read': 'Y', 'can_create': 'Y', 'can_update': 'Y', 'can_delete': 'Y'}
            )
            created += c
        self.stdout.write(f'Perfilpermisos (Admin): {created} registros creados.')

    def seed_admin_user(self):
        if Usuarios.objects.filter(id_usuario='admin').exists():
            self.stdout.write('Usuario admin ya existe. Se omite.')
            return

        perfil_admin = Perfiles.objects.get(id_perfil=1)
        sexo = Sexos.objects.get(id_sexo=3)
        Usuarios.objects.create(
            id_usuario='admin',
            nombre='Admin',
            primer_apellido='Sistema',
            password_hash=hash_password('admin123'),
            usuario_id_sexo=sexo,
            usuario_id_perfil=perfil_admin,
            activo=1
        )
        self.stdout.write('Usuario "admin" creado (contraseña: admin123).')

    def seed_config_contacto(self):
        tipos = [
            (1, 'Teléfono', 'Número de contacto telefónico', None, 7, 15, 'Teléfono inválido'),
            (2, 'Email', 'Correo electrónico', None, 5, 100, 'Email inválido'),
            (3, 'Dirección', 'Dirección física', None, 5, 200, 'Dirección inválida'),
        ]
        created = 0
        for pk, nombre, desc, regex, min_l, max_l, msg in tipos:
            _, c = Config_Contacto.objects.get_or_create(
                id_regla=pk,
                defaults={
                    'nombre_contacto': nombre,
                    'descripcion': desc,
                    'regex_val': regex,
                    'min_length': min_l,
                    'max_length': max_l,
                    'mensaje_error': msg,
                }
            )
            created += c
        self.stdout.write(f'Config_Contacto: {created} registros creados.')
