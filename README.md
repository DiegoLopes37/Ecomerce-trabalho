# Ecomerce-trabalho

---

# EduPortal: correção das vulnerabilidades V1 a V5

Análise e solução das cinco primeiras falhas encontradas na auditoria. As correções foram aplicadas e testadas numa cópia do projeto, com o cliente de testes do Flask.

| # | Gravidade | Falha | Arquivo |
|---|---|---|---|
| V1 | Crítica | Injeção de SQL no login | `app.py` |
| V2 | Crítica | Chave de sessão fixa e fraca | `app.py` |
| V3 | Alta | XSS armazenado em comentários | `app.py` |
| V4 | Alta | Acesso ao boletim de outro aluno (IDOR) | `app.py` |
| V5 | Alta | Senhas em MD5 sem salt | `database.py`, `app.py` |

Os números de linha se referem ao código original. **V1 e V5 devem ser aplicadas juntas.**

---

## V1. Injeção de SQL no login

### Análise

Em `app.py:64-65`, o e-mail digitado é colado dentro do texto da consulta:

```python
consulta = f"SELECT * FROM usuarios WHERE email = '{email}' AND senha = '{hash_senha(senha)}'"
usuario = db.execute(consulta).fetchone()
```

Um apóstrofo no e-mail encerra a string SQL, e o restante passa a ser executado como comando.

**Reprodução (somente no ambiente local):** informe `admin@eduportal.com' -- ` como e-mail e qualquer senha. O `--` comenta a verificação da senha.

**Impacto:** acesso como qualquer usuário, inclusive administrador, sem conhecer a senha. Um apóstrofo comum (`o'brien@x.com`) também causa erro 500.

### Solução

Usar consulta parametrizada e conferir a senha no Python:

```python
email = request.form.get("email", "").strip().lower()
senha = request.form.get("senha", "")
db = conectar()
usuario = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
if usuario and verificar_senha(usuario["senha"], senha):
    if hash_antigo(usuario["senha"]):  # migra o MD5 (ver V5)
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (hash_senha(senha), usuario["id"]))
        db.commit()
    session.clear()
    session["usuario_id"] = usuario["id"]
    # o restante do bloco continua igual
```

O `.lower()` corrige ainda um erro à parte: quem digitava o e-mail com maiúsculas não conseguia entrar.

---

## V2. Chave de sessão fixa e fraca

### Análise

Em `app.py:9`:

```python
app.secret_key = "escola123"
```

O Flask guarda a sessão num cookie assinado com essa chave. Ela é curta, previsível e está no código-fonte.

**Impacto:** quem a conhece cria um cookie com `perfil: admin` e entra sem fazer login.

### Solução

Ler a chave do ambiente. A aplicação passa a não iniciar sem ela.

```python
import os

app.secret_key = os.environ["SECRET_KEY"]
```

Gere uma chave aleatória:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Defina a variável antes de rodar:

```bash
export SECRET_KEY="cole-a-chave-aqui"      # Linux/Mac
$env:SECRET_KEY="cole-a-chave-aqui"        # Windows PowerShell
set SECRET_KEY=cole-a-chave-aqui           # Windows CMD
python app.py
```

No `docker-compose.yml`, dentro do serviço `eduportal`:

```yaml
    environment:
      - SECRET_KEY=${SECRET_KEY:?defina a variavel SECRET_KEY}
```

Não grave a chave no repositório. Ao trocá-la, todas as sessões abertas são encerradas.

---

## V3. XSS armazenado

### Análise

Em `app.py:33-36`, o filtro marca o texto do usuário como HTML seguro:

```python
def formatar(texto):
    return Markup(texto.replace("\n", "<br>"))
```

Isso desliga o escape automático do Jinja. O filtro é usado nos comentários (`aviso.html:18`).

**Reprodução (local):** comente `<script>alert(1)</script>` em um aviso. O script é executado por quem abrir a página.

**Impacto:** como o cadastro é público, um estranho pode executar ações em nome do administrador que ler o comentário.

### Solução

Primeiro escapar o texto, depois inserir as quebras de linha:

```python
def formatar(texto):
    """Mantém as quebras de linha que o usuário digitou."""
    return escape(texto).replace("\n", Markup("<br>"))
```

Os avisos já eram escapados antes de gravar (`app.py:482`). Com o filtro corrigido, haveria escape duplo, então grave o texto original:

```python
(session["usuario_id"], titulo, conteudo))
```

### Migração dos avisos antigos

Se já existe um `eduportal.db`, faça uma cópia dele. Salve o script abaixo como `migrar_avisos.py` na pasta do projeto e execute **uma única vez**, com a aplicação parada e antes de publicar novos avisos:

```python
import html
import sqlite3

db = sqlite3.connect("eduportal.db")
for aviso_id, conteudo in db.execute("SELECT id, conteudo FROM avisos").fetchall():
    db.execute("UPDATE avisos SET conteudo = ? WHERE id = ?", (html.unescape(conteudo), aviso_id))
db.commit()
db.close()
```

---

## V4. Acesso ao boletim de outro aluno (IDOR)

### Análise

A rota `/boletim/<aluno_id>` (`app.py:427-445`) exige login, mas não confere de quem é o boletim.

**Reprodução (local):** entre como `ana@eduportal.com` e abra `/boletim/5`. Aparecem as notas e o e-mail de Bruno.

**Impacto:** qualquer aluno pode ver os dados de todos, trocando o número no endereço.

### Solução

Verificar a permissão antes de consultar o banco:

```python
def boletim(aluno_id):
    if session["perfil"] not in ("professor", "admin") and aluno_id != session["usuario_id"]:
        abort(403)
    db = conectar()
    # o restante continua igual
```

Assim, o aluno vê apenas o próprio boletim, e um ID inexistente também retorna 403. Professores continuam vendo todos. Se cada professor só deve ver suas turmas, essa regra precisa ser acrescentada.

---

## V5. Senhas em MD5 sem salt

### Análise

Em `database.py:84-85`:

```python
def hash_senha(senha):
    return hashlib.md5(senha.encode()).hexdigest()
```

O MD5 é muito rápido e, sem salt, senhas iguais geram hashes iguais.

**Impacto:** se o banco vazar (ou for lido por injeção de SQL), senhas fracas são descobertas em pouco tempo.

### Solução

Usar as funções do Werkzeug, que já vem com o Flask. Em `database.py`:

```python
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash


def hash_senha(senha):
    return generate_password_hash(senha)


def hash_antigo(guardado):
    """Diz se o valor guardado ainda é um MD5 (32 dígitos hexadecimais)."""
    return re.fullmatch(r"[0-9a-f]{32}", guardado) is not None


def verificar_senha(guardado, senha):
    if hash_antigo(guardado):  # só durante a migração
        return hmac.compare_digest(guardado, hashlib.md5(senha.encode()).hexdigest())
    return check_password_hash(guardado, senha)
```

No `SCHEMA`, altere `senha VARCHAR(64)` para `senha VARCHAR(255)`. O SQLite não impõe esse limite, então o banco existente não precisa ser recriado.

Em `app.py`, atualize a importação:

```python
from database import conectar, criar_banco, fechar, hash_antigo, hash_senha, verificar_senha
```

Na troca de senha do perfil (`app.py:149`), não compare hashes com `!=`, pois cada hash novo é diferente:

```python
elif nova and not verificar_senha(usuario["senha"], atual):
```

O login atualizado está em V1. Cada conta antiga é convertida no primeiro login correto. Contas que não entrarem continuam em MD5: redefina essas senhas e depois remova o suporte ao formato antigo.

Se o seu Python não tiver suporte a `scrypt` (erro ao gerar o hash), use `generate_password_hash(senha, method="pbkdf2")`.

---

## Como conferir

| Teste | Resultado esperado |
|---|---|
| Login com `admin@eduportal.com' -- ` | "E-mail ou senha incorretos" |
| Cookie assinado com `escola123` | Redireciona para o login |
| Comentário com `<script>` | Aparece como texto |
| Aluno abre o boletim de outro | Erro 403 |
| Coluna `senha` após o login | Começa com `scrypt:` ou `pbkdf2:` |
