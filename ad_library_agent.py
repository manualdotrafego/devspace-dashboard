"""
Agente de busca de criativos na Meta Ad Library.

Nicho: Aparelho Dental, Implante, Canal dentário
Países: BR, US, PT
Ranking: Longevidade + Volume de Impressões (score combinado)

Uso:
    python ad_library_agent.py
    python ad_library_agent.py --termo "implante dental" --limite 50
"""

import os
import argparse
import json
from datetime import datetime, date
from math import log

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────

API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}/ads_archive"

TERMOS_NICHO = [
    "aparelho dental",
    "aparelho ortodontico",
    "orthodontic braces",
    "implante dental",
    "implante dentario",
    "dental implant",
    "canal dentário",
    "tratamento de canal",
    "root canal",
    "dentista",
    "clinica odontologica",
]

PAISES = ["BR", "US", "PT"]

CAMPOS = [
    "id",
    "page_name",
    "page_id",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_creative_link_captions",
    "ad_snapshot_url",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "impressions",
    "spend",
    "currency",
    "publisher_platforms",
    "demographic_distribution",
    "delivery_by_region",
]

# ─────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────

def _parse_impressions(impressions_dict: dict | None) -> int:
    """Converte o range de impressões em um valor estimado (ponto médio)."""
    if not impressions_dict:
        return 0
    lower = int(impressions_dict.get("lower_bound", 0) or 0)
    upper = int(impressions_dict.get("upper_bound", lower) or lower)
    return (lower + upper) // 2


def _dias_rodando(start_str: str | None, stop_str: str | None) -> int:
    """Calcula quantos dias o anúncio ficou/está no ar."""
    if not start_str:
        return 0
    fmt = "%Y-%m-%dT%H:%M:%S%z"
    try:
        start = datetime.strptime(start_str, fmt).date()
    except ValueError:
        start = date.fromisoformat(start_str[:10])

    if stop_str:
        try:
            end = datetime.strptime(stop_str, fmt).date()
        except ValueError:
            end = date.fromisoformat(stop_str[:10])
    else:
        end = date.today()

    return max((end - start).days, 0)


def _score(dias: int, impressoes: int) -> float:
    """
    Score combinado (0-100) baseado em longevidade + impressões.
    Usa log para suavizar outliers.
    Peso: 50% longevidade, 50% impressões.
    """
    s_dias = log(dias + 1) * 10          # log para não favorecer demais anúncios muito antigos
    s_imp  = log(impressoes + 1) * 5
    return round(s_dias + s_imp, 2)


# ─────────────────────────────────────────
# BUSCA NA AD LIBRARY
# ─────────────────────────────────────────

def buscar_anuncios(
    termo: str,
    access_token: str,
    paises: list[str] = None,
    limite: int = 100,
) -> list[dict]:
    """Faz paginação na Ad Library API e retorna lista de anúncios."""
    if paises is None:
        paises = PAISES

    params = {
        "access_token": access_token,
        "search_terms": termo,
        "ad_reached_countries": json.dumps(paises),
        "ad_type": "ALL",
        "fields": ",".join(CAMPOS),
        "limit": min(limite, 100),  # máx 100 por página
    }

    resultados = []
    url = BASE_URL
    paginas = 0

    while url and len(resultados) < limite:
        resp = requests.get(url, params=params if paginas == 0 else {})
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"Erro da API: {data['error']}")

        resultados.extend(data.get("data", []))
        paginas += 1

        # paginação via cursor
        next_url = data.get("paging", {}).get("next")
        url = next_url
        params = {}  # próximas páginas usam a URL completa com cursor embutido

        print(f"  [{termo}] Página {paginas} — {len(resultados)} anúncios coletados...")

        if len(resultados) >= limite:
            break

    return resultados[:limite]


# ─────────────────────────────────────────
# PROCESSAMENTO E RANKING
# ─────────────────────────────────────────

def processar(anuncios: list[dict]) -> pd.DataFrame:
    """Transforma lista de anúncios brutos em DataFrame ranqueado."""
    linhas = []
    for ad in anuncios:
        dias = _dias_rodando(
            ad.get("ad_delivery_start_time"),
            ad.get("ad_delivery_stop_time"),
        )
        impressoes = _parse_impressions(ad.get("impressions"))

        # Corpo do criativo (texto principal)
        bodies = ad.get("ad_creative_bodies") or []
        titulo = (ad.get("ad_creative_link_titles") or [""])[0]
        descricao = (ad.get("ad_creative_link_descriptions") or [""])[0]

        # Status: ainda ativo ou encerrado
        status = "ATIVO" if not ad.get("ad_delivery_stop_time") else "ENCERRADO"

        linhas.append({
            "id": ad.get("id"),
            "pagina": ad.get("page_name"),
            "status": status,
            "dias_no_ar": dias,
            "impressoes_est": impressoes,
            "score": _score(dias, impressoes),
            "titulo": titulo,
            "descricao": descricao,
            "copy_principal": bodies[0] if bodies else "",
            "plataformas": ", ".join(ad.get("publisher_platforms") or []),
            "inicio": (ad.get("ad_delivery_start_time") or "")[:10],
            "fim": (ad.get("ad_delivery_stop_time") or "ativo")[:10],
            "link_criativo": ad.get("ad_snapshot_url"),
            "page_id": ad.get("page_id"),
        })

    df = pd.DataFrame(linhas)
    if df.empty:
        return df

    # Remove duplicatas pelo id do anúncio
    df = df.drop_duplicates(subset="id")

    # Ranking pelo score combinado
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.index += 1  # ranking começa em 1
    df.index.name = "rank"

    return df


# ─────────────────────────────────────────
# EXPORTAÇÃO
# ─────────────────────────────────────────

def exportar(df: pd.DataFrame, nome_base: str = "criativos_dentista"):
    """Exporta para Excel com formatação e para JSON."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_xlsx = f"{nome_base}_{ts}.xlsx"
    arquivo_json = f"{nome_base}_{ts}.json"

    # Excel com hiperlinks na coluna de criativo
    with pd.ExcelWriter(arquivo_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Ranking Criativos")
        ws = writer.sheets["Ranking Criativos"]

        # Largura das colunas
        col_widths = {
            "B": 30, "C": 30, "D": 10, "E": 10, "F": 15, "G": 10,
            "H": 50, "I": 50, "J": 80, "K": 20, "L": 12, "M": 12, "N": 50,
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width

    # JSON para uso programático
    df.reset_index().to_json(arquivo_json, orient="records", force_ascii=False, indent=2)

    print(f"\nExportado: {arquivo_xlsx}")
    print(f"Exportado: {arquivo_json}")
    return arquivo_xlsx, arquivo_json


# ─────────────────────────────────────────
# AGENTE PRINCIPAL
# ─────────────────────────────────────────

def rodar_agente(
    termos: list[str] = None,
    limite_por_termo: int = 50,
    paises: list[str] = None,
    exportar_resultado: bool = True,
):
    """
    Executa o agente completo:
    1. Busca anúncios para cada termo do nicho
    2. Processa e ranqueia pelo score combinado
    3. Exibe o Top 20 e exporta relatório
    """
    access_token = os.getenv("META_AD_LIBRARY_TOKEN")
    if not access_token:
        raise ValueError(
            "META_AD_LIBRARY_TOKEN não encontrado no .env\n"
            "Consulte as instruções em README_TOKEN.md para obter o token."
        )

    termos = termos or TERMOS_NICHO
    paises = paises or PAISES

    print("=" * 60)
    print("  AGENTE — META AD LIBRARY | NICHO DENTAL")
    print(f"  Termos: {len(termos)} | Países: {paises} | Limite/termo: {limite_por_termo}")
    print("=" * 60)

    todos_anuncios = []
    for termo in termos:
        print(f"\nBuscando: '{termo}'...")
        try:
            ads = buscar_anuncios(termo, access_token, paises, limite=limite_por_termo)
            todos_anuncios.extend(ads)
        except Exception as e:
            print(f"  ERRO ao buscar '{termo}': {e}")

    if not todos_anuncios:
        print("\nNenhum anúncio encontrado. Verifique o token e os termos.")
        return None

    print(f"\nTotal coletado (com duplicatas): {len(todos_anuncios)}")

    df = processar(todos_anuncios)
    print(f"Total após deduplicação: {len(df)}")

    # Exibe Top 20 no terminal
    print("\n" + "=" * 60)
    print("  TOP 20 CRIATIVOS — SCORE LONGEVIDADE + IMPRESSÕES")
    print("=" * 60)
    colunas_exibir = ["pagina", "status", "dias_no_ar", "impressoes_est", "score", "titulo", "link_criativo"]
    print(df.head(20)[colunas_exibir].to_string())

    if exportar_resultado:
        exportar(df)

    return df


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente de criativos — Meta Ad Library")
    parser.add_argument("--termo", nargs="+", help="Termos de busca customizados")
    parser.add_argument("--limite", type=int, default=50, help="Anúncios por termo (padrão: 50)")
    parser.add_argument("--paises", nargs="+", default=["BR", "US", "PT"], help="Códigos de país")
    parser.add_argument("--sem-export", action="store_true", help="Não exportar arquivos")
    args = parser.parse_args()

    rodar_agente(
        termos=args.termo,
        limite_por_termo=args.limite,
        paises=args.paises,
        exportar_resultado=not args.sem_export,
    )
