import os
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adsinsights import AdsInsights

load_dotenv()


class MetaAdsClient:
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.account_id = os.getenv("META_ACCOUNT_ID")

        if not self.access_token or not self.account_id:
            raise ValueError("META_ACCESS_TOKEN e META_ACCOUNT_ID devem estar definidos no .env")

        FacebookAdsApi.init(access_token=self.access_token)
        self.account = AdAccount(f"act_{self.account_id}")
        print(f"Conectado à conta: act_{self.account_id}")

    # ─────────────────────────────────────────
    # CAMPANHAS
    # ─────────────────────────────────────────

    def listar_campanhas(self, status=None):
        """Retorna todas as campanhas da conta."""
        fields = [
            Campaign.Field.id,
            Campaign.Field.name,
            Campaign.Field.status,
            Campaign.Field.objective,
            Campaign.Field.created_time,
            Campaign.Field.start_time,
            Campaign.Field.stop_time,
            Campaign.Field.daily_budget,
            Campaign.Field.lifetime_budget,
        ]
        params = {}
        if status:
            params["effective_status"] = status  # ex: ['ACTIVE', 'PAUSED']

        campanhas = self.account.get_campaigns(fields=fields, params=params)
        dados = [dict(c) for c in campanhas]
        df = pd.DataFrame(dados)
        print(f"{len(df)} campanha(s) encontrada(s).")
        return df

    def criar_campanha(self, nome, objetivo, status="PAUSED", orcamento_diario=None):
        """
        Cria uma nova campanha.

        Objetivos comuns:
          OUTCOME_TRAFFIC, OUTCOME_LEADS, OUTCOME_SALES,
          OUTCOME_AWARENESS, OUTCOME_ENGAGEMENT, OUTCOME_APP_PROMOTION
        """
        params = {
            Campaign.Field.name: nome,
            Campaign.Field.objective: objetivo,
            Campaign.Field.status: status,
            Campaign.Field.special_ad_categories: [],
        }
        if orcamento_diario:
            params[Campaign.Field.daily_budget] = int(orcamento_diario * 100)  # em centavos

        campanha = self.account.create_campaign(fields=[], params=params)
        print(f"Campanha criada: {campanha['id']} — {nome}")
        return campanha

    # ─────────────────────────────────────────
    # CONJUNTOS DE ANÚNCIOS (Ad Sets)
    # ─────────────────────────────────────────

    def listar_conjuntos(self, campanha_id=None):
        """Lista conjuntos de anúncios, opcionalmente filtrados por campanha."""
        fields = [
            AdSet.Field.id,
            AdSet.Field.name,
            AdSet.Field.status,
            AdSet.Field.campaign_id,
            AdSet.Field.daily_budget,
            AdSet.Field.start_time,
            AdSet.Field.end_time,
            AdSet.Field.targeting,
        ]
        params = {}
        if campanha_id:
            params["campaign_id"] = campanha_id

        conjuntos = self.account.get_ad_sets(fields=fields, params=params)
        dados = [dict(c) for c in conjuntos]
        return pd.DataFrame(dados)

    def criar_conjunto(
        self,
        campanha_id,
        nome,
        orcamento_diario,
        data_inicio,
        otimizacao="LINK_CLICKS",
        cobranca="IMPRESSIONS",
        pais="BR",
        idade_min=18,
        idade_max=65,
        status="PAUSED",
    ):
        """Cria um conjunto de anúncios dentro de uma campanha."""
        targeting = {
            "geo_locations": {"countries": [pais]},
            "age_min": idade_min,
            "age_max": idade_max,
        }
        params = {
            AdSet.Field.name: nome,
            AdSet.Field.campaign_id: campanha_id,
            AdSet.Field.daily_budget: int(orcamento_diario * 100),
            AdSet.Field.start_time: data_inicio,
            AdSet.Field.optimization_goal: otimizacao,
            AdSet.Field.billing_event: cobranca,
            AdSet.Field.targeting: targeting,
            AdSet.Field.status: status,
        }
        conjunto = self.account.create_ad_set(fields=[], params=params)
        print(f"Conjunto criado: {conjunto['id']} — {nome}")
        return conjunto

    # ─────────────────────────────────────────
    # ANÚNCIOS
    # ─────────────────────────────────────────

    def listar_anuncios(self, conjunto_id=None):
        """Lista anúncios, opcionalmente filtrados por conjunto."""
        fields = [
            Ad.Field.id,
            Ad.Field.name,
            Ad.Field.status,
            Ad.Field.adset_id,
            Ad.Field.campaign_id,
            Ad.Field.creative,
            Ad.Field.created_time,
        ]
        params = {}
        if conjunto_id:
            params["adset_id"] = conjunto_id

        anuncios = self.account.get_ads(fields=fields, params=params)
        dados = [dict(a) for a in anuncios]
        return pd.DataFrame(dados)

    def criar_anuncio(self, conjunto_id, nome, criativo_id, status="PAUSED"):
        """Cria um anúncio dentro de um conjunto de anúncios."""
        params = {
            Ad.Field.name: nome,
            Ad.Field.adset_id: conjunto_id,
            Ad.Field.creative: {"creative_id": criativo_id},
            Ad.Field.status: status,
        }
        anuncio = self.account.create_ad(fields=[], params=params)
        print(f"Anúncio criado: {anuncio['id']} — {nome}")
        return anuncio

    def criar_criativo(self, nome, pagina_id, mensagem, link, titulo, descricao, imagem_url):
        """Cria um criativo de anúncio (necessário antes de criar o anúncio)."""
        params = {
            AdCreative.Field.name: nome,
            AdCreative.Field.object_story_spec: {
                "page_id": pagina_id,
                "link_data": {
                    "message": mensagem,
                    "link": link,
                    "name": titulo,
                    "description": descricao,
                    "picture": imagem_url,
                },
            },
        }
        criativo = self.account.create_ad_creative(fields=[], params=params)
        print(f"Criativo criado: {criativo['id']} — {nome}")
        return criativo

    # ─────────────────────────────────────────
    # RELATÓRIOS / INSIGHTS
    # ─────────────────────────────────────────

    def obter_insights(
        self,
        nivel="campaign",
        periodo="last_30d",
        data_inicio=None,
        data_fim=None,
    ):
        """
        Retorna métricas de desempenho.

        nivel: 'account' | 'campaign' | 'adset' | 'ad'
        periodo: 'today' | 'yesterday' | 'last_7d' | 'last_30d' | 'last_90d'
                 Se data_inicio/data_fim forem fornecidos, período é ignorado.
        """
        fields = [
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.adset_name,
            AdsInsights.Field.ad_name,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.reach,
            AdsInsights.Field.spend,
            AdsInsights.Field.cpc,
            AdsInsights.Field.cpm,
            AdsInsights.Field.ctr,
            AdsInsights.Field.frequency,
            AdsInsights.Field.actions,
            AdsInsights.Field.cost_per_action_type,
            AdsInsights.Field.date_start,
            AdsInsights.Field.date_stop,
        ]
        params = {"level": nivel}

        if data_inicio and data_fim:
            params["time_range"] = {"since": data_inicio, "until": data_fim}
        else:
            params["date_preset"] = periodo

        insights = self.account.get_insights(fields=fields, params=params)
        dados = [dict(i) for i in insights]
        df = pd.DataFrame(dados)
        print(f"{len(df)} linha(s) de insights obtida(s).")
        return df

    def exportar_relatorio(self, df, nome_arquivo=None, formato="xlsx"):
        """
        Exporta DataFrame para Excel ou CSV.

        formato: 'xlsx' | 'csv'
        """
        if nome_arquivo is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"relatorio_meta_{ts}.{formato}"

        if formato == "xlsx":
            df.to_excel(nome_arquivo, index=False)
        else:
            df.to_csv(nome_arquivo, index=False, encoding="utf-8-sig")

        print(f"Relatório exportado: {nome_arquivo}")
        return nome_arquivo

    def resumo_conta(self):
        """Exibe um resumo rápido da conta."""
        campos_conta = [
            AdAccount.Field.name,
            AdAccount.Field.account_status,
            AdAccount.Field.currency,
            AdAccount.Field.timezone_name,
            AdAccount.Field.amount_spent,
            AdAccount.Field.balance,
        ]
        info = self.account.api_get(fields=campos_conta)
        print("\n=== RESUMO DA CONTA ===")
        for k, v in dict(info).items():
            print(f"  {k}: {v}")
        print("=======================\n")
        return dict(info)
