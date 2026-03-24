# Como obter o token da Meta Ad Library API

## O que é esse token?

Diferente do token da sua conta de anúncios (`META_ACCESS_TOKEN`), a **Ad Library API**
usa um **App Access Token** que não expira e dá acesso público à biblioteca de anúncios.

Formato: `SEU_APP_ID|SEU_APP_SECRET`

---

## Passo a Passo

### 1. Criar uma conta de desenvolvedor Meta

Acesse: https://developers.facebook.com
Faça login com sua conta do Facebook e confirme o cadastro como desenvolvedor.

---

### 2. Criar um App

1. Clique em **"Meus Apps"** > **"Criar App"**
2. Escolha o tipo: **"Outro"** (ou "Nenhum")
3. Em seguida, selecione **"Negócio"** como tipo de app
4. Preencha:
   - **Nome do app**: `AdLibraryAgent` (qualquer nome)
   - **E-mail de contato**: seu e-mail
5. Clique em **"Criar App"**

---

### 3. Pegar o App ID e o App Secret

1. No painel do app, clique em **"Configurações"** > **"Básico"** (menu lateral)
2. Anote o **ID do Aplicativo** (App ID)
3. Clique em **"Mostrar"** ao lado de **"Chave Secreta do Aplicativo"** e anote o valor

---

### 4. Habilitar acesso à Ad Library API

1. No menu lateral, clique em **"Produtos"** > clique em **"+"**
2. Procure por **"Marketing API"** e clique em **"Configurar"**
3. Isso habilita as permissões necessárias para a Ad Library

> A Ad Library API para anúncios não-políticos (como o nicho dental) **não exige revisão**
> da Meta — o App Access Token já funciona imediatamente.

---

### 5. Montar o token

O App Access Token tem o formato:

```
APP_ID|APP_SECRET
```

Exemplo:
```
1234567890|abcdef1234567890abcdef1234567890
```

---

### 6. Adicionar ao arquivo .env

Abra (ou crie) o arquivo `.env` na raiz do projeto e adicione:

```env
META_ACCESS_TOKEN=seu_token_da_conta_de_anuncios
META_ACCOUNT_ID=seu_account_id
META_AD_LIBRARY_TOKEN=SEU_APP_ID|SEU_APP_SECRET
```

---

## Testando o token

Execute no terminal:

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('META_AD_LIBRARY_TOKEN')
r = requests.get('https://graph.facebook.com/v21.0/ads_archive', params={
    'access_token': token,
    'search_terms': 'implante dental',
    'ad_reached_countries': '[\"BR\"]',
    'ad_type': 'ALL',
    'fields': 'id,page_name',
    'limit': 3
})
print(r.json())
"
```

Se retornar uma lista com `id` e `page_name`, o token está funcionando.

---

## Executando o agente

```bash
# Busca com todos os termos do nicho dental (padrão)
python ad_library_agent.py

# Busca com termo específico, 100 anúncios por termo
python ad_library_agent.py --termo "implante dental" --limite 100

# Múltiplos termos customizados
python ad_library_agent.py --termo "aparelho dental" "orthodontist" --paises BR US

# Sem exportar arquivos (só exibe no terminal)
python ad_library_agent.py --sem-export
```

---

## Entendendo o Score

| Coluna | O que significa |
|--------|----------------|
| `dias_no_ar` | Dias desde que o anúncio foi publicado até hoje (ou até encerrar) |
| `impressoes_est` | Estimativa de impressões fornecida pelo Meta (ponto médio do intervalo) |
| `score` | Score combinado: `log(dias+1)*10 + log(impressoes+1)*5` — quanto maior, melhor |
| `status` | ATIVO = ainda rodando / ENCERRADO = foi pausado/finalizado |
| `link_criativo` | URL para ver o anúncio completo na Biblioteca de Anúncios do Meta |

**Dica:** Priorize anúncios com status **ATIVO** e alto `score` — são os que estão
gerando resultado agora (anunciante continua investindo).
