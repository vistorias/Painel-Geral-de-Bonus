import streamlit as st
import pandas as pd
import json

# Configurações da página
st.set_page_config(page_title="Painel de Bônus Trimestral", layout="wide")

# Carregamento dos dados
df = pd.read_json("colaboradores_bonus_completo_com_destaque_v2.json")
with open("indicadores_nao_entregues.json", "r", encoding="utf-8") as f:
    indicadores_perdidos = json.load(f)

# Interface: Filtros
st.title("🚀 Painel de Bônus Trimestral")

col1, col2, col3, col4 = st.columns(4)
with col1:
    filtro_nome = st.text_input("🔍 Buscar por nome, função ou cidade")
with col2:
    empresas = ["Todas"] + sorted(df["EMPRESA"].unique())
    filtro_empresa = st.selectbox("🏢 Filtrar por empresa", empresas)
with col3:
    funcoes = ["Todas"] + sorted(df["FUNÇÃO"].unique())
    filtro_funcao = st.selectbox("👤 Filtrar por função", funcoes)
with col4:
    cidades = ["Todas"] + sorted(df["CIDADE"].unique())
    filtro_cidade = st.selectbox("📍 Filtrar por cidade", cidades)

filtro_tempo = st.multiselect("🕒 Filtrar por tempo de casa", options=sorted(df["TEMPO DE CASA"].unique()))
meses = ["Trimestre", "Janeiro", "Fevereiro", "Março"]
filtro_mes = st.radio("📅 Visualizar por mês:", meses, horizontal=True)

# Aplicar filtros
dados = df.copy()
if filtro_nome:
    dados = dados[dados["NOME"].str.contains(filtro_nome, case=False)]
if filtro_empresa != "Todas":
    dados = dados[dados["EMPRESA"] == filtro_empresa]
if filtro_funcao != "Todas":
    dados = dados[dados["FUNÇÃO"] == filtro_funcao]
if filtro_cidade != "Todas":
    dados = dados[dados["CIDADE"] == filtro_cidade]
if filtro_tempo:
    dados = dados[dados["TEMPO DE CASA"].isin(filtro_tempo)]

# Cálculo de perdas ajustadas por colaborador
def calcular_ajustes(row):
    if filtro_mes == "Trimestre":
        return row["VALOR TOTAL"], row["VALOR REAL"], row["VALOR PERDIDO"], row["% CUMPRIDO"]
    else:
        valor_mensal = row["VALOR TOTAL"] / 3
        perdas = 0
        indicadores = indicadores_perdidos.get(row["EMPRESA"], {}).get(filtro_mes, [])
        for indicador in indicadores:
            if indicador == "Satisfação do Cliente":
                perdas += valor_mensal * 0.275
            elif indicador == "Produção":
                perdas += valor_mensal * 0.15
            elif indicador == "Ticket Médio":
                perdas += valor_mensal * 0.15
        recebido = valor_mensal - perdas
        cumprimento = (recebido / valor_mensal * 100) if valor_mensal != 0 else 0
        return valor_mensal, recebido, perdas, cumprimento

dados[["META AJ", "REAL AJ", "PERDA AJ", "% AJ"]] = dados.apply(lambda row: pd.Series(calcular_ajustes(row)), axis=1)

# Resumo Geral
st.markdown("### 📊 Resumo Geral")
total = dados["META AJ"].sum()
real = dados["REAL AJ"].sum()
perdido = dados["PERDA AJ"].sum()
st.success(f"💰 **Total possível:** R$ {total:,.2f}")
st.info(f"📈 **Recebido:** R$ {real:,.2f}")
st.error(f"📉 **Deixou de ganhar:** R$ {perdido:,.2f}")

# Aviso de indicadores perdidos
if filtro_mes != "Trimestre" and filtro_empresa != "Todas":
    indicadores_mes = indicadores_perdidos.get(filtro_empresa, {}).get(filtro_mes, [])
    if indicadores_mes:
        st.warning(f"⚠️ Indicadores não cumpridos no mês de {filtro_mes}: {', '.join(indicadores_mes)}")

# Cards dos colaboradores
st.markdown("### 👥 Colaboradores")
cols = st.columns(3)
for idx, row in dados.iterrows():
    cor_destaque = "#d4edda" if row["DESTAQUE"] == "melhor" else "#f8d7da" if row["DESTAQUE"] == "pior" else "#f9f9f9"
    with cols[idx % 3]:
        st.markdown(f'''
            <div style="border:1px solid #ccc;padding:16px;border-radius:12px;margin-bottom:12px;background:{cor_destaque}">
                <h4>{row['NOME'].title()}</h4>
                <p><strong>{row['FUNÇÃO']}</strong> - {row['CIDADE']}</p>
                <p><strong>Meta {'Mensal' if filtro_mes != 'Trimestre' else 'Trimestral'}:</strong> R$ {row['META AJ']:,.2f}<br>
                <strong>Recebido:</strong> R$ {row['REAL AJ']:,.2f}<br>
                <strong>Deixou de ganhar:</strong> R$ {row['PERDA AJ']:,.2f}<br>
                <strong>Cumprimento:</strong> {row['% AJ']:.1f}%</p>
                <div style="height: 10px; background: #ddd; border-radius: 5px; overflow: hidden;">
                    <div style="width: {row['% AJ']:.1f}%; background: black; height: 100%;"></div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
