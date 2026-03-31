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
    cons_id = models.IntegerField(primary_key=True)
    cons_nombre = models.CharField(unique=True, max_length=50, blank=False, null=False)
    cons_sql = models.CharField(max_length=4000, blank=False, null=False)
    cons_descripcion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'consultas_dinamicas'

    def __str__(self):
        return self.cons_nombre or str(self.cons_id)

class Categoria(models.Model):
    cat_id = models.CharField(primary_key=True, max_length=10)
    cat_nombre = models.CharField(unique=True, max_length=50, blank=True, null=True)
    cat_descripcion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'categoria'
        app_label = 'MultiverseAnimeStore'

    def __str__(self):
        return self.cat_nombre or str(self.cat_id)



class EstadoPedidos(models.Model):
    est_id = models.IntegerField(primary_key=True)
    est_nombre = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estadopedidos'

    def __str__(self):
        return self.est_nombre or str(self.id_estado)

class Pedidos(models.Model):
    ped_id = models.IntegerField(primary_key=True)
    usu = models.ForeignKey('Usuarios', models.DO_NOTHING)
    ped_fecha_pedido = models.DateField(blank=True, null=True)
    ped_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    # ped_estado = models.IntegerField(max_length=1, blank=True, null=True, default=1)
    #ped_estado = models.ForeignKey(EstadoPedidos, models.DO_NOTHING, blank=True, null=True, db_column='ped_estado')
    ped_estado = models.FloatField(max_length=1, blank=True, null=True, default=1)
    ped_direccion_envio = models.CharField(max_length=200, blank=True, null=True)
    ped_notas = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pedidos'

    def __str__(self):
        return f"Pedido {self.ped_id}"


class PedidosProductos(models.Model):
    pk = models.CompositePrimaryKey('ped_id', 'prod_id')
    ped = models.ForeignKey(Pedidos, models.DO_NOTHING)
    prod = models.ForeignKey('Productos', models.DO_NOTHING)
    pped_fecha_entrega = models.DateField(blank=True, null=True)
    pped_cantidad = models.IntegerField(blank=True, null=True)
    pped_precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pped_descuento = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=False, default=0)
    pped_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=False)
    pped_estado = models.ForeignKey(EstadoPedidos, models.DO_NOTHING, blank=True, null=True, db_column='pped_estado')

    class Meta:
        managed = False
        db_table = 'pedidos_productos'


class Perfiles(models.Model):
    id_perfil = models.IntegerField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100, blank=True, null=True)
    rol_id = models.ForeignKey('Roles', models.DO_NOTHING, blank=True, null=True, db_column='rol_id')
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'perfiles'

    def __str__(self):
        return self.nombre or str(self.id_perfil)


class Modulos(models.Model):
    id_mod = models.AutoField(primary_key=True)
    nombre_mod = models.CharField(unique=True, max_length=100, blank=True, null=False)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    url_mod = models.CharField(max_length=200, blank=True, null=False)
    padre_mod = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'modulos'

    def __str__(self):
        return self.nombre_mod or str(self.id_mod)

class Perfilpermisos(models.Model):
    id_perfil_permiso = models.IntegerField(primary_key=True)
    perfil_id = models.ForeignKey(Perfiles, models.DO_NOTHING)
    mod_id = models.ForeignKey('Modulos', models.DO_NOTHING)

    can_create = models.CharField(max_length=1, blank=True, null=True, default='N')
    can_read = models.CharField(max_length=1, blank=True, null=True, default='Y')
    can_update = models.CharField(max_length=1, blank=True, null=True, default='N')
    can_delete = models.CharField(max_length=1, blank=True, null=True, default='N')

    class Meta:
        managed = False
        db_table = 'perfilpermisos'


class Productos(models.Model):
    prod_id = models.CharField(primary_key=True, max_length=10)
    cat = models.ForeignKey(Categoria, models.DO_NOTHING)
    prod_nombre = models.CharField(max_length=100, blank=True, null=True)
    prod_descripcion = models.CharField(max_length=400, blank=True, null=True)
    prod_precio_venta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    prod_stock = models.IntegerField(blank=True, null=True)
    prod_imagen_url = models.CharField(max_length=500, blank=True, null=True)
    prod_descuento = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, default=0)

    class Meta:
        managed = False
        db_table = 'productos'

    def __str__(self):
        return self.prod_nombre or str(self.prod_id)


class Productos_Auditoria(models.Model):
    dummy_id = models.AutoField(primary_key=True),
    creation_date = models.DateField(blank=True, null=True)
    au_type = models.IntegerField(blank=True, null=True)
    auditoria = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productos_auditoria'


class Roles(models.Model):
    id_rol = models.IntegerField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.nombre or str(self.id_rol)



class Sexos(models.Model):
    id_sexo = models.IntegerField(primary_key=True)
    nombre_sexo = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sexos'

    def __str__(self):
        return self.nombre_sexo or str(self.id_sexo)


class Usuarios(models.Model):
    id_usuario = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=300, blank=True, null=True)
    primer_apellido = models.CharField(max_length=50, blank=True, null=True)
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    usuario_id_sexo = models.ForeignKey(Sexos, models.DO_NOTHING, db_column='usuario_id_sexo')
    usuario_id_perfil = models.ForeignKey(Perfiles, models.DO_NOTHING, db_column='usuario_id_perfil')
    activo = models.FloatField(max_length=1, blank=True, null=True, default=1)

    class Meta:
        managed = False
        db_table = 'usuarios'
        # fields = ['id_usuario', 'nombre', 'primer_apellido', 'segundo_apellido', 'fecha_nacimiento',
        #            'password_hash', 'usuario_id_sexo', 'usuario_id_rol']
        

    def __str__(self):
        
        return self.nombre or str(self.id_usuario)
    


class Config_Contacto(models.Model):
    id_regla = models.IntegerField(primary_key=True, )
    nombre_contacto = models.CharField(max_length=50, blank=True, null=False)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    regex_val = models.CharField(max_length=200, blank=True, null=True)
    min_length = models.FloatField(blank=True, null=True)
    max_length = models.FloatField(blank=True, null=True)
    mensaje_error = models.CharField(max_length=200, blank=True, null=False)

    class Meta:
        managed = False
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
    id_contacto = models.IntegerField(primary_key=True, )
    tipo_contacto = models.ForeignKey(Config_Contacto, models.DO_NOTHING, db_column='tipo_contacto', blank=True, null=True)
    dato_contacto = models.CharField(max_length=100, blank=True, null=True)
    id_usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contactos'

    def __str__(self):
        return self.dato_contacto or str(self.id_contacto)
