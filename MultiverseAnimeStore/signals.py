import json

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from .models import PedidosProductos, Productos, Pedidos, Productos_Auditoria


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


@receiver(pre_save, sender=Pedidos)
def restaurar_stock_si_cancelado(sender, instance, **kwargs):
    if instance.pk is None:
        return
    try:
        anterior = Pedidos.objects.only('ped_estado_id').get(pk=instance.pk)
    except Pedidos.DoesNotExist:
        return
    if instance.ped_estado_id == 6 and anterior.ped_estado_id != 6:
        productos_pedido = PedidosProductos.objects.filter(ped=instance)
        for pp in productos_pedido:
            Productos.objects.filter(pk=pp.prod_id).update(
                prod_stock=F('prod_stock') + pp.pped_cantidad
            )


def _producto_to_dict(producto):
    def _decimal(val):
        if val is None:
            return None
        return '{:.2f}'.format(val)

    return {
        'prod_id': producto.prod_id,
        'cat_id': producto.cat_id,
        'prod_nombre': producto.prod_nombre,
        'prod_descripcion': producto.prod_descripcion,
        'prod_precio_venta': _decimal(producto.prod_precio_venta),
        'prod_stock': producto.prod_stock,
        'prod_imagen_url': producto.prod_imagen_url,
        'prod_descuento': _decimal(producto.prod_descuento),
    }


@receiver(pre_save, sender=Productos)
def capturar_valores_anteriores(sender, instance, **kwargs):
    if instance.pk is None:
        instance._old_values = None
        return
    try:
        old = Productos.objects.get(pk=instance.pk)
        instance._old_values = _producto_to_dict(old)
    except Productos.DoesNotExist:
        instance._old_values = None


@receiver(post_save, sender=Productos)
def auditar_producto_save(sender, instance, created, **kwargs):
    data = _producto_to_dict(instance)

    if created:
        Productos_Auditoria.objects.create(
            model_name='Productos',
            object_id=instance.prod_id,
            au_type=1,
            auditoria=json.dumps(data, ensure_ascii=False),
        )
        return

    old_data = getattr(instance, '_old_values', None)
    if old_data is None:
        return

    update_fields = kwargs.get('update_fields')
    if update_fields is not None:
        changed_field_names = {f.name for f in update_fields}
    else:
        changed_field_names = set(data.keys())

    changed_data = {}
    for field in changed_field_names:
        new_val = data.get(field)
        old_val = old_data.get(field)
        if new_val != old_val:
            changed_data[field] = (old_val, new_val)

    if not changed_data:
        return

    old = {field: vals[0] for field, vals in changed_data.items()}
    new = {field: vals[1] for field, vals in changed_data.items()}

    Productos_Auditoria.objects.create(
        model_name='Productos',
        object_id=instance.prod_id,
        au_type=2,
        auditoria=json.dumps({'old': old, 'new': new}, ensure_ascii=False),
    )


@receiver(post_delete, sender=Productos)
def auditar_producto_delete(sender, instance, **kwargs):
    data = _producto_to_dict(instance)
    Productos_Auditoria.objects.create(
        model_name='Productos',
        object_id=instance.prod_id,
        au_type=3,
        auditoria=json.dumps(data, ensure_ascii=False),
    )
