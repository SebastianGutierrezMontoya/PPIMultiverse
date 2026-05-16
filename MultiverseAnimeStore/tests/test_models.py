from django.test import TestCase
from django.db import IntegrityError
from ..models import (
    Productos, Categoria, Usuarios, Sexos, Perfiles, Roles,
    Pedidos, EstadoPedidos, Contactos, Config_Contacto
)


class ProductosConstraintsTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(cat_id="CAT-TEST", cat_nombre="Test Cat")

    def test_precio_venta_debe_ser_positivo(self):
        """ck_precio_positivo: prod_precio_venta > 0"""
        with self.assertRaises(IntegrityError):
            Productos.objects.create(
                prod_id="PROD-TST1", cat=self.cat, prod_precio_venta=1
            )

    def test_stock_no_negativo(self):
        """ck_stock_no_negativo: prod_stock >= 0"""
        with self.assertRaises(IntegrityError):
            Productos.objects.create(
                prod_id="PROD-TST2", cat=self.cat, prod_stock=-1
            )

    def test_descuento_no_excede_99(self):
        """ck_descuento_maximo: prod_descuento <= 99"""
        with self.assertRaises(IntegrityError):
            Productos.objects.create(
                prod_id="PROD-TST3", cat=self.cat, prod_descuento=100
            )

    def test_descuento_99_es_valido(self):
        """99 es el máximo permitido"""
        prod = Productos.objects.create(
            prod_id="PROD-TST4", cat=self.cat, prod_descuento=99
        )
        self.assertEqual(prod.prod_descuento, 99)


class UsuariosConstraintsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sexo = Sexos.objects.create(id_sexo=1, nombre_sexo="Test")
        cls.rol = Roles.objects.create(id_rol=1, nombre="Test")
        cls.perfil = Perfiles.objects.create(
            id_perfil=1, nombre="Test", rol_id=cls.rol
        )

    def _base_usuario(self, id_suffix=""):
        return Usuarios.objects.create(
            id_usuario=f"TST-USR{id_suffix}",
            nombre="Test",
            primer_apellido="User",
            password_hash="abc",
            usuario_id_sexo=self.sexo,
            usuario_id_perfil=self.perfil,
        )

    def test_activo_0_es_valido(self):
        user = self._base_usuario("0")
        user.activo = 0
        user.save()
        self.assertEqual(user.activo, 0)

    def test_activo_1_es_valido(self):
        user = self._base_usuario("1")
        user.activo = 1
        user.save()
        self.assertEqual(user.activo, 1)

    def test_activo_2_es_invalido(self):
        """ck_activo_valido: activo solo acepta 0 o 1"""
        with self.assertRaises(IntegrityError):
            user = self._base_usuario("2")
            user.activo = 2
            user.save()


class PedidosConstraintsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sexo = Sexos.objects.create(id_sexo=1, nombre_sexo="Test")
        rol = Roles.objects.create(id_rol=1, nombre="Test")
        perfil = Perfiles.objects.create(id_perfil=1, nombre="Test", rol_id=rol)
        cls.usuario = Usuarios.objects.create(
            id_usuario="TST-USR-PED",
            nombre="Test",
            primer_apellido="User",
            password_hash="abc",
            usuario_id_sexo=sexo,
            usuario_id_perfil=perfil,
        )
        cls.estado = EstadoPedidos.objects.create(est_id=1, est_nombre="Test")

    def test_total_negativo_es_invalido(self):
        """ck_total_no_negativo: ped_total >= 0"""
        with self.assertRaises(IntegrityError):
            Pedidos.objects.create(
                ped_id=999,
                usu=self.usuario,
                ped_total=-1,
                ped_estado=self.estado,
            )

    def test_total_0_es_valido(self):
        pedido = Pedidos.objects.create(
            ped_id=1000,
            usu=self.usuario,
            ped_total=0,
            ped_estado=self.estado,
        )
        self.assertEqual(pedido.ped_total, 0)


class ContactosUniqueTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        sexo = Sexos.objects.create(id_sexo=1, nombre_sexo="Test")
        rol = Roles.objects.create(id_rol=1, nombre="Test")
        perfil = Perfiles.objects.create(id_perfil=1, nombre="Test", rol_id=rol)
        cls.usuario = Usuarios.objects.create(
            id_usuario="TST-USR-CONT",
            nombre="Test",
            primer_apellido="User",
            password_hash="abc",
            usuario_id_sexo=sexo,
            usuario_id_perfil=perfil,
        )
        cls.tipo_tel = Config_Contacto.objects.create(
            id_regla=1, nombre_contacto="Teléfono", regex_val="",
            min_length=7, max_length=15, mensaje_error="Err"
        )

    def test_no_duplicar_mismo_tipo_mismo_usuario(self):
        """uq_usuario_tipo_contacto: unique (id_usuario, tipo_contacto)"""
        Contactos.objects.create(
            id_contacto=1,
            dato_contacto="123456789",
            tipo_contacto=self.tipo_tel,
            id_usuario=self.usuario,
        )
        with self.assertRaises(IntegrityError):
            Contactos.objects.create(
                id_contacto=2,
                dato_contacto="987654321",
                tipo_contacto=self.tipo_tel,
                id_usuario=self.usuario,
            )
