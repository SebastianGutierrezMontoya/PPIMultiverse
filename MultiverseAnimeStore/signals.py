from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from .models import PedidosProductos, Productos, Pedidos


@receiver(pre_save, sender=PedidosProductos)
def validar_stock(sender, instance, **kwargs):
    if instance.pped_cantidad is None:
        return
    producto = Productos.objects.filter(pk=instance.prod_id).only('prod_stock').first()
    if producto is None:
        raise ValidationError(f'Producto no encontrado')
    if producto.prod_stock is None or producto.prod_stock < instance.pped_cantidad:
        raise ValidationError(
            f'Stock insuficiente para "{producto.prod_nombre}". '
            f'Disponible: {producto.prod_stock if producto.prod_stock is not None else 0}, '
            f'solicitado: {instance.pped_cantidad}'
        )


@receiver(post_save, sender=PedidosProductos)
def descontar_stock_y_actualizar_total(sender, instance, created, **kwargs):
    if not created:
        return

    Productos.objects.filter(pk=instance.prod_id).update(
        prod_stock=F('prod_stock') - instance.pped_cantidad
    )

    total_real = PedidosProductos.objects.filter(ped=instance.ped).aggregate(
        total=Sum('pped_total')
    )['total'] or 0
    Pedidos.objects.filter(pk=instance.ped.ped_id).update(ped_total=total_real)


@receiver(pre_save, sender=PedidosProductos)
def validar_datos_pedido_producto(sender, instance, **kwargs):
    if instance.pped_cantidad is not None and instance.pped_cantidad <= 0:
        raise ValidationError('La cantidad debe ser mayor a 0')
    if instance.pped_precio_unitario is not None and instance.pped_precio_unitario < 0:
        raise ValidationError('El precio unitario no puede ser negativo')
