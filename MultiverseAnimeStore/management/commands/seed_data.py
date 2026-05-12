from django.core.management.base import BaseCommand
from MultiverseAnimeStore.models import (
    Sexos, Roles, Perfiles, Modulos, Perfilpermisos,
    EstadoPedidos, Usuarios, Config_Contacto, Categoria, Productos
)
import hashlib
from decimal import Decimal


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class Command(BaseCommand):
    help = 'Seed initial data: sexos, roles, perfiles, modulos, permisos, estado_pedidos, usuario admin, categorías, productos de prueba'

    def handle(self, *args, **kwargs):
        self.seed_sexos()
        self.seed_estado_pedidos()
        self.seed_roles()
        self.seed_perfiles()
        self.seed_modulos()
        self.seed_perfilpermisos()
        self.seed_admin_user()
        self.seed_config_contacto()
        self.seed_categorias()
        self.seed_productos()
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

    def seed_categorias(self):
        categorias = [
            ('CAT-1', 'Figuras de Acción', 'Figuras coleccionables de personajes anime'),
            ('CAT-2', 'Manga', 'Manga y novelas ligeras'),
            ('CAT-3', 'Accesorios', 'Llaveros, pulseras y accesorios anime'),
            ('CAT-4', 'Ropa', 'Camisetas, hoodies y más'),
            ('CAT-5', 'Tarjetas TCG', 'Cartas coleccionables y juegos de cartas'),
            ('CAT-6', 'Peluches', 'Peluches suaves de tus personajes favoritos'),
            ('CAT-7', 'Pósters', 'Pósters y láminas decorativas'),
        ]
        created = 0
        for pk, nombre, desc in categorias:
            _, c = Categoria.objects.get_or_create(
                cat_id=pk,
                defaults={'cat_nombre': nombre, 'cat_descripcion': desc}
            )
            created += c
        self.stdout.write(f'Categorías: {created} creadas.')

    def seed_productos(self):
        productos = [
            # Figuras de Acción
            ('PROD-1', 'Goku Ultra Instinct', 'Figura de acción Goku Ultra Instinct 30cm', 'CAT-1', 85000, 20, 10),
            ('PROD-2', 'Naruto Modo Sabio', 'Figura Naruto Modo Sabio 25cm', 'CAT-1', 72000, 15, 5),
            ('PROD-3', 'Zoro Roronoa', 'Figura Zoro Roronoa 3 espadas 28cm', 'CAT-1', 95000, 12, 0),
            ('PROD-4', 'Luffy Gear 5', 'Figura Monkey D. Luffy Gear 5 30cm', 'CAT-1', 89900, 18, 8),
            # Manga
            ('PROD-5', 'One Piece Vol. 1', 'One Piece volumen 1 - Romance Dawn', 'CAT-2', 25000, 50, 0),
            ('PROD-6', 'Jujutsu Kaisen Vol. 1', 'Jujutsu Kaisen volumen 1', 'CAT-2', 22000, 45, 10),
            ('PROD-7', 'Attack on Titan Vol. 1', 'Ataque a los Titanes volumen 1', 'CAT-2', 23000, 30, 0),
            ('PROD-8', 'Demon Slayer Vol. 1', 'Kimetsu no Yaiba volumen 1', 'CAT-2', 22000, 35, 5),
            # Accesorios
            ('PROD-9', 'Llavero Sharingan', 'Llavero ojo Sharingan de acero', 'CAT-3', 12000, 100, 0),
            ('PROD-10', 'Pulsera Akatsuki', 'Pulsera de cuero con dije Akatsuki', 'CAT-3', 18000, 80, 0),
            ('PROD-11', 'Anillo Esfera del Dragón', 'Anillo con esfera del dragón 4 estrellas', 'CAT-3', 25000, 40, 15),
            # Ropa
            ('PROD-12', 'Camiseta Multiverse', 'Camiseta algodón diseño exclusivo Multiverse', 'CAT-4', 45000, 30, 0),
            ('PROD-13', 'Hoodie Akatsuki', 'Hoodie negro nubes rojas Akatsuki', 'CAT-4', 95000, 20, 10),
            ('PROD-14', 'Gorra Bola de Dragón', 'Gorra con bordado esfera del dragón', 'CAT-4', 32000, 25, 0),
            # Tarjetas TCG
            ('PROD-15', 'Booster One Piece TCG', 'Sobre de 12 cartas One Piece TCG', 'CAT-5', 18000, 60, 0),
            ('PROD-16', 'Deck Dragon Ball Z', 'Mazo básico Dragon Ball Z TCG', 'CAT-5', 35000, 25, 5),
            # Peluches
            ('PROD-17', 'Peluche Pikachu', 'Peluche Pikachu 25cm', 'CAT-6', 42000, 15, 0),
            ('PROD-18', 'Peluche Totoro', 'Peluche Totoro gigante 40cm', 'CAT-6', 65000, 10, 0),
            ('PROD-19', 'Peluche Eevee', 'Peluche Eevee 20cm', 'CAT-6', 38000, 20, 15),
            # Pósters
            ('PROD-20', 'Póster Sword Art Online', 'Lámina A2 Sword Art Online', 'CAT-7', 15000, 40, 0),
            ('PROD-21', 'Póster My Hero Academia', 'Lámina A2 My Hero Academia', 'CAT-7', 15000, 35, 0),
            ('PROD-22', 'Combo 3 Pósters Anime', 'Set 3 láminas A2: Demon Slayer + One Piece + Jujutsu', 'CAT-7', 35000, 20, 20),
        ]
        created = 0
        for pk, nombre, desc, cat_id, precio, stock, descuento in productos:
            cat = Categoria.objects.get(cat_id=cat_id)
            _, c = Productos.objects.get_or_create(
                prod_id=pk,
                defaults={
                    'prod_nombre': nombre,
                    'prod_descripcion': desc,
                    'cat': cat,
                    'prod_precio_venta': Decimal(str(precio)),
                    'prod_stock': stock,
                    'prod_descuento': Decimal(str(descuento)),
                }
            )
            created += c
        self.stdout.write(f'Productos: {created} creados.')
