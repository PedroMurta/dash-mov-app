import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import gdown
import ssl
import os

ssl._create_default_https_context = ssl._create_unverified_context  #

# 📌 Configuração inicial
st.set_page_config(page_title="Mov", layout="wide", page_icon="🤖")

# 📌 1. Função para baixar e carregar os dados do Google Drive
@st.cache_data
def load_data():
    GDRIVE_ID = "1X1m2d9LwU6Y2Vsua_owp9m_YQnychSOj"
    GDRIVE_URL = f"https://drive.google.com/uc?id={GDRIVE_ID}"
    FILE_PATH = "caged_20_24.parquet"

    # Se o arquivo não existir localmente, faça o download
    if not os.path.exists(FILE_PATH):
        st.info("📥 Baixando arquivo de dados... Aguarde.")
        gdown.download(GDRIVE_URL, FILE_PATH, quiet=False)

    # Ler o arquivo Parquet
    df = pd.read_parquet(FILE_PATH)

    # Criar colunas de Ano e Mês
    df["ano"] = df["competencia"].dt.year
    df["mes"] = df["competencia"].dt.month

    return df

# 📌 Carregar os dados
st.sidebar.info("📥 Carregando dados...")
df = load_data()
st.sidebar.success("✅ Dados carregados com sucesso!")

# 📌 3. Criar sidebar para filtros
st.sidebar.title("🔎 Filtros")
anos_disponiveis = sorted(df["ano"].unique(), reverse=True)
ufs_disponiveis = sorted(df["uf"].unique())
regioes_disponiveis = sorted(df["regiao"].unique())

anos_selecionados = st.sidebar.multiselect("📅 Selecione os anos", anos_disponiveis, default=anos_disponiveis[:3])
uf_selecionada = st.sidebar.selectbox("📍 Selecione um estado (UF)", ["Todos"] + ufs_disponiveis)
regiao_selecionada = st.sidebar.selectbox("🌍 Selecione uma região", ["Todas"] + regioes_disponiveis)

# 📌 4. Filtrar o DataFrame conforme os filtros selecionados
df_filtrado = df[df["ano"].isin(anos_selecionados)]

if uf_selecionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado["uf"] == uf_selecionada]

if regiao_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["regiao"] == regiao_selecionada]

# 📌 5. Criar DataFrame de saldo final acumulado APÓS FILTRAR OS DADOS
df_acumulado = (
    df_filtrado.groupby("competencia")
    .agg(
        total_movimentacoes=("saldo_movimentacao", "size"),
        admissoes=("admissao", "sum"),
        demissoes=("demissao", "sum"),
        saldo_final=("saldo_movimentacao", "sum"),
    )
    .reset_index()
)

# Criar saldo final acumulado e variação percentual
df_acumulado["saldo_final_acumulado"] = df_acumulado["saldo_final"].cumsum()

prev = df_acumulado["saldo_final_acumulado"].shift(1)
pct_change = (df_acumulado["saldo_final_acumulado"] - prev) / prev * 100

df_acumulado["variacao_percentual_saldo_acumulado"] = np.where(
    prev < 0, -pct_change, pct_change
).round(2)

# Criar colunas de Ano e Mês
df_acumulado["ano"] = df_acumulado["competencia"].dt.year
df_acumulado["mes"] = df_acumulado["competencia"].dt.month

# 📌 6. Criar abas no Streamlit
aba1, aba2 = st.tabs(["📊 Saldo Final Acumulado", "📉 Saldo Final Mensal"])

# 📌 7. Aplicar CSS Customizado
st.markdown(
    """
    <style>
        .stApp {
            background-color: #C9D6DF;
            font-family: 'Arial', sans-serif;
        }
        [data-testid="stSidebar"] {
            background-color: #E6F0F8;
        }
        h1 {
            color: #2C3E50;
            text-align: center;
            font-size: 28px;
            font-weight: bold;
        }
        .stButton>button {
            background-color: #2C3E50;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stButton>button:hover {
            background-color: #1A252F;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

with aba1:
    st.title("📊 Evolução do Saldo Final Acumulado")

    # 📌 Estatísticas
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Saldo Total", f"{int(df_acumulado['saldo_final_acumulado'].max()):,}".replace(",", "."), "Total acumulado")
    col2.metric("📈 Média", f"{int(df_acumulado['saldo_final_acumulado'].mean()):,}".replace(",", "."), "Média mensal")
    col3.metric("📉 Mínimo", f"{int(df_acumulado['saldo_final_acumulado'].min()):,}".replace(",", "."), "Menor saldo")
    col4.metric("📊 Máximo", f"{int(df_acumulado['saldo_final_acumulado'].max()):,}".replace(",", "."), "Maior saldo")
    col5.metric("📊 Desvio Padrão", f"{int(df_acumulado['saldo_final_acumulado'].std()):,}".replace(",", "."), "Variação")

    # 📌 Gráfico de linhas - Saldo Final Acumulado
    fig = px.line(
        df_acumulado,
        x="mes",
        y="saldo_final_acumulado",
        color="ano",
        markers=True,
        title="📊 Evolução Mensal do Saldo Final Acumulado",
        labels={"saldo_final_acumulado": "Saldo Final Acumulado", "mes": "Mês do Ano"},
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
    )

    st.plotly_chart(fig, use_container_width=True)

with aba2:
    st.title("📉 Evolução do Saldo Final Mensal")

    # 📌 Estatísticas para Saldo Final
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Saldo Total", f"{int(df_acumulado['saldo_final'].sum()):,}".replace(",", "."), "Total mensal")
    col2.metric("📈 Média", f"{int(df_acumulado['saldo_final'].mean()):,}".replace(",", "."), "Média mensal")
    col3.metric("📉 Mínimo", f"{int(df_acumulado['saldo_final'].min()):,}".replace(",", "."), "Menor saldo")
    col4.metric("📊 Máximo", f"{int(df_acumulado['saldo_final'].max()):,}".replace(",", "."), "Maior saldo")
    col5.metric("📊 Desvio Padrão", f"{int(df_acumulado['saldo_final'].std()):,}".replace(",", "."), "Variação")

    # 📌 Gráfico de linhas - Saldo Final Mensal
    fig2 = px.line(
        df_acumulado,
        x="mes",
        y="saldo_final",
        color="ano",
        markers=True,
        title="📉 Evolução Mensal do Saldo Final",
        labels={"saldo_final": "Saldo Final", "mes": "Mês do Ano"},
    )

    fig2.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
    )

    st.plotly_chart(fig2, use_container_width=True)
