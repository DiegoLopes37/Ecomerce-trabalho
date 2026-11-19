# Loja Virtual de Produtos Artesanais — Crochê da Isa

Autores: Diego e Diogo

Loja virtual em **Python/Django** com **MySQL**, executada via **Docker Compose**.

## Pré-requisitos
- Docker e Docker Compose

## Instalação e execução

```bash
cd loja
cp .env.example .env        # Windows (PowerShell): Copy-Item .env.example .env
docker compose up --build
```

Acesse **http://localhost:8000**.

Na primeira execução o container aplica as migrações e cria o administrador definido no `.env`
(padrão: usuário `admin`, senha `admin12345` — **altere antes de usar em produção**).

- Loja: http://localhost:8000
- Painel do administrador: http://localhost:8000/painel/ (usuários com `is_staff`)
- Django Admin (opcional): http://localhost:8000/django-admin/

### Comandos úteis
```bash
docker compose down            # para os containers (dados do MySQL são mantidos)
docker compose down -v         # para e APAGA os dados (volumes)
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

## Persistência (RNF11)
O banco usa o volume `mysql_data` e as imagens enviadas ficam no volume `media_data`; ambos sobrevivem à reinicialização dos containers.

## HTTPS em produção (RNF10)
Coloque a aplicação atrás de um proxy reverso com certificado TLS (Nginx, Caddy, Traefik...) que envie `X-Forwarded-Proto: https` e, no `.env`:
```
DJANGO_DEBUG=False
USE_HTTPS=True
DJANGO_ALLOWED_HOSTS=seudominio.com.br
CSRF_TRUSTED_ORIGINS=https://seudominio.com.br
DJANGO_SECRET_KEY=<chave longa e aleatória>
```
Isso ativa redirecionamento para HTTPS, cookies seguros e HSTS.

## Estrutura (RNF12)
| App | Responsabilidade |
|---|---|
| `accounts` | cadastro, login e logout |
| `catalog` | produtos, página inicial, listagem e detalhes |
| `cart` | carrinho (sessão): adicionar, alterar, remover, total |
| `orders` | checkout, pedidos, histórico, baixa de estoque |
| `painel` | área administrativa (produtos e pedidos) |

## Rastreabilidade dos requisitos
| Requisito | Onde |
|---|---|
| RF01–RF03 | `catalog` (`/`, `/produtos/`, `/produtos/<slug>/`) |
| RF04–RF06 | `accounts` (`/conta/cadastro/`, `/conta/login/`, `/conta/sair/`) |
| RF07–RF10 | `cart` (`/carrinho/`) |
| RF11–RF13 | `orders` (`/pedidos/finalizar/`, `/pedidos/`) |
| RF14–RF17 | `painel` (`/painel/produtos/`, `/painel/pedidos/`) |
| RF18 | baixa de estoque em `orders.views.create_order` (com `select_for_update`); devolução ao cancelar em `Order.change_status` |
| RNF06 | hash PBKDF2 do Django |
| RNF07/RNF09 | `login_required` + `staff_required` (403 para usuários comuns) |
| RNF08 | validação em formulários Django (`forms.py`) |
| RNF13 | framework de mensagens do Django |

## Testes
```bash
docker compose exec web python manage.py test
```
