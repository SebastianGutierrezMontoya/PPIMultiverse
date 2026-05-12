"""
URL configuration for PPIMultiverse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from django.urls import path, include
from MultiverseAnimeStore.views import home_view, catalogo_view, login_view, logout_view, register_view, checkout_view, mis_pedidos_view, pedido_detalle_view

urlpatterns = [
    path('admindjango/', admin.site.urls),
    path('AdminMultiverse/', include('MultiverseAnimeStore.urls')),

    path('', home_view, name='home'),
    path('catalogo/', catalogo_view, name='catalogo'),

    path('checkout/', checkout_view, name='checkout'),

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

    path('mis-pedidos/', mis_pedidos_view, name='mis_pedidos'),
    path('mis-pedidos/<int:ped_id>/', pedido_detalle_view, name='pedido_detalle'),
]
