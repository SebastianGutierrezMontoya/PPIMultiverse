from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Categoria, Contactos, Estadopedidos, Estadousuarios, Pedidos, PedidosProductos, Productos, Roles, Usuarios

#Categorias
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'

class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categoria_detail.html'

class CategoriaCreateView(CreateView):
    model = Categoria
    fields = '__all__'
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    fields = '__all__'
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_list')

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')

#Contactos

class ContactosListView(ListView):
    model = Contactos
    template_name = 'contactos_list.html'

class ContactosDetailView(DetailView):
    model = Contactos
    template_name = 'contactos_detail.html'

class ContactosCreateView(CreateView):
    model = Contactos
    fields = '__all__'
    template_name = 'contactos_form.html'
    success_url = reverse_lazy('contactos_list')

class ContactosUpdateView(UpdateView):
    model = Contactos
    fields = '__all__'
    template_name = 'contactos_form.html'
    success_url = reverse_lazy('contactos_list')

class ContactosDeleteView(DeleteView):
    model = Contactos
    template_name = 'contactos_confirm_delete.html'
    success_url = reverse_lazy('contactos_list')
