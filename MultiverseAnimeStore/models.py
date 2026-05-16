# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models import Max




class Consultas_Dinamicas(models.Model):
    cons_id = models.IntegerField(primary_key=True, verbose_name="ID")
    cons_nombre = models.CharField(unique=True, max_length=50, blank=False, null=False, verbose_name="Nombre")
    cons_sql = models.CharField(max_length=4000, blank=False, null=False, verbose_name="Consulta SQL")
    cons_descripcion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción")

    class Meta:
        managed = True
        db_table = 'consultas_dinamicas'

    def __str__(self):
        return self.cons_nombre or str(self.cons_id)

class Categoria(models.Model):
    cat_id = models.CharField(primary_key=True, max_length=10, verbose_name="ID")
    cat_nombre = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="Nombre")
    cat_descripcion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción")

    class Meta:
        managed = True
        db_table = 'categoria'
        app_label = 'MultiverseAnimeStore'

    def __str__(self):
        return self.cat_nombre or str(self.cat_id)



class EstadoPedidos(models.Model):
    est_id = models.IntegerField(primary_key=True, verbose_name="ID")
    est_nombre = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nombre")

    class Meta:
        managed = True
        db_table = 'estadopedidos'

    def __str__(self):
        return self.est_nombre or str(self.id_estado)

class Pedidos(models.Model):
    ped_id = models.IntegerField(primary_key=True, verbose_name="ID")
    usu = models.ForeignKey('Usuarios', models.DO_NOTHING, verbose_name="Usuario")
    ped_fecha_pedido = models.DateField(blank=True, null=True, verbose_name="Fecha de pedido")
    ped_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0, verbose_name="Total")
    ped_estado = models.ForeignKey(
        EstadoPedidos, models.DO_NOTHING,
        db_column='ped_estado', default=1,
        related_name='pedidos', verbose_name="Estado"
    )
    ped_direccion_envio = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dirección de envío")
    ped_notas = models.CharField(max_length=200, blank=True, null=True, verbose_name="Notas")

    class Meta:
        managed = True
        db_table = 'pedidos'
        constraints = [
            models.CheckConstraint(check=models.Q(ped_total__gte=0), name='ck_total_no_negativo'),
        ]

    def __str__(self):
        return f"Pedido {self.ped_id}"


class PedidosProductos(models.Model):
    pk = models.CompositePrimaryKey('ped_id', 'prod_id')
    ped = models.ForeignKey(Pedidos, models.DO_NOTHING, verbose_name="Pedido")
    prod = models.ForeignKey('Productos', models.DO_NOTHING, verbose_name="Producto")
    pped_fecha_entrega = models.DateField(blank=True, null=True, verbose_name="Fecha de entrega")
    pped_cantidad = models.IntegerField(blank=True, null=True, verbose_name="Cantidad")
    pped_precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Precio unitario")
    pped_descuento = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=False, default=0, verbose_name="Descuento")
    pped_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=False, verbose_name="Total")
    pped_estado = models.ForeignKey(EstadoPedidos, models.DO_NOTHING, blank=True, null=True, db_column='pped_estado', verbose_name="Estado")

    class Meta:
        managed = True
        db_table = 'pedidos_productos'


class Perfiles(models.Model):
    id_perfil = models.IntegerField(primary_key=True, verbose_name="ID")
    nombre = models.CharField(unique=True, max_length=100, blank=True, null=True, verbose_name="Nombre")
    rol_id = models.ForeignKey('Roles', models.DO_NOTHING, blank=True, null=True, db_column='rol_id', verbose_name="Rol")
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")

    class Meta:
        managed = True
        db_table = 'perfiles'

    def __str__(self):
        return self.nombre or str(self.id_perfil)


class Modulos(models.Model):
    id_mod = models.AutoField(primary_key=True, verbose_name="ID")
    nombre_mod = models.CharField(unique=True, max_length=100, blank=True, null=False, verbose_name="Nombre")
    descripcion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción")
    url_mod = models.CharField(max_length=200, blank=True, null=False, verbose_name="URL")
    padre_mod = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, db_column='padre_mod', verbose_name="Módulo padre")


    class Meta:
        managed = True
        db_table = 'modulos'

    def __str__(self):
        return self.nombre_mod or str(self.id_mod)

class Perfilpermisos(models.Model):
    pk = models.CompositePrimaryKey('perfil_id', 'mod_id')
    perfil_id = models.ForeignKey(Perfiles, models.DO_NOTHING, db_column='perfil_id', verbose_name="Perfil")
    mod_id = models.ForeignKey('Modulos', models.DO_NOTHING, db_column='mod_id', verbose_name="Módulo")

    can_create = models.CharField(max_length=1, blank=True, null=True, default='N', verbose_name="Crear")
    can_read = models.CharField(max_length=1, blank=True, null=True, default='Y', verbose_name="Leer")
    can_update = models.CharField(max_length=1, blank=True, null=True, default='N', verbose_name="Actualizar")
    can_delete = models.CharField(max_length=1, blank=True, null=True, default='N', verbose_name="Eliminar")

    class Meta:
        managed = True
        db_table = 'perfilpermisos'


class Productos(models.Model):
    prod_id = models.CharField(primary_key=True, max_length=10, verbose_name="ID")
    cat = models.ForeignKey(Categoria, models.DO_NOTHING, verbose_name="Categoría")
    prod_nombre = models.CharField(max_length=100, blank=False, null=False, default='Sin nombre', verbose_name="Nombre")
    prod_descripcion = models.CharField(max_length=400, blank=True, null=True, verbose_name="Descripción")
    prod_precio_venta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Precio de venta")
    prod_stock = models.IntegerField(blank=True, null=True, verbose_name="Stock")
    prod_imagen_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="URL de imagen")
    prod_descuento = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, default=0, verbose_name="Descuento")

    class Meta:
        managed = True
        db_table = 'productos'
        constraints = [
            models.CheckConstraint(check=models.Q(prod_precio_venta__gt=0), name='ck_precio_positivo'),
            models.CheckConstraint(check=models.Q(prod_stock__gte=0), name='ck_stock_no_negativo'),
            models.CheckConstraint(check=models.Q(prod_descuento__lte=99), name='ck_descuento_maximo'),
        ]

    def __str__(self):
        return self.prod_nombre or str(self.prod_id)


class Productos_Auditoria(models.Model):
    dummy_id = models.AutoField(primary_key=True, verbose_name="ID")
    creation_date = models.DateField(blank=True, null=True, verbose_name="Fecha de creación")
    au_type = models.IntegerField(blank=True, null=True, verbose_name="Tipo")
    auditoria = models.CharField(max_length=500, blank=True, null=True, verbose_name="Auditoría")

    class Meta:
        managed = True
        db_table = 'productos_auditoria'


class Roles(models.Model):
    id_rol = models.IntegerField(primary_key=True, verbose_name="ID")
    nombre = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="Nombre")
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")

    class Meta:
        managed = True
        db_table = 'roles'

    def __str__(self):
        return self.nombre or str(self.id_rol)



class Sexos(models.Model):
    id_sexo = models.IntegerField(primary_key=True, verbose_name="ID")
    nombre_sexo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Nombre")

    class Meta:
        managed = True
        db_table = 'sexos'

    def __str__(self):
        return self.nombre_sexo or str(self.id_sexo)


class Usuarios(models.Model):
    id_usuario = models.CharField(max_length=50, primary_key=True, verbose_name="ID")
    nombre = models.CharField(max_length=300, blank=True, null=True, verbose_name="Nombre")
    primer_apellido = models.CharField(max_length=50, blank=True, null=True, verbose_name="Primer apellido")
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True, verbose_name="Segundo apellido")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    password_hash = models.CharField(max_length=255, blank=True, null=True, verbose_name="Contraseña")
    usuario_id_sexo = models.ForeignKey(Sexos, models.DO_NOTHING, db_column='usuario_id_sexo', verbose_name="Sexo")
    usuario_id_perfil = models.ForeignKey(Perfiles, models.DO_NOTHING, db_column='usuario_id_perfil', verbose_name="Perfil")
    activo = models.FloatField(max_length=1, blank=True, null=True, default=1, verbose_name="Activo")

    class Meta:
        managed = True
        db_table = 'usuarios'
        constraints = [
            models.CheckConstraint(check=models.Q(activo=0) | models.Q(activo=1), name='ck_activo_valido'),
        ]

    def __str__(self):
        
        return self.nombre or str(self.id_usuario)
    


class Config_Contacto(models.Model):
    id_regla = models.IntegerField(primary_key=True, verbose_name="ID")
    nombre_contacto = models.CharField(max_length=50, blank=True, null=False, verbose_name="Nombre")
    descripcion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descripción")
    regex_val = models.CharField(max_length=200, blank=True, null=True, verbose_name="Regex")
    min_length = models.FloatField(blank=True, null=True, verbose_name="Longitud mínima")
    max_length = models.FloatField(blank=True, null=True, verbose_name="Longitud máxima")
    mensaje_error = models.CharField(max_length=200, blank=True, null=False, verbose_name="Mensaje de error")

    class Meta:
        managed = True
        db_table = 'config_contacto'

    def __str__(self):
        return self.nombre_contacto or str(self.id_regla)

    @classmethod
    def next_id(cls):
        """
        Devuelve max(id_regla) + 1 (maneja valores nulos).
        Útil para prellenar formularios con la próxima id disponible.
        """
        maxv = cls.objects.aggregate(maxv=Max('id_regla'))['maxv']
        if maxv is None:
            return 1
        try:
            return int(maxv) + 1
        except Exception:
            try:
                return int(float(maxv)) + 1
            except Exception:
                return 1

class Contactos(models.Model):
    id_contacto = models.IntegerField(primary_key=True, verbose_name="ID")
    tipo_contacto = models.ForeignKey(Config_Contacto, models.DO_NOTHING, db_column='tipo_contacto', blank=True, null=True, verbose_name="Tipo de contacto")
    dato_contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dato")
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True, verbose_name="Usuario")

    class Meta:
        managed = True
        db_table = 'contactos'
        constraints = [
            models.UniqueConstraint(fields=['id_usuario', 'tipo_contacto'], name='uq_usuario_tipo_contacto'),
        ]

    def __str__(self):
        return self.dato_contacto or str(self.id_contacto)
