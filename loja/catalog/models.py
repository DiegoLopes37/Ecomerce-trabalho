from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Product(models.Model):
    name = models.CharField("nome", max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField("descrição", blank=True)
    price = models.DecimalField("preço", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("estoque", default=0)
    image = models.ImageField("imagem", upload_to="produtos/", blank=True)
    active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "produto"

    def __str__(self):
        return self.name

    IMAGE_SIZE = (800, 800)

    def _normalize_image(self):
        """Recorta ao centro e redimensiona para quadrado padrão (JPEG)."""
        from io import BytesIO
        from pathlib import Path

        from django.core.files.base import ContentFile
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(Image.open(self.image)).convert("RGB")
        img = ImageOps.fit(img, self.IMAGE_SIZE, Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, "JPEG", quality=88, optimize=True)
        name = Path(self.image.name).stem + ".jpg"
        self.image.save(name, ContentFile(buf.getvalue()), save=False)

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:  # imagem nova enviada
            self._normalize_image()
        if not self.slug:
            base = slugify(self.name) or "produto"
            slug, n = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:detail", args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0
