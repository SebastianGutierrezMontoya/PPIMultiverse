from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MultiverseAnimeStore', '0004_alter_pedidos_ped_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='productos_auditoria',
            name='model_name',
            field=models.CharField(default='Productos', max_length=100, verbose_name='Modelo'),
        ),
        migrations.AddField(
            model_name='productos_auditoria',
            name='object_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='ID del registro'),
        ),
        migrations.AlterField(
            model_name='productos_auditoria',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación'),
        ),
        migrations.AlterField(
            model_name='productos_auditoria',
            name='au_type',
            field=models.IntegerField(default=1, verbose_name='Tipo'),
        ),
        migrations.AlterField(
            model_name='productos_auditoria',
            name='auditoria',
            field=models.TextField(blank=True, null=True, verbose_name='Auditoría'),
        ),
    ]
