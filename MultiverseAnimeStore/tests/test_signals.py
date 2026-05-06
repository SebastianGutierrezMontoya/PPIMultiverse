from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import models
from ..models import (
    Productos, Categoria, Usuarios, Sexos, Perfiles, Roles,
    Pedidos, EstadoPedidos, PedidosProductos
)


class BaseSignalTest(TestCase):
    """Datos compartidos para todos los tests de signals."""

    @classmethod
    def setUpTestData(cls):
        cat = Categoria.objects.create(cat_id="CAT-SIG", cat_nombre="Signal Test")
        cls.producto_con_stock = Productos.objects.create(
            prod_id="PROD-SIG1", cat=cat, prod_nombre="Con Stock",
            prod_precio_venta=100, prod_stock=10,
        )
        cls.producto_sin_stock = Productos.objects.create(
            prod_id="PROD-SIG2", cat=cat, prod_nombre="Sin Stock",
            prod_precio_venta=50, prod_stock=0,
        )
        cls.producto_stock_nulo = Productos.objects.create(
            prod_id="PROD-SIG3", cat=cat, prod_nombre="Stock Nulo",
            prod_precio_venta=75, prod_stock=None,
        )
        sexo = Sexos.objects.create(id_sexo=1, nombre_sexo="Test")
        rol = Roles.objects.create(id_rol=1, nombre="Test")
        perfil = Perfiles.objects.create(id_perfil=1, nombre="Test", rol_id=rol)
        usuario = Usuarios.objects.create(
            id_usuario="TST-USR-SIG",
            nombre="Test", primer_apellido="User",
            password_hash="abc",
            usuario_id_sexo=sexo, usuario_id_perfil=perfil,
        )
        cls.estado = EstadoPedidos.objects.create(est_id=1, est_nombre="Pendiente")
        cls.pedido = Pedidos.objects.create(
            ped_id=1, usu=usuario, ped_total=0, ped_estado=cls.estado,
        )


class ValidarStockSignalTest(BaseSignalTest):

    def test_stock_insuficiente_rechazado(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_con_stock,
                pped_cantidad=20, pped_precio_unitario=100,
                pped_total=2000, pped_estado=self.estado,
            )

    def test_stock_suficiente_aceptado(self):
        pp = PedidosProductos.objects.create(
            ped=self.pedido, prod=self.producto_con_stock,
            pped_cantidad=5, pped_precio_unitario=100,
            pped_total=500, pped_estado=self.estado,
        )
        self.assertEqual(pp.pped_cantidad, 5)

    def test_stock_0_rechaza_cualquier_cantidad(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_sin_stock,
                pped_cantidad=1, pped_precio_unitario=50,
                pped_total=50, pped_estado=self.estado,
            )

    def test_stock_nulo_rechazado(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_stock_nulo,
                pped_cantidad=1, pped_precio_unitario=75,
                pped_total=75, pped_estado=self.estado,
            )

    def test_cantidad_none_no_dispara_validacion(self):
        pp = PedidosProductos.objects.create(
            ped=self.pedido, prod=self.producto_con_stock,
            pped_cantidad=None, pped_precio_unitario=100,
            pped_total=500, pped_estado=self.estado,
        )
        self.assertIsNone(pp.pped_cantidad)


class DescontarStockSignalTest(BaseSignalTest):

    def test_stock_se_descuenta_al_crear(self):
        stock_inicial = Productos.objects.get(pk="PROD-SIG1").prod_stock
        PedidosProductos.objects.create(
            ped=self.pedido, prod=self.producto_con_stock,
            pped_cantidad=3, pped_precio_unitario=100,
            pped_total=300, pped_estado=self.estado,
        )
        stock_final = Productos.objects.get(pk="PROD-SIG1").prod_stock
        self.assertEqual(stock_final, stock_inicial - 3)

    def test_ped_total_se_actualiza_al_crear(self):
        PedidosProductos.objects.create(
            ped=self.pedido, prod=self.producto_con_stock,
            pped_cantidad=2, pped_precio_unitario=100,
            pped_total=200, pped_estado=self.estado,
        )
        pedido_actualizado = Pedidos.objects.get(pk=1)
        self.assertEqual(pedido_actualizado.ped_total, 200)

    def test_multiples_productos_acumulan_total(self):
        PedidosProductos.objects.create(
            ped=self.pedido, prod=self.producto_con_stock,
            pped_cantidad=2, pped_precio_unitario=100,
            pped_total=200, pped_estado=self.estado,
        )
        producto_extra = Productos.objects.create(
            prod_id="PROD-SIG4", cat=self.producto_con_stock.cat,
            prod_nombre="Extra", prod_precio_venta=50, prod_stock=10,
        )
        PedidosProductos.objects.create(
            ped=self.pedido, prod=producto_extra,
            pped_cantidad=3, pped_precio_unitario=50,
            pped_total=150, pped_estado=self.estado,
        )
        pedido_actualizado = Pedidos.objects.get(pk=1)
        self.assertEqual(pedido_actualizado.ped_total, 350)


class ValidarDatosPedidoProductoTest(BaseSignalTest):

    def test_cantidad_0_rechazado(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_con_stock,
                pped_cantidad=0, pped_precio_unitario=100,
                pped_total=0, pped_estado=self.estado,
            )

    def test_cantidad_negativa_rechazado(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_con_stock,
                pped_cantidad=-1, pped_precio_unitario=100,
                pped_total=-100, pped_estado=self.estado,
            )

    def test_precio_negativo_rechazado(self):
        with self.assertRaises(ValidationError):
            PedidosProductos.objects.create(
                ped=self.pedido, prod=self.producto_con_stock,
                pped_cantidad=1, pped_precio_unitario=-50,
                pped_total=-50, pped_estado=self.estado,
            )
