from .models import Usuarios

class AnonymousUser:
    is_authenticated = False
    is_anonymous = True

class CustomAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')

        if user_id:
            try:
                user = Usuarios.objects.get(id_usuario=user_id)

                # Inyectar atributos mínimos
                user.is_authenticated = True
                user.is_anonymous = False

                request.user = user

            except Usuarios.DoesNotExist:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()

        return self.get_response(request)