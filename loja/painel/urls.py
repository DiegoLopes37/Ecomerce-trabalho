from django.urls import path

from . import views

app_name = "painel"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("produtos/", views.product_list, name="products"),
    path("produtos/novo/", views.product_create, name="product_create"),
    path("produtos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path("produtos/<int:pk>/excluir/", views.product_delete, name="product_delete"),
    path("pedidos/", views.order_list, name="orders"),
    path("pedidos/<int:pk>/", views.order_detail, name="order_detail"),
]
