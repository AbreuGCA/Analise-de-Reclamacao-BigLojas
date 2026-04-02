import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import spacy
import numpy as np

import re
import unicodedata

UF_BRASIL = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO"
]

NOMES_ESTADOS_POR_UF = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia",
    "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

ESTADOS_POR_NOME = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM",
    "bahia": "BA", "ceara": "CE", "distrito federal": "DF", "espirito santo": "ES",
    "goias": "GO", "maranhao": "MA", "mato grosso": "MT", "mato grosso do sul": "MS",
    "minas gerais": "MG", "para": "PA", "paraiba": "PB", "parana": "PR",
    "pernambuco": "PE", "piaui": "PI", "rio de janeiro": "RJ",
    "rio grande do norte": "RN", "rio grande do sul": "RS", "rondonia": "RO",
    "roraima": "RR", "santa catarina": "SC", "sao paulo": "SP",
    "sergipe": "SE", "tocantins": "TO",
}

ESTADOS_INVALIDOS = {
    "", "-", "--", "N/A", "NA", "NULL", "NAN", "NONE", "SEM INFORMACAO",
    "SEM INFORMAÇÃO", "NAO INFORMADO", "NÃO INFORMADO", "NÃO INFORMADA",
    "ESTADO NÃO INFORMADO", "ESTADO NAO INFORMADO", "CIDADE NÃO INFORMADA"
}

def normalizar_texto_base(valor: str) -> str:
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def padronizar_estado(valor) -> str:
    if pd.isna(valor):
        return "NÃO INFORMADO"
    texto_original = str(valor).strip()
    texto_norm = normalizar_texto_base(texto_original).upper()
    texto_norm_lower = normalizar_texto_base(texto_original)
    if not texto_original or texto_norm in ESTADOS_INVALIDOS:
        return "NÃO INFORMADO"
    if len(texto_norm) == 2 and texto_norm.isalpha():
        return texto_norm
    if texto_norm_lower in ESTADOS_POR_NOME:
        return ESTADOS_POR_NOME[texto_norm_lower]
    if texto_norm in UF_BRASIL:
        return texto_norm
    return "NÃO INFORMADO"

def padronizar_cidade(valor) -> str:
    if pd.isna(valor):
        return "NÃO INFORMADA"
    texto_original = str(valor).strip()
    texto_norm = normalizar_texto_base(texto_original).upper()
    if not texto_original or texto_norm in ESTADOS_INVALIDOS:
        return "NÃO INFORMADA"
    return texto_original.title()

# ==========================================
# 0. CONFIGURAÇÃO INICIAL E CACHE DE DADOS
# ==========================================
st.set_page_config(
    page_title="BIG Lojas | Inteligência Executiva",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)



@st.cache_resource
def setup_nlp():
    return spacy.load('pt_core_news_sm')

nlp = setup_nlp()

@st.cache_data
def carregar_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        return requests.get(url).json()
    except:
        return None

geojson_brasil = carregar_geojson()

@st.cache_data
def carregar_dados():
    df = pd.read_csv('BIGLOJAS_DADOS_TRATADOS_FINAL.csv', sep=';', encoding='utf-8-sig')
    df['ANO_MES'] = df['ANO'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2)
    df['DESCRICAO'] = df['DESCRICAO'].astype(str)
    df['TAMANHO_TEXTO'] = df['DESCRICAO'].apply(len)
    return df

df = carregar_dados()

# ==========================================
# 1. BARRA LATERAL - FILTROS GLOBAIS
# ==========================================
st.sidebar.markdown(
    """
    <div style="display: flex; justify-content: center;">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTfhM5bvg-ONlcIrgbJJkVNNUAQppPQ5mly2A&s" width="100"/>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.title("Filtros Globais")

estados_disponiveis = sorted(df['ESTADO'].dropna().unique())
estado_selecionado = st.sidebar.multiselect("📍 Regional (Estado)", estados_disponiveis, default=estados_disponiveis)

status_disponiveis = df['STATUS'].dropna().unique()
status_selecionado = st.sidebar.multiselect("📌 Status da Ocorrência", status_disponiveis, default=status_disponiveis)

min_txt, max_txt = int(df['TAMANHO_TEXTO'].min()), int(df['TAMANHO_TEXTO'].max())
faixa_texto = st.sidebar.slider("📝 Complexidade do Relato (Tamanho do Texto)", min_txt, max_txt, (min_txt, max_txt))

df_filtrado = df[
    (df['ESTADO'].isin(estado_selecionado)) &
    (df['STATUS'].isin(status_selecionado)) &
    (df['TAMANHO_TEXTO'] >= faixa_texto[0]) &
    (df['TAMANHO_TEXTO'] <= faixa_texto[1])
]

# ==========================================
# 2. CABEÇALHO E FUNIL DE STORYTELLING
# ==========================================
st.title("📈 Análise de Reclamações - BIG Lojas")
st.divider()

if df_filtrado.empty:
    st.error("Nenhum dado encontrado com os filtros atuais. Por favor, ajuste a barra lateral.")
else:
    aba_macro, aba_logistica, aba_ambiente, aba_dados = st.tabs([
        "🌐 1. Visão Macro (Brasil)",
        "🚚 2. Deep Dive: Logística e Resolução",
        "🏪 3. Deep Dive: Ambiente e NLP",
        "📋 4. Plano de Ação (Base)"
    ])

    # ==========================================
    # ABA 1: VISÃO MACRO
    # ==========================================
    with aba_macro:
        st.header("1. Diagnóstico Geral: Como a BIG Lojas está no Brasil?")
        st.markdown("Monitoramento de picos de crise e áreas de atenção máxima na geografia nacional.")

        st.subheader("Evolução Histórica e Tendência de Crises (Média Móvel)")
        df_tempo = df_filtrado.groupby('ANO_MES').size().reset_index(name='Volume').sort_values('ANO_MES')
        df_tempo['Media_Movel'] = df_tempo['Volume'].rolling(window=3, min_periods=1).mean()

        fig_tempo = go.Figure()
        fig_tempo.add_trace(go.Scatter(x=df_tempo['ANO_MES'], y=df_tempo['Volume'], mode='lines+markers', name='Volume Real', line=dict(color='#1f77b4', width=2)))
        fig_tempo.add_trace(go.Scatter(x=df_tempo['ANO_MES'], y=df_tempo['Media_Movel'], mode='lines', name='Média Móvel (Tendência)', line=dict(color='red', dash='dash', width=3)))
        fig_tempo.update_layout(template='plotly_white', hovermode='x unified', height=400)
        st.plotly_chart(fig_tempo, width='stretch')

        col_mapa, col_pareto = st.columns(2)

        with col_mapa:
            st.subheader("Mapa de Calor Geográfico")
            anos_disponiveis = sorted(df_filtrado['ANO'].unique())
            ano_mapa = st.selectbox("Recorte Anual do Mapa:", anos_disponiveis)

            df_mapa_ano = df_filtrado[df_filtrado['ANO'] == ano_mapa]
            df_mapa = df_mapa_ano.groupby('ESTADO').size().reset_index(name='Volume')
            base_estados = pd.DataFrame({'ESTADO': UF_BRASIL})
            df_mapa = base_estados.merge(df_mapa, on='ESTADO', how='left').fillna({'Volume': 0})
            df_mapa['Volume'] = df_mapa['Volume'].astype(int)

            # ── MELHORIA DO MAPA ──────────────────────────────────────────
            # Escala logarítmica para separar valores próximos de zero dos
            # estados que realmente têm volume = 0 (exibidos em cinza claro)
            df_mapa['Volume_Log'] = np.log1p(df_mapa['Volume'])

            # Colorscale: cinza para 0, gradiente vermelho para > 0
            colorscale_mapa = [
                [0.00, '#d6d6d6'],
                [0.01, '#fde0d0'],
                [0.25, '#fc8d59'],
                [0.60, '#d7301f'],   
                [1.00, '#7f0000'],   
            ]

            estados_zero = df_mapa.loc[df_mapa['Volume'] == 0, 'ESTADO'].tolist()

            if geojson_brasil:
                fig_mapa = px.choropleth(
                    df_mapa,
                    geojson=geojson_brasil,
                    locations='ESTADO',
                    featureidkey='properties.sigla',
                    color='Volume_Log',           # usa escala log para cor
                    color_continuous_scale=colorscale_mapa,
                    scope="south america",
                    hover_data={'Volume': True, 'Volume_Log': False, 'ESTADO': True},
                    labels={'Volume_Log': 'Escala (log)', 'Volume': 'Ocorrências'}
                )
                fig_mapa.update_geos(fitbounds="locations", visible=False)
                fig_mapa.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    coloraxis_colorbar=dict(
                        title="Ocorrências",
                        tickvals=[np.log1p(v) for v in [0, 1, 5, 10, 50, 100, 500]
                                  if np.log1p(v) <= df_mapa['Volume_Log'].max()],
                        ticktext=[str(v) for v in [0, 1, 5, 10, 50, 100, 500]
                                  if np.log1p(v) <= df_mapa['Volume_Log'].max()],
                    )
                )
                st.plotly_chart(fig_mapa, width='stretch')

                # Legenda explicativa
                col_leg1, col_leg2 = st.columns(2)
                with col_leg1:
                    st.markdown(
                        "<span style='background:#d6d6d6;padding:2px 8px;border-radius:4px;'>&nbsp;&nbsp;&nbsp;&nbsp;</span>"
                        " &nbsp;**Sem ocorrências (0)**",
                        unsafe_allow_html=True
                    )
                with col_leg2:
                    st.markdown(
                        "<span style='background:#fc8d59;padding:2px 8px;border-radius:4px;'>&nbsp;&nbsp;&nbsp;&nbsp;</span>"
                        " &nbsp;**Com ocorrências (escala log)**",
                        unsafe_allow_html=True
                    )

                if estados_zero:
                    st.caption("🔘 Estados sem ocorrências no recorte: " + ", ".join(estados_zero))
            else:
                st.warning("Coordenadas do mapa indisponíveis.")
            # ─────────────────────────────────────────────────────────────

        with col_pareto:
            st.subheader("Princípio de Pareto (Ofensores Regionais)")
            df_pareto = df_filtrado.groupby('ESTADO').size().reset_index(name='Volume').sort_values('Volume', ascending=False)
            df_pareto['Perc_Acumulado'] = (df_pareto['Volume'].cumsum() / df_pareto['Volume'].sum()) * 100
            top3 = df_pareto.head(3)['ESTADO'].tolist()

            st.info(f"""
            🚨 Regiões Críticas:
            Os estados com maior volume de reclamações são: {', '.join(top3)}.
            Essas regiões devem ser tratadas como prioridade máxima.
            """)

            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=df_pareto['ESTADO'], y=df_pareto['Volume'], name='Volume de Queixas', marker_color='teal'))
            fig_pareto.add_trace(go.Scatter(x=df_pareto['ESTADO'], y=df_pareto['Perc_Acumulado'], name='% Acumulado', mode='lines+markers', line=dict(color='orange'), yaxis='y2'))
            fig_pareto.update_layout(template='plotly_white', yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 105]), showlegend=False, margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_pareto, width='stretch')

            total = df_pareto['Volume'].sum()
            top3_volume = df_pareto.head(3)['Volume'].sum()
            perc = (top3_volume / total) * 100
            st.success(f"""
            📊 Concentração de Reclamações:
            Os 3 principais estados concentram aproximadamente {perc:.2f}% de todas as reclamações.
            """)

    # ==========================================
    # ABA 2: DEEP DIVE - LOGÍSTICA E RESOLUÇÃO
    # ==========================================
    with aba_logistica:
        st.header("2. Gargalos de Logística: Capacidade de Resolução")

        df_log = df_filtrado[df_filtrado['OBJETIVO_PROJETO'] == 'Logística dos Produtos']

        if df_log.empty:
            st.info("Sem dados de Logística para os filtros atuais.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Taxa de Resolução Logística")
                df_status = df_log['STATUS'].value_counts().reset_index()
                df_status.columns = ['STATUS', 'Volume']
                fig_status = px.pie(df_status, names='STATUS', values='Volume', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_status.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_status, width='stretch')

            with c2:
                st.subheader("Correlação: Frustração x Status")
                fig_box = px.box(df_log, x='STATUS', y='TAMANHO_TEXTO', color='STATUS', template='plotly_white')
                fig_box.update_layout(showlegend=False, yaxis_title="Tamanho do Texto (Caracteres)", xaxis_title="Status atual")
                st.plotly_chart(fig_box, width='stretch')

    # ==========================================
    # ABA 3: DEEP DIVE - AMBIENTE E NLP
    # ==========================================
    with aba_ambiente:
        st.header("3. Gargalos de Ambiente: O que o cliente está dizendo?")

        df_amb = df_filtrado[df_filtrado['OBJETIVO_PROJETO'] == 'Qualidade do Ambiente']

        if df_amb.empty:
            st.info("Sem dados de Ambiente para os filtros atuais.")
        else:
            c1, c2 = st.columns([1, 1.5])

            with c1:
                st.subheader("Concentração por Categoria")
                pareto_amb = df_amb['CATEGORIA_ANALITICA'].value_counts().reset_index()
                pareto_amb.columns = ['Categoria', 'Volume']
                fig_bar_amb = px.bar(pareto_amb, x='Volume', y='Categoria', orientation='h', template='plotly_white', color='Volume', color_continuous_scale='Teal')
                fig_bar_amb.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_bar_amb, width='stretch')

            with c2:
                st.subheader("Mineração de Sentimentos (WordCloud)")

                texto_completo = " ".join(descricao for descricao in df_amb['DESCRICAO'].dropna())

                # Processa texto com spaCy e filtra apenas substantivos e adjetivos
                doc = nlp(texto_completo)
                palavras_filtradas = [
                    token.lemma_.lower() for token in doc
                    if token.pos_ in ["NOUN", "ADJ"] and len(token.lemma_) > 3 and not token.is_stop and token.is_alpha
                ]
                texto_filtrado = " ".join(palavras_filtradas)

                if texto_filtrado:
                    wordcloud = WordCloud(
                        stopwords=None,
                        background_color="white",
                        width=800,
                        height=400,
                        colormap='magma',
                        max_words=80
                    ).generate(texto_filtrado)
                    fig_wc, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                else:
                    st.info("Texto insuficiente para gerar WordCloud.")

    # ==========================================
    # ABA 4: PLANO DE AÇÃO E EXTRAÇÃO
    # ==========================================
    with aba_dados:
        st.header("4. Extração para Equipes Operacionais")
        st.markdown("Utilize esta tabela para auditar ocorrências específicas baseadas nas descobertas das abas anteriores.")

        colunas = ['ID', 'DATA', 'STATUS', 'ESTADO', 'CATEGORIA_ANALITICA', 'OBJETIVO_PROJETO', 'TAMANHO_TEXTO', 'DESCRICAO']
        colunas_exibir = [col for col in colunas if col in df_filtrado.columns]

        st.dataframe(df_filtrado[colunas_exibir], width='stretch', height=400)

        csv = df_filtrado[colunas_exibir].to_csv(sep=';', index=False, encoding='utf-8-sig')
        st.download_button("📥 Exportar Base para o Time (CSV)", data=csv, file_name='Plano_Acao_BigLojas.csv', mime='text/csv')

        st.markdown("""
        ## Métricas do Dashboard
        - Volume de Reclamações
        - Distribuição Geográfica
        - Tendência Temporal
        - Taxa de Resolução
        - Complexidade do Texto
        """)