# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Categoria(models.Model):
    cat_id = models.CharField(primary_key=True, max_length=10)
    cat_nombre = models.CharField(unique=True, max_length=50, blank=True, null=True)
    cat_descripcion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categoria'
        app_label = 'MultiverseAnimeStore'


class Contactos(models.Model):
    id_contacto = models.FloatField(primary_key=True)
    tipo_contacto = models.CharField(max_length=1, blank=True, null=True)
    dato_contacto = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contactos'


class Estadopedidos(models.Model):
    est_id = models.IntegerField(primary_key=True)
    est_nombre = models.CharField(unique=True, max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estadopedidos'


class Estadousuarios(models.Model):
    id_estado_usuario = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estadousuarios'


class Pedidos(models.Model):
    ped_id = models.IntegerField(primary_key=True)
    usu = models.ForeignKey('Usuarios', models.DO_NOTHING)
    ped_fecha_pedido = models.DateField(blank=True, null=True)
    ped_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ped_estado = models.ForeignKey(Estadopedidos, models.DO_NOTHING, db_column='ped_estado')
    ped_direccion_envio = models.CharField(max_length=200, blank=True, null=True)
    ped_notas = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos'


class PedidosProductos(models.Model):
    pk = models.CompositePrimaryKey('ped_id', 'prod_id')
    ped = models.ForeignKey(Pedidos, models.DO_NOTHING)
    prod = models.ForeignKey('Productos', models.DO_NOTHING)
    pped_cantidad = models.IntegerField(blank=True, null=True)
    pped_precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos_productos'


class Perfiles(models.Model):
    id_perfil = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'perfiles'


class Perfilpermisos(models.Model):
    id_perfil_permiso = models.FloatField(primary_key=True)
    perfil = models.ForeignKey(Perfiles, models.DO_NOTHING)
    permiso = models.ForeignKey('Permisos', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'perfilpermisos'


class Permisos(models.Model):
    id_permiso = models.FloatField(primary_key=True)
    nombre_permiso = models.CharField(unique=True, max_length=100, blank=True, null=True)
    descripcion_permiso = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'permisos'


class Productos(models.Model):
    prod_id = models.CharField(primary_key=True, max_length=10)
    cat = models.ForeignKey(Categoria, models.DO_NOTHING)
    prod_nombre = models.CharField(max_length=100, blank=True, null=True)
    prod_descripcion = models.CharField(max_length=400, blank=True, null=True)
    prod_precio_venta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    prod_stock = models.IntegerField(blank=True, null=True)
    prod_imagen_url = models.CharField(max_length=500, blank=True, null=True)
    prod_descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos'


class ProductosAuditoria(models.Model):
    creation_date = models.DateField(blank=True, null=True)
    au_type = models.IntegerField(blank=True, null=True)
    auditoria = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos_auditoria'


class Roles(models.Model):
    id_rol = models.FloatField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'


class Rolperfiles(models.Model):
    id_rol_perfil = models.FloatField(primary_key=True)
    rol = models.ForeignKey(Roles, models.DO_NOTHING)
    perfil = models.ForeignKey(Perfiles, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'rolperfiles'


class Sexos(models.Model):
    id_sexo = models.FloatField(primary_key=True)
    nombre_sexo = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sexos'


class Usuarios(models.Model):
    id_usuario = models.FloatField(primary_key=True)
    nombre = models.CharField(max_length=300, blank=True, null=True)
    primer_apellido = models.CharField(max_length=50, blank=True, null=True)
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    usuario_id_contacto = models.ForeignKey(Contactos, models.DO_NOTHING, db_column='usuario_id_contacto', blank=True, null=True)
    usuario_id_sexo = models.ForeignKey(Sexos, models.DO_NOTHING, db_column='usuario_id_sexo', blank=True, null=True)
    usuario_id_rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column='usuario_id_rol')
    usuario_id_estado = models.ForeignKey(Estadousuarios, models.DO_NOTHING, db_column='usuario_id_estado')
    activo = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'
