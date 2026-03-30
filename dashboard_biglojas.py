import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords

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
    """Baixa as stopwords do NLTK para a WordCloud (REQUISITO 6)"""
    nltk.download('stopwords', quiet=True)
    return stopwords.words('portuguese')

stop_words_pt = setup_nlp()

@st.cache_data
def carregar_geojson():
    """Carrega coordenadas para o Mapa Cloroplético (REQUISITO 2)"""
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
    df['TAMANHO_TEXTO'] = df['DESCRICAO'].apply(len) # Variável para Boxplot e Filtros
    return df

df = carregar_dados()

# ==========================================
# 1. BARRA LATERAL - FILTROS GLOBAIS OBRIGATÓRIOS
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

# Filtro 1: Estado
estados_disponiveis = sorted(df['ESTADO'].dropna().unique())
estado_selecionado = st.sidebar.multiselect("📍 Regional (Estado)", estados_disponiveis, default=estados_disponiveis)

# Filtro 2: Status
status_disponiveis = df['STATUS'].dropna().unique()
status_selecionado = st.sidebar.multiselect("📌 Status da Ocorrência", status_disponiveis, default=status_disponiveis)

# Filtro 3: Faixa de tamanho do texto (REQUISITO DO PDF)
min_txt, max_txt = int(df['TAMANHO_TEXTO'].min()), int(df['TAMANHO_TEXTO'].max())
faixa_texto = st.sidebar.slider("📝 Complexidade do Relato (Tamanho do Texto)", min_txt, max_txt, (min_txt, max_txt))

# Aplicação dos Filtros
df_filtrado = df[
    (df['ESTADO'].isin(estado_selecionado)) &
    (df['STATUS'].isin(status_selecionado)) &
    (df['TAMANHO_TEXTO'] >= faixa_texto[0]) &
    (df['TAMANHO_TEXTO'] <= faixa_texto[1])
]

# ==========================================
# 2. CABEÇALHO E FUNIL DE STORYTELLING
# ==========================================
st.title("📈 Analíse de Reclamações - BIG Lojas")
st.divider()

if df_filtrado.empty:
    st.error("Nenhum dado encontrado com os filtros atuais. Por favor, ajuste a barra lateral.")
else:
    # ESTRUTURA DE ABAS (O Funil)
    aba_macro, aba_logistica, aba_ambiente, aba_dados = st.tabs([
        "🌐 1. Visão Macro (Brasil)", 
        "🚚 2. Deep Dive: Logística e Resolução", 
        "🏪 3. Deep Dive: Ambiente e NLP",
        "📋 4. Plano de Ação (Base)"
    ])

    # ==========================================
    # ABA 1: VISÃO MACRO (Geografia e Tempo)
    # ==========================================
    with aba_macro:
        st.header("1. Diagnóstico Geral: Como a BIG Lojas está no Brasil?")
        st.markdown("Monitoramento de picos de crise e áreas de atenção máxima na geografia nacional.")
        
        # REQUISITO 1: Série Temporal com Tendência (Média Móvel)
        st.subheader("Evolução Histórica e Tendência de Crises (Média Móvel)")
        df_tempo = df_filtrado.groupby('ANO_MES').size().reset_index(name='Volume').sort_values('ANO_MES')
        df_tempo['Media_Movel'] = df_tempo['Volume'].rolling(window=3, min_periods=1).mean()
        
        fig_tempo = go.Figure()
        fig_tempo.add_trace(go.Scatter(x=df_tempo['ANO_MES'], y=df_tempo['Volume'], mode='lines+markers', name='Volume Real', line=dict(color='#1f77b4', width=2)))
        fig_tempo.add_trace(go.Scatter(x=df_tempo['ANO_MES'], y=df_tempo['Media_Movel'], mode='lines', name='Média Móvel (Tendência)', line=dict(color='red', dash='dash', width=3)))
        fig_tempo.update_layout(template='plotly_white', hovermode='x unified', height=400)
        st.plotly_chart(fig_tempo, use_container_width=True)

        col_mapa, col_pareto = st.columns(2)
        with col_mapa:
            # REQUISITO 2: Mapa Cloroplético com Seletor de Ano
            st.subheader("Mapa de Calor Geográfico")
            anos_disponiveis = sorted(df_filtrado['ANO'].unique())
            ano_mapa = st.selectbox("Recorte Anual do Mapa:", anos_disponiveis)
            df_mapa = df_filtrado[df_filtrado['ANO'] == ano_mapa].groupby('ESTADO').size().reset_index(name='Volume')
            top_estados = df_filtrado['ESTADO'].value_counts().head(5)


            if geojson_brasil:
                fig_mapa = px.choropleth(df_mapa, geojson=geojson_brasil, locations='ESTADO', featureidkey='properties.sigla', color='Volume', color_continuous_scale="Reds", scope="south america")
                fig_mapa.update_geos(fitbounds="locations", visible=False)
                fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.warning("Coordenadas do mapa indisponíveis.")

        with col_pareto:
            # REQUISITO 3: Gráfico de Pareto
            st.subheader("Princípio de Pareto (Ofensores Regionais)")
            df_pareto = df_filtrado.groupby('ESTADO').size().reset_index(name='Volume').sort_values('Volume', ascending=False)
            df_pareto['Perc_Acumulado'] = (df_pareto['Volume'].cumsum() / df_pareto['Volume'].sum()) * 100
            top3 = df_pareto.head(3)['ESTADO'].tolist()

            st.info(f"""
            🚨 Regiões Críticas:
            Os estados com maior volume de reclamações são: {', '.join(top3)}.
            Essas regiões devem ser tratadas como prioridade máxima, pois concentram os maiores riscos de insatisfação do cliente.
            """)
            
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=df_pareto['ESTADO'], y=df_pareto['Volume'], name='Volume de Queixas', marker_color='teal'))
            fig_pareto.add_trace(go.Scatter(x=df_pareto['ESTADO'], y=df_pareto['Perc_Acumulado'], name='% Acumulado', mode='lines+markers', line=dict(color='orange'), yaxis='y2'))
            fig_pareto.update_layout(template='plotly_white', yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 105]), showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_pareto, use_container_width=True)
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
                # REQUISITO 4: Proporção de Resoluções
                st.subheader("Taxa de Resolução Logística")
                df_status = df_log['STATUS'].value_counts().reset_index()
                df_status.columns = ['STATUS', 'Volume']
                fig_status = px.pie(df_status, names='STATUS', values='Volume', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_status.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_status, use_container_width=True)
                
            with c2:
                # REQUISITO 5: Boxplot Text vs Status
                st.subheader("Correlação: Frustração x Status")
                fig_box = px.box(df_log, x='STATUS', y='TAMANHO_TEXTO', color='STATUS', template='plotly_white')
                fig_box.update_layout(showlegend=False, yaxis_title="Tamanho do Texto (Caracteres)", xaxis_title="Status atual")
                st.plotly_chart(fig_box, use_container_width=True)

    # ==========================================
    # ABA 3: DEEP DIVE - AMBIENTE E NLP
    # ==========================================
    with aba_ambiente:
        st.header("3. Gargalos de Ambiente: O que o cliente está dizendo?")
        
        df_amb = df_filtrado[df_filtrado['OBJETIVO_PROJETO'] == 'Qualidade do Ambiente']
        
        if df_amb.empty:
            st.info("Sem dados de Ambiente para os filtros atuais.")
        else:
            c1, c2 = st.columns([1, 1.5]) # Proporção para a wordcloud ficar maior
            
            with c1:
                st.subheader("Concentração por Categoria")
                pareto_amb = df_amb['CATEGORIA_ANALITICA'].value_counts().reset_index()
                pareto_amb.columns = ['Categoria', 'Volume']
                fig_bar_amb = px.bar(pareto_amb, x='Volume', y='Categoria', orientation='h', template='plotly_white', color='Volume', color_continuous_scale='Teal')
                fig_bar_amb.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar_amb, use_container_width=True)
                
            with c2:
                # REQUISITO 6: WordCloud (NLP Básica)
                st.subheader("Mineração de Sentimentos (WordCloud)")
                
                texto_completo = " ".join(descricao for descricao in df_amb['DESCRICAO'].dropna())
                stopwords_extras = ['loja', 'big', 'comprei', 'compra', 'dia', 'produto', 'fazer', 'lojas', 'hipermercado']
                stop_words_finais = stop_words_pt + stopwords_extras
                
                if len(texto_completo) > 0:
                    wordcloud = WordCloud(stopwords=stop_words_finais, background_color="white", width=800, height=400, colormap='magma', max_words=80).generate(texto_completo)
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
        
        st.dataframe(df_filtrado[colunas_exibir], use_container_width=True, height=400)
        
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