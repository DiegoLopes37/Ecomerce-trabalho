from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from catalog.models import Product

# (arquivo em seed/produtos, nome, descrição, preço provisório, estoque)
PRODUTOS = [
    ("roqueiro-guitarra", "Amigurumi Roqueiro com Guitarra", "Boneco de crochê roqueiro com chapéu de chifrinhos, gravata azul e guitarra vermelha. Feito à mão.", "89.90", 5),
    ("girassol-coraline", "Girassol Coraline em Buquê", "Girassol de crochê com carinha de boneca de botões, folha e embalagem de buquê com laço.", "49.90", 8),
    ("chapeu-seletor", "Chapéu Seletor de Crochê", "Chapéu de bruxo marrom em crochê, ótimo para decoração e colecionadores.", "39.90", 6),
    ("buque-plataforma-9-3-4", "Buquê Girassol Plataforma 9¾", "Flor de crochê vermelha e amarela inspirada na Plataforma 9¾, embalada em buquê.", "54.90", 6),
    ("baby-yoda", "Amigurumi Baby Yoda", "Mini amigurumi verde de orelhas grandes, perfeito para presentear.", "59.90", 10),
    ("chaveiro-guarda-vermelho", "Chaveiro Guarda Vermelho", "Chaveiro de crochê com macacão vermelho e máscara de triângulo.", "29.90", 15),
    ("girassol-ogro", "Girassol Ogro Verde", "Girassol de crochê com rosto de ogro verde, folhas e embalagem em tule.", "49.90", 7),
    ("monstrinho-um-olho", "Amigurumi Monstrinho de Um Olho", "Monstrinho verde de um olho só, macio e fofo, feito em fio felpudo.", "44.90", 9),
    ("buque-girassol", "Buquê de Girassol de Crochê", "Girassol amarelo de crochê com folhas, embalado em papel verde com laço dourado.", "49.90", 12),
    ("dupla-chapeu-palha-rena", "Dupla Chapéu de Palha e Rena", "Par de mini amigurumis: pirata de chapéu de palha e rena de chapéu rosa. Vendidos juntos.", "69.90", 6),
    ("jacare-coroa", "Amigurumi Jacaré com Coroa", "Jacaré verde de crochê com coroinha amarela e bochechas rosadas.", "47.90", 8),
    ("buque-capivara-tulipas", "Buquê Capivara com Tulipas", "Capivara de crochê abraçando um coração, com tulipas e folhas, em embalagem de buquê rosa.", "79.90", 4),
]


class Command(BaseCommand):
    help = "Cadastra os produtos iniciais com as imagens de seed/produtos (não duplica)."

    def handle(self, *args, **options):
        pasta = Path(settings.BASE_DIR) / "seed" / "produtos"
        criados = 0
        for arquivo, nome, descricao, preco, estoque in PRODUTOS:
            if Product.objects.filter(name=nome).exists():
                continue
            caminho = pasta / f"{arquivo}.jpeg"
            produto = Product(name=nome, description=descricao, price=Decimal(preco), stock=estoque, active=True)
            with open(caminho, "rb") as f:
                produto.image.save(f"{arquivo}.jpeg", File(f), save=False)
            produto.save()
            criados += 1
        self.stdout.write(self.style.SUCCESS(f"{criados} produto(s) criado(s)."))
