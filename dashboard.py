"""
Meta Ads Dashboard — Captação de Leads / WhatsApp
Execute: streamlit run dashboard.py
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights

load_dotenv()

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meta Ads Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
        font-weight: 600;
        background: #f0f2f6;
    }
    .stTabs [aria-selected="true"] {
        background: #1877F2 !important;
        color: white !important;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 13px !important; color: #666; }

    /* Table alternating rows */
    .dataframe tbody tr:nth-child(even) { background-color: #f9f9f9; }

    /* Ad card */
    .ad-card { background: #fff; border: 1px solid #e4e6ef; border-radius: 12px; padding: 12px; }

    /* Quality badge */
    .badge-green  { color: #1a7f37; background: #dafbe1; border-radius: 4px; padding: 2px 7px; font-size: 12px; font-weight: 600; }
    .badge-yellow { color: #9a6700; background: #fff8c5; border-radius: 4px; padding: 2px 7px; font-size: 12px; font-weight: 600; }
    .badge-red    { color: #cf222e; background: #ffebe9; border-radius: 4px; padding: 2px 7px; font-size: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ─── CONSTANTS ─────────────────────────────────────────────────────────────────
WHATSAPP_ACTIONS = [
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.total_messaging_connection",
    "onsite_conversion.messaging_first_reply",
]
LEAD_ACTIONS = [
    "lead",
    "onsite_conversion.lead_grouped",
    "offsite_conversion.fb_pixel_lead",
]
INSIGHT_FIELDS = [
    "campaign_id", "campaign_name",
    "adset_id", "adset_name",
    "ad_id", "ad_name",
    "impressions", "reach", "frequency",
    "clicks", "inline_link_clicks",
    "ctr", "inline_link_click_ctr",
    "spend", "cpm", "cpc", "cost_per_inline_link_click",
    "outbound_clicks", "outbound_clicks_ctr",
    "actions", "cost_per_action_type",
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking",
    "date_start", "date_stop",
]
RANK_MAP = {
    "ABOVE_AVERAGE": ("⬆ Acima da média", "badge-green"),
    "AVERAGE": ("↔ Média", "badge-yellow"),
    "BELOW_AVERAGE_10": ("⬇ Abaixo (10%)", "badge-red"),
    "BELOW_AVERAGE_20": ("⬇⬇ Abaixo (20%)", "badge-red"),
    "BELOW_AVERAGE_35": ("⬇⬇⬇ Abaixo (35%)", "badge-red"),
}
STATUS_ICON = {"ACTIVE": "🟢", "PAUSED": "🟡", "DELETED": "🔴", "ARCHIVED": "⚫"}


# ─── API ───────────────────────────────────────────────────────────────────────
@st.cache_resource
def init_api():
    token = os.getenv("META_ACCESS_TOKEN")
    account_id = os.getenv("META_ACCOUNT_ID")
    if not token or not account_id:
        st.error("❌ Credenciais não encontradas. Verifique o arquivo .env")
        st.stop()
    FacebookAdsApi.init(access_token=token)
    return AdAccount(f"act_{account_id}"), account_id


# ─── DATA HELPERS ──────────────────────────────────────────────────────────────
def _extract_action(actions, types):
    if not isinstance(actions, list):
        return 0.0
    for item in actions:
        if item.get("action_type") in types:
            return float(item.get("value", 0))
    return 0.0


def _extract_cpa(cost_per_action, types):
    if not isinstance(cost_per_action, list):
        return None
    for item in cost_per_action:
        if item.get("action_type") in types:
            v = float(item.get("value", 0))
            return v if v > 0 else None
    return None


def _extract_outbound(outbound):
    if isinstance(outbound, list) and outbound:
        return float(outbound[0].get("value", 0))
    return 0.0


def _process_df(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])

    num_cols = [
        "impressions", "reach", "frequency", "clicks", "inline_link_clicks",
        "ctr", "inline_link_click_ctr", "spend", "cpm", "cpc",
        "cost_per_inline_link_click",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Results: WhatsApp first, then leads
    df["wa_starts"]  = df.get("actions", pd.Series([None]*len(df))).apply(
        lambda x: _extract_action(x, WHATSAPP_ACTIONS))
    df["lead_count"] = df.get("actions", pd.Series([None]*len(df))).apply(
        lambda x: _extract_action(x, LEAD_ACTIONS))
    df["resultados"] = df.apply(
        lambda r: r["wa_starts"] if r["wa_starts"] > 0 else r["lead_count"], axis=1)

    # Cost per result
    df["cpr_wa"]   = df.get("cost_per_action_type", pd.Series([None]*len(df))).apply(
        lambda x: _extract_cpa(x, WHATSAPP_ACTIONS))
    df["cpr_lead"] = df.get("cost_per_action_type", pd.Series([None]*len(df))).apply(
        lambda x: _extract_cpa(x, LEAD_ACTIONS))
    df["cpr"] = df.apply(
        lambda r: r["cpr_wa"] if r["cpr_wa"] else r["cpr_lead"], axis=1)

    # Outbound clicks
    if "outbound_clicks" in df.columns:
        df["outbound_clicks_val"] = df["outbound_clicks"].apply(_extract_outbound)
    else:
        df["outbound_clicks_val"] = 0.0

    df["date"] = pd.to_datetime(df["date_start"])
    return df


# ─── FETCH FUNCTIONS (cached) ──────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_insights_daily(level: str, date_start: str, date_end: str, _account):
    params = {
        "level": level,
        "time_increment": 1,
        "time_range": {"since": date_start, "until": date_end},
        "limit": 500,
    }
    rows = list(_account.get_insights(fields=INSIGHT_FIELDS, params=params))
    return _process_df(rows)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ads_with_previews(_account):
    fields = [
        "id", "name", "status", "adset_id", "adset_name",
        "campaign_id", "campaign_name",
        "creative{id,name,thumbnail_url,image_url,body,title,call_to_action_type}",
    ]
    ads = list(_account.get_ads(fields=fields, params={"limit": 300}))
    result = []
    for ad in ads:
        d = dict(ad)
        cr = d.pop("creative", {}) or {}
        d["thumbnail_url"]   = cr.get("thumbnail_url") or cr.get("image_url", "")
        d["creative_body"]   = cr.get("body", "")
        d["creative_title"]  = cr.get("title", "")
        d["cta_type"]        = cr.get("call_to_action_type", "")
        result.append(d)
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_account_info(_account):
    fields = ["name", "account_status", "currency", "timezone_name", "amount_spent"]
    return dict(_account.api_get(fields=fields))


# ─── FORMATTERS ────────────────────────────────────────────────────────────────
def brl(v):
    try:
        s = f"{float(v):,.2f}"
        return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def n(v, dec=0):
    try:
        return f"{float(v):,.{dec}f}".replace(",", ".")
    except Exception:
        return "0"


def pct(v):
    try:
        return f"{float(v):.2f}%"
    except Exception:
        return "—"


def rank_badge(val):
    if not val or val == "UNKNOWN":
        return "—"
    label, css = RANK_MAP.get(val, (val, "badge-yellow"))
    return f'<span class="{css}">{label}</span>'


def agg_df(df, group_cols):
    """Aggregate metrics for given group columns."""
    link_clicks_col = "inline_link_clicks" if "inline_link_clicks" in df.columns else "clicks"
    agg = df.groupby(group_cols).agg(
        impressions=(    "impressions",     "sum"),
        reach=(          "reach",           "sum"),
        link_clicks=(    link_clicks_col,   "sum"),
        spend=(          "spend",           "sum"),
        resultados=(     "resultados",      "sum"),
        wa_starts=(      "wa_starts",       "sum"),
        lead_count=(     "lead_count",      "sum"),
        frequency=(      "frequency",       "mean"),
        outbound=(       "outbound_clicks_val", "sum"),
    ).reset_index()
    agg["CTR"]   = (agg["link_clicks"] / agg["impressions"] * 100).fillna(0)
    agg["CPM"]   = (agg["spend"] / agg["impressions"] * 1000).fillna(0)
    agg["CPC"]   = (agg["spend"] / agg["link_clicks"]).replace([float("inf")], 0).fillna(0)
    agg["CPL"]   = (agg["spend"] / agg["resultados"]).replace([float("inf")], 0).fillna(0)
    agg["conv_rate"] = (agg["resultados"] / agg["link_clicks"] * 100).replace([float("inf")], 0).fillna(0)
    return agg


# ─── CHARTS ────────────────────────────────────────────────────────────────────
BLUE   = "#1877F2"
GREEN  = "#00C851"
ORANGE = "#FF6D00"
RED    = "#FF4444"


def dual_axis_chart(df, x, y_line, y_bar, y_line_name, y_bar_name, title):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df[x], y=df[y_line], name=y_line_name,
                   line=dict(color=BLUE, width=2.5),
                   fill="tozeroy", fillcolor="rgba(24,119,242,0.08)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(x=df[x], y=df[y_bar], name=y_bar_name,
               marker_color="rgba(0,200,81,0.75)"),
        secondary_y=True,
    )
    fig.update_layout(
        title=title, hovermode="x unified", height=360,
        legend=dict(orientation="h", y=-0.18),
        margin=dict(t=42, b=10, l=10, r=10),
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(title_text=y_line_name, secondary_y=False, gridcolor="#f0f0f0")
    fig.update_yaxes(title_text=y_bar_name,  secondary_y=True,  showgrid=False)
    return fig


def multi_line(df, x, y, color, title, y_label=""):
    fig = px.line(df, x=x, y=y, color=color, title=title, height=360,
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(hovermode="x unified", margin=dict(t=42, b=10),
                      legend=dict(orientation="h", y=-0.2),
                      plot_bgcolor="white")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f0f0f0", title_text=y_label)
    return fig


def hbar(df, x, y, title, color_scale="blues_r"):
    fig = px.bar(df.head(12), y=y, x=x, orientation="h", title=title,
                 height=380, color=x, color_continuous_scale=color_scale)
    fig.update_layout(showlegend=False, margin=dict(t=42, b=10),
                      coloraxis_showscale=False, plot_bgcolor="white")
    fig.update_yaxes(autorange="reversed")
    return fig


# ─── TAB: VISÃO GERAL ──────────────────────────────────────────────────────────
def tab_overview(df_all, info):
    currency = info.get("currency", "BRL")

    total_spend  = df_all["spend"].sum()
    total_imp    = df_all["impressions"].sum()
    total_reach  = df_all["reach"].sum()
    total_clicks = df_all["inline_link_clicks"].sum() if "inline_link_clicks" in df_all else df_all["clicks"].sum()
    total_res    = df_all["resultados"].sum()
    total_wa     = df_all["wa_starts"].sum()
    total_leads  = df_all["lead_count"].sum()
    avg_cpr      = total_spend / total_res   if total_res   > 0 else 0
    avg_ctr      = total_clicks / total_imp  * 100 if total_imp > 0 else 0
    avg_cpm      = total_spend  / total_imp  * 1000 if total_imp > 0 else 0
    avg_freq     = df_all["frequency"].mean() if "frequency" in df_all else 0

    # ── KPIs row 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Investimento",      brl(total_spend))
    c2.metric("🎯 Resultados Totais", n(total_res))
    c3.metric("💵 Custo por Resultado", brl(avg_cpr))
    c4.metric("🖱 CTR (Link Click)",  pct(avg_ctr))

    # ── KPIs row 2
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("👁 Impressões",         n(total_imp))
    c6.metric("👥 Alcance",            n(total_reach))
    c7.metric("📊 CPM",                brl(avg_cpm))
    c8.metric("🔄 Frequência Média",   n(avg_freq, 2))

    # ── WhatsApp vs Leads breakdown
    if total_wa > 0 or total_leads > 0:
        st.divider()
        st.caption("#### Breakdown de Resultados")
        wb1, wb2 = st.columns(2)
        wb1.metric("💬 Conversas WhatsApp iniciadas", n(total_wa))
        wb2.metric("📋 Leads (formulário/pixel)",     n(total_leads))

    st.divider()

    # ── Daily trend
    daily = (
        df_all.groupby("date")
        .agg(spend=("spend", "sum"), resultados=("resultados", "sum"),
             impressions=("impressions", "sum"))
        .reset_index()
    )

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.plotly_chart(
            dual_axis_chart(daily, "date", "spend", "resultados",
                            f"Investimento ({currency})", "Resultados",
                            "📈 Investimento vs Resultados por Dia"),
            use_container_width=True,
        )
    with col_b:
        camp_agg = agg_df(df_all, ["campaign_name"])
        fig_pie = px.pie(
            camp_agg, values="spend", names="campaign_name",
            title="Distribuição de Gasto", hole=0.42, height=360,
        )
        fig_pie.update_layout(legend=dict(orientation="h", y=-0.15),
                               margin=dict(t=42, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── CPM / CTR daily trend
    col_c, col_d = st.columns(2)
    with col_c:
        cpm_daily = df_all.groupby("date").apply(
            lambda g: g["spend"].sum() / g["impressions"].sum() * 1000 if g["impressions"].sum() > 0 else 0
        ).reset_index(name="cpm")
        fig_cpm = go.Figure(go.Scatter(
            x=cpm_daily["date"], y=cpm_daily["cpm"],
            mode="lines+markers", line=dict(color=ORANGE, width=2),
            name="CPM"))
        fig_cpm.update_layout(title="📉 CPM Diário (R$)", height=300,
                               plot_bgcolor="white", margin=dict(t=42, b=10))
        fig_cpm.update_xaxes(showgrid=False)
        fig_cpm.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig_cpm, use_container_width=True)
    with col_d:
        link_col = "inline_link_clicks" if "inline_link_clicks" in df_all.columns else "clicks"
        ctr_daily = df_all.groupby("date").apply(
            lambda g: g[link_col].sum() / g["impressions"].sum() * 100 if g["impressions"].sum() > 0 else 0
        ).reset_index(name="ctr")
        fig_ctr = go.Figure(go.Scatter(
            x=ctr_daily["date"], y=ctr_daily["ctr"],
            mode="lines+markers", line=dict(color=GREEN, width=2),
            name="CTR"))
        fig_ctr.update_layout(title="📈 CTR Diário (%)", height=300,
                               plot_bgcolor="white", margin=dict(t=42, b=10))
        fig_ctr.update_xaxes(showgrid=False)
        fig_ctr.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig_ctr, use_container_width=True)


# ─── TAB: CAMPANHAS ────────────────────────────────────────────────────────────
def tab_campanhas(df):
    agg = agg_df(df, ["campaign_id", "campaign_name"])
    agg = agg.sort_values("spend", ascending=False)

    st.subheader("Resumo por Campanha")
    display = agg[["campaign_name", "impressions", "reach", "link_clicks",
                    "spend", "resultados", "CTR", "CPM", "CPC", "CPL",
                    "conv_rate", "frequency"]].copy()
    display.columns = ["Campanha", "Impressões", "Alcance", "Cliques (Link)",
                        "Gasto (R$)", "Resultados", "CTR (%)", "CPM (R$)",
                        "CPC (R$)", "CPL (R$)", "Conv. (%)", "Freq."]
    st.dataframe(
        display.style.format({
            "Impressões":     "{:,.0f}",
            "Alcance":        "{:,.0f}",
            "Cliques (Link)": "{:,.0f}",
            "Gasto (R$)":     "R$ {:,.2f}",
            "Resultados":     "{:,.0f}",
            "CTR (%)":        "{:.2f}%",
            "CPM (R$)":       "R$ {:,.2f}",
            "CPC (R$)":       "R$ {:,.2f}",
            "CPL (R$)":       "R$ {:,.2f}",
            "Conv. (%)":      "{:.2f}%",
            "Freq.":          "{:.2f}",
        }).background_gradient(subset=["Gasto (R$)", "Resultados"], cmap="Blues"),
        use_container_width=True,
    )

    st.divider()

    # Daily breakdown per campaign
    camp_names = sorted(df["campaign_name"].unique().tolist())
    selected = st.multiselect(
        "Campanhas para gráfico diário:", camp_names,
        default=camp_names[:min(4, len(camp_names))])

    if selected:
        df_f = df[df["campaign_name"].isin(selected)]
        link_col = "inline_link_clicks" if "inline_link_clicks" in df_f.columns else "clicks"

        c1, c2 = st.columns(2)
        with c1:
            d_spend = df_f.groupby(["date", "campaign_name"])["spend"].sum().reset_index()
            st.plotly_chart(
                multi_line(d_spend, "date", "spend", "campaign_name",
                           "📈 Gasto Diário por Campanha (R$)", "R$"),
                use_container_width=True)
        with c2:
            d_res = df_f.groupby(["date", "campaign_name"])["resultados"].sum().reset_index()
            st.plotly_chart(
                multi_line(d_res, "date", "resultados", "campaign_name",
                           "🎯 Resultados Diários por Campanha"),
                use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            d_cpl = df_f.groupby(["date", "campaign_name"]).apply(
                lambda g: g["spend"].sum() / g["resultados"].sum()
                if g["resultados"].sum() > 0 else 0
            ).reset_index(name="cpl")
            st.plotly_chart(
                multi_line(d_cpl, "date", "cpl", "campaign_name",
                           "💵 CPL Diário por Campanha (R$)", "R$"),
                use_container_width=True)
        with c4:
            d_ctr = df_f.groupby(["date", "campaign_name"]).apply(
                lambda g: g[link_col].sum() / g["impressions"].sum() * 100
                if g["impressions"].sum() > 0 else 0
            ).reset_index(name="ctr")
            st.plotly_chart(
                multi_line(d_ctr, "date", "ctr", "campaign_name",
                           "🖱 CTR Diário por Campanha (%)", "%"),
                use_container_width=True)


# ─── TAB: CONJUNTOS ────────────────────────────────────────────────────────────
def tab_conjuntos(df):
    agg = agg_df(df, ["adset_id", "adset_name", "campaign_name"])
    agg = agg.sort_values("spend", ascending=False)

    st.subheader("Resumo por Conjunto de Anúncios")
    display = agg[["campaign_name", "adset_name", "impressions", "reach",
                    "link_clicks", "spend", "resultados", "CTR", "CPM",
                    "CPL", "conv_rate", "frequency"]].copy()
    display.columns = ["Campanha", "Conjunto", "Impressões", "Alcance",
                        "Cliques (Link)", "Gasto (R$)", "Resultados",
                        "CTR (%)", "CPM (R$)", "CPL (R$)", "Conv. (%)", "Freq."]
    st.dataframe(
        display.style.format({
            "Impressões":     "{:,.0f}",
            "Alcance":        "{:,.0f}",
            "Cliques (Link)": "{:,.0f}",
            "Gasto (R$)":     "R$ {:,.2f}",
            "Resultados":     "{:,.0f}",
            "CTR (%)":        "{:.2f}%",
            "CPM (R$)":       "R$ {:,.2f}",
            "CPL (R$)":       "R$ {:,.2f}",
            "Conv. (%)":      "{:.2f}%",
            "Freq.":          "{:.2f}",
        }).background_gradient(subset=["Gasto (R$)", "Resultados"], cmap="Blues"),
        use_container_width=True,
    )

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            hbar(agg, "spend", "adset_name", "🏆 Top Conjuntos por Gasto (R$)", "Blues"),
            use_container_width=True)
    with c2:
        top_res = agg.sort_values("resultados", ascending=False)
        st.plotly_chart(
            hbar(top_res, "resultados", "adset_name",
                 "🎯 Top Conjuntos por Resultados", "Greens"),
            use_container_width=True)

    # Scatter: CPL vs Resultados (bubble = spend)
    st.divider()
    st.subheader("🔍 Eficiência: CPL vs Resultados")
    agg_f = agg[(agg["resultados"] > 0) & (agg["CPL"] > 0)].copy()
    if not agg_f.empty:
        fig_scatter = px.scatter(
            agg_f, x="CPL", y="resultados", size="spend",
            color="campaign_name", hover_name="adset_name",
            title="Conjuntos — CPL x Resultados (tamanho = gasto)",
            height=400,
            labels={"CPL": "CPL (R$)", "resultados": "Resultados"},
        )
        fig_scatter.update_layout(plot_bgcolor="white", margin=dict(t=42))
        fig_scatter.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
        fig_scatter.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Dados insuficientes para o gráfico de dispersão.")

    # Daily selector
    st.divider()
    adset_names = sorted(df["adset_name"].unique().tolist())
    sel = st.multiselect("Conjuntos para gráfico diário:", adset_names,
                         default=adset_names[:min(4, len(adset_names))])
    if sel:
        df_f = df[df["adset_name"].isin(sel)]
        c3, c4 = st.columns(2)
        with c3:
            d = df_f.groupby(["date", "adset_name"])["spend"].sum().reset_index()
            st.plotly_chart(
                multi_line(d, "date", "spend", "adset_name",
                           "Gasto Diário por Conjunto (R$)"),
                use_container_width=True)
        with c4:
            d2 = df_f.groupby(["date", "adset_name"])["resultados"].sum().reset_index()
            st.plotly_chart(
                multi_line(d2, "date", "resultados", "adset_name",
                           "Resultados Diários por Conjunto"),
                use_container_width=True)


# ─── TAB: ANÚNCIOS ─────────────────────────────────────────────────────────────
def tab_anuncios(df, ads_info):
    agg = agg_df(df, ["ad_id", "ad_name", "adset_name", "campaign_name"])

    # Rankings (last available value per ad)
    rank_cols = ["quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]
    rank_df = df.dropna(subset=["ad_id"])
    for col in rank_cols:
        if col in rank_df.columns:
            latest = rank_df.groupby("ad_id")[col].last().reset_index()
            agg = agg.merge(latest, on="ad_id", how="left")
        else:
            agg[col] = None

    # Merge thumbnail info
    info_map = {a["id"]: a for a in ads_info}
    agg["thumbnail_url"]  = agg["ad_id"].map(lambda i: info_map.get(i, {}).get("thumbnail_url", ""))
    agg["status"]         = agg["ad_id"].map(lambda i: info_map.get(i, {}).get("status", ""))
    agg["creative_body"]  = agg["ad_id"].map(lambda i: info_map.get(i, {}).get("creative_body", ""))
    agg["creative_title"] = agg["ad_id"].map(lambda i: info_map.get(i, {}).get("creative_title", ""))
    agg["cta_type"]       = agg["ad_id"].map(lambda i: info_map.get(i, {}).get("cta_type", ""))

    agg = agg.sort_values("spend", ascending=False)

    # ── View toggle
    view = st.radio("Visualização:", ["🃏 Cards com Prévia", "📋 Tabela Completa"],
                    horizontal=True)

    if view == "📋 Tabela Completa":
        display = agg[["campaign_name", "adset_name", "ad_name", "status",
                        "impressions", "reach", "link_clicks", "spend",
                        "resultados", "CTR", "CPM", "CPC", "CPL",
                        "conv_rate", "frequency"]].copy()
        display.columns = ["Campanha", "Conjunto", "Anúncio", "Status",
                            "Impressões", "Alcance", "Cliques", "Gasto (R$)",
                            "Resultados", "CTR (%)", "CPM (R$)", "CPC (R$)",
                            "CPL (R$)", "Conv. (%)", "Freq."]
        st.dataframe(
            display.style.format({
                "Impressões":  "{:,.0f}",
                "Alcance":     "{:,.0f}",
                "Cliques":     "{:,.0f}",
                "Gasto (R$)":  "R$ {:,.2f}",
                "Resultados":  "{:,.0f}",
                "CTR (%)":     "{:.2f}%",
                "CPM (R$)":    "R$ {:,.2f}",
                "CPC (R$)":    "R$ {:,.2f}",
                "CPL (R$)":    "R$ {:,.2f}",
                "Conv. (%)":   "{:.2f}%",
                "Freq.":       "{:.2f}",
            }).background_gradient(subset=["Gasto (R$)", "Resultados"], cmap="Blues"),
            use_container_width=True,
        )
        return

    # ── Cards view
    sort_opt = st.selectbox("Ordenar por:",
                            ["Maior Gasto", "Mais Resultados", "Menor CPL", "Maior CTR"])
    sort_map = {
        "Maior Gasto":     ("spend",      False),
        "Mais Resultados": ("resultados", False),
        "Menor CPL":       ("CPL",        True),
        "Maior CTR":       ("CTR",        False),
    }
    scol, sasc = sort_map[sort_opt]
    agg_sorted = agg.sort_values(scol, ascending=sasc).reset_index(drop=True)

    # Filter by status
    statuses = ["Todos"] + sorted(agg_sorted["status"].unique().tolist())
    sel_status = st.selectbox("Filtrar por status:", statuses)
    if sel_status != "Todos":
        agg_sorted = agg_sorted[agg_sorted["status"] == sel_status]

    n_cols = 3
    for i in range(0, len(agg_sorted), n_cols):
        batch = agg_sorted.iloc[i:i + n_cols]
        cols = st.columns(n_cols)
        for col, (_, row) in zip(cols, batch.iterrows()):
            with col:
                with st.container(border=True):
                    # Thumbnail
                    if row["thumbnail_url"]:
                        st.image(row["thumbnail_url"], use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='background:#f0f2f6;border-radius:8px;"
                            "height:140px;display:flex;align-items:center;"
                            "justify-content:center;font-size:32px;'>📷</div>",
                            unsafe_allow_html=True,
                        )

                    # Name & status
                    st.markdown(f"**{row['ad_name'][:45]}{'…' if len(row['ad_name'])>45 else ''}**")
                    icon = STATUS_ICON.get(row["status"], "⚪")
                    st.markdown(f"{icon} `{row['status']}`  |  🎬 `{row['cta_type'] or '—'}`")

                    # Creative text preview
                    body = row["creative_body"] or row["creative_title"]
                    if body:
                        st.caption(f'"{body[:90]}{"…" if len(body)>90 else ""}"')

                    # Quality rankings
                    qr = row.get("quality_ranking")
                    er = row.get("engagement_rate_ranking")
                    cr_r = row.get("conversion_rate_ranking")
                    if any([qr, er, cr_r]):
                        st.markdown(
                            f"<small><b>Qualidade:</b> {rank_badge(qr)} "
                            f"&nbsp;<b>Engaj.:</b> {rank_badge(er)} "
                            f"&nbsp;<b>Conv.:</b> {rank_badge(cr_r)}</small>",
                            unsafe_allow_html=True,
                        )

                    st.divider()

                    # Metrics 2×3 grid
                    m1, m2, m3 = st.columns(3)
                    m1.metric("💰 Gasto",  brl(row["spend"]))
                    m2.metric("🎯 Result.", n(row["resultados"]))
                    m3.metric("💵 CPL",    brl(row["CPL"]))
                    m4, m5, m6 = st.columns(3)
                    m4.metric("🖱 CTR",    pct(row["CTR"]))
                    m5.metric("📊 CPM",    brl(row["CPM"]))
                    m6.metric("🔄 Freq.",  n(row["frequency"], 2))

                    st.caption(
                        f"👁 {n(row['impressions'])} impr. | "
                        f"👥 {n(row['reach'])} alcance | "
                        f"🖱 {n(row['link_clicks'])} cliques"
                    )

    # ── Top ads charts
    st.divider()
    st.subheader("📊 Comparativo de Anúncios")
    top = agg.nlargest(10, "spend")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            hbar(top, "spend", "ad_name", "Top 10 Anúncios — Gasto (R$)"),
            use_container_width=True)
    with c2:
        top_r = agg.nlargest(10, "resultados")
        st.plotly_chart(
            hbar(top_r, "resultados", "ad_name",
                 "Top 10 Anúncios — Resultados", "Greens"),
            use_container_width=True)

    # ── Daily breakdown for selected ad
    st.divider()
    st.subheader("📅 Evolução Diária de Anúncios")
    ad_names = sorted(df["ad_name"].unique().tolist())
    sel_ads = st.multiselect("Selecionar anúncios:", ad_names,
                             default=ad_names[:min(3, len(ad_names))])
    if sel_ads:
        df_f = df[df["ad_name"].isin(sel_ads)]
        link_col = "inline_link_clicks" if "inline_link_clicks" in df_f.columns else "clicks"
        cc1, cc2 = st.columns(2)
        with cc1:
            d = df_f.groupby(["date", "ad_name"])["spend"].sum().reset_index()
            st.plotly_chart(
                multi_line(d, "date", "spend", "ad_name",
                           "Gasto Diário por Anúncio (R$)"),
                use_container_width=True)
        with cc2:
            d2 = df_f.groupby(["date", "ad_name"])["resultados"].sum().reset_index()
            st.plotly_chart(
                multi_line(d2, "date", "resultados", "ad_name",
                           "Resultados Diários por Anúncio"),
                use_container_width=True)


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    account, account_id = init_api()

    # ── Sidebar
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Meta_Platforms_Inc._logo.svg/1200px-Meta_Platforms_Inc._logo.svg.png",
            width=120,
        )
        st.title("Meta Ads")
        st.caption(f"Conta: `act_{account_id}`")

        st.divider()
        st.subheader("📅 Período")
        today = date.today()
        presets = {
            "Hoje":           (today,                today),
            "Ontem":          (today - timedelta(1),  today - timedelta(1)),
            "Últimos 7 dias": (today - timedelta(6),  today),
            "Últimos 14 dias":(today - timedelta(13), today),
            "Últimos 30 dias":(today - timedelta(29), today),
            "Últimos 60 dias":(today - timedelta(59), today),
            "Últimos 90 dias":(today - timedelta(89), today),
            "Personalizado":  None,
        }
        preset = st.selectbox("Período rápido:", list(presets.keys()), index=4)
        if preset == "Personalizado":
            d_start = st.date_input("De:", today - timedelta(29))
            d_end   = st.date_input("Até:", today)
        else:
            d_start, d_end = presets[preset]

        st.divider()

        if st.button("🔄 Atualizar dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.caption("ℹ️ Cache: 30 min")

    # ── Header
    with st.spinner("Carregando dados da conta..."):
        info = fetch_account_info(account)

    acc_name = info.get("name", f"act_{account_id}")
    currency = info.get("currency", "BRL")
    spent    = info.get("amount_spent", 0)

    st.markdown(
        f"## 📊 Meta Ads Dashboard — {acc_name}  "
        f"<small style='color:#888'>| {currency} | Total gasto histórico: {brl(float(spent)/100 if spent else 0)}</small>",
        unsafe_allow_html=True,
    )
    st.caption(f"Período selecionado: **{d_start.strftime('%d/%m/%Y')}** até **{d_end.strftime('%d/%m/%Y')}**")
    st.divider()

    # ── Fetch all levels
    date_start_str = d_start.strftime("%Y-%m-%d")
    date_end_str   = d_end.strftime("%Y-%m-%d")

    with st.spinner("Buscando insights (pode levar alguns segundos)..."):
        df_ad = fetch_insights_daily("ad", date_start_str, date_end_str, account)

    if df_ad.empty:
        st.warning("Nenhum dado encontrado para o período selecionado.")
        return

    # Build campaign/adset views from ad-level data (already contains parent names)
    df_all = df_ad.copy()

    with st.spinner("Buscando prévias dos anúncios..."):
        ads_info = fetch_ads_with_previews(account)

    # ── Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Visão Geral",
        "📣 Campanhas",
        "🎯 Conjuntos de Anúncios",
        "🎨 Anúncios",
    ])

    with tab1:
        tab_overview(df_all, info)
    with tab2:
        tab_campanhas(df_all)
    with tab3:
        tab_conjuntos(df_all)
    with tab4:
        tab_anuncios(df_all, ads_info)


if __name__ == "__main__":
    main()
