from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("conta/", include("accounts.urls")),
    path("carrinho/", include("cart.urls")),
    path("pedidos/", include("orders.urls")),
    path("painel/", include("painel.urls")),
    path("", include("catalog.urls")),
    # Imagens enviadas (servidas pela própria aplicação; em produção real use um servidor de arquivos/CDN)
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
