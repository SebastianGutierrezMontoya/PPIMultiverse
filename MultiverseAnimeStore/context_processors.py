from MultiverseAnimeStore.models import Configuracion


def guest_checkout(request):
    try:
        config = Configuracion.objects.get(clave='guest_checkout')
        return {'guest_checkout_enabled': config.valor != '0'}
    except Configuracion.DoesNotExist:
        return {'guest_checkout_enabled': True}
