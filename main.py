"""
Exemplos de uso do MetaAdsClient.
Execute: python main.py
"""
from meta_ads import MetaAdsClient

client = MetaAdsClient()

# ─────────────────────────────────────────
# 1. Resumo da conta
# ─────────────────────────────────────────
client.resumo_conta()

# ─────────────────────────────────────────
# 2. Listar campanhas ativas
# ─────────────────────────────────────────
campanhas = client.listar_campanhas(status=["ACTIVE", "PAUSED"])
print(campanhas[["id", "name", "status", "objective"]].to_string())

# ─────────────────────────────────────────
# 3. Relatório dos últimos 30 dias (por campanha)
# ─────────────────────────────────────────
df_insights = client.obter_insights(nivel="campaign", periodo="last_30d")
client.exportar_relatorio(df_insights, "relatorio_campanhas.xlsx")

# ─────────────────────────────────────────
# 4. Relatório por período específico (por anúncio)
# ─────────────────────────────────────────
# df = client.obter_insights(
#     nivel="ad",
#     data_inicio="2024-01-01",
#     data_fim="2024-01-31"
# )
# client.exportar_relatorio(df, "janeiro_por_anuncio.csv", formato="csv")

# ─────────────────────────────────────────
# 5. Criar campanha (descomente para usar)
# ─────────────────────────────────────────
# nova_campanha = client.criar_campanha(
#     nome="Minha Campanha de Tráfego",
#     objetivo="OUTCOME_TRAFFIC",
#     status="PAUSED",
#     orcamento_diario=50.00,  # R$ 50/dia
# )

# ─────────────────────────────────────────
# 6. Criar conjunto de anúncios
# ─────────────────────────────────────────
# conjunto = client.criar_conjunto(
#     campanha_id=nova_campanha["id"],
#     nome="Conjunto Brasil 18-45",
#     orcamento_diario=50.00,
#     data_inicio="2024-02-01",
#     pais="BR",
#     idade_min=18,
#     idade_max=45,
# )

# ─────────────────────────────────────────
# 7. Criar criativo e anúncio
# ─────────────────────────────────────────
# criativo = client.criar_criativo(
#     nome="Criativo Principal",
#     pagina_id="SUA_PAGE_ID",
#     mensagem="Confira nossa oferta especial!",
#     link="https://seusite.com.br",
#     titulo="Oferta Imperdível",
#     descricao="Clique e saiba mais",
#     imagem_url="https://seusite.com.br/imagem.jpg",
# )

# anuncio = client.criar_anuncio(
#     conjunto_id=conjunto["id"],
#     nome="Anúncio Principal",
#     criativo_id=criativo["id"],
# )
