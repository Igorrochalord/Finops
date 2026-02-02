import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv

try:
    from pdf_generator import create_pdf
except ImportError:
    st.error("Erro: Arquivo 'pdf_generator.py' não encontrado.")
    st.stop()
load_dotenv()
st.set_page_config(
    page_title="Cloud Budget Master", 
    layout="wide", 
    page_icon="☁️",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dcdcdc;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    uri = os.getenv("MONGO_URI", "mongodb://172.24.247.186:27017/")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        return client[os.getenv("DB_NAME", "cloud_pricing")]
    except Exception as e:
        st.error(f"❌ Erro de conexão com Mongo: {e}")
        st.stop()

db = get_database()
collection = db[os.getenv("COLLECTION_NAME", "pricing_catalog")]

@st.cache_data(ttl=3600)
def get_dolar_rate():
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL"
        response = requests.get(url, timeout=2)
        data = response.json()
        return float(data['USDBRL']['bid'])
    except Exception:
        return 5.80

if "cart" not in st.session_state:
    st.session_state.cart = []
st.title("☁️ Cloud Budget Master")
st.markdown("### 🎯 Simulador de Custos & Aprovação de Budget (FinOps)")
st.markdown("---")
with st.sidebar:
    st.header("🛠️ Montar Infraestrutura")
    st.info("Selecione os recursos abaixo para adicionar ao seu orçamento.")
    
    providers = collection.distinct("provider")
    
    if not providers:
        st.error("⚠️ Banco vazio! Rode o script de seed.")
    else:
        selected_provider = st.selectbox("1. Provedor Cloud", providers)
        
        categories = collection.distinct("service_type", {"provider": selected_provider})
        selected_category = st.selectbox("2. Categoria do Serviço", categories)
        
        resources = list(collection.find({
            "provider": selected_provider, 
            "service_type": selected_category
        }))
        
        resource_options = {r.get("name", ""): r for r in resources if r.get("name")}
        
        if not resource_options:
            st.warning("Nenhum recurso encontrado.")
        else:
            selected_res_name = st.selectbox("3. Escolha o Recurso", list(resource_options.keys()))
            item_data = resource_options[selected_res_name]
            
            specs = item_data.get('specs', 'N/A')
            pricing = item_data.get("pricing", {})
            unit = pricing.get("unit", "Unit")
            price_usd = pricing.get("value_usd", 0.0)
            with st.container(border=True):
                st.markdown(f"**Specs:** {specs}")
                st.markdown(f"**Custo Unit:** <span style='color:green'>$ {price_usd:.4f}</span> / {unit}", unsafe_allow_html=True)
            col_qty, col_hr = st.columns(2)
            with col_qty:
                qty = st.number_input("Qtd.", min_value=1, value=1)
            with col_hr:
                hours = st.number_input("Horas/Mês", min_value=1, value=730, help="730h = Mês completo (24x7)")
            st.markdown("---")
            justification = st.text_area(
                "📝 Justificativa Técnica", 
                placeholder="Ex: Banco de dados dedicado para o microserviço de Pagamentos.",
                help="Explique por que este recurso é necessário. Isso aparecerá no relatório."
            )
            
            if st.button("➕ Adicionar Item", type="primary", use_container_width=True):
                multiplier = hours if unit == "Hour" else 1
                cost = price_usd * qty * multiplier
                
                st.session_state.cart.append({
                    "Provider": selected_provider,
                    "Type": selected_category,
                    "Resource": selected_res_name,
                    "Qty": qty,
                    "Unit Price": price_usd,
                    "Total USD": cost,
                    "Justification": justification if justification else "N/A"
                })
                st.toast("Recurso adicionado com sucesso!", icon="✅")
    st.markdown("---")
    if st.session_state.cart:
        if st.button("🗑️ Limpar Projeto", type="secondary", use_container_width=True):
            st.session_state.cart = []
            st.rerun()

if st.session_state.cart:
    df = pd.DataFrame(st.session_state.cart)
    total_usd = df["Total USD"].sum()
    dolar_ptax = get_dolar_rate()
    total_brl = total_usd * dolar_ptax
    total_brl_safe = total_brl * 1.10
    tab_dash, tab_details, tab_export = st.tabs(["📊 Dashboard Financeiro", "📋 Detalhamento & Justificativas", "📄 Relatório & Exportação"])
    with tab_dash:
        col1, col2, col3 = st.columns(3)
        col1.metric("Custo Mensal (USD)", f"$ {total_usd:,.2f}", border=True)
        col2.metric("Estimativa (BRL)", f"R$ {total_brl:,.2f}", delta=f"PTAX: {dolar_ptax:.2f}", border=True)
        col3.metric("Budget Seguro (+10%)", f"R$ {total_brl_safe:,.2f}", help="Margem para IOF e variação cambial", border=True)
        
        st.markdown("### 📈 Análise de Custos")
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            fig1 = px.pie(
                df, values='Total USD', names='Provider', 
                title='Distribuição por Cloud Provider', hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with c_chart2:
            df_grouped = df.groupby('Type')['Total USD'].sum().reset_index()
            fig2 = px.bar(
                df_grouped, x='Type', y='Total USD', 
                title='Custo por Categoria de Serviço',
                text_auto='.2s', color='Total USD',
                color_continuous_scale='Bluered'
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab_details:
        st.markdown("### 📦 Lista de Recursos e Justificativas")
        st.info("Revise os itens e as justificativas técnicas antes de gerar o relatório.")
        
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "Unit Price": st.column_config.NumberColumn(format="$ %.4f"),
                "Total USD": st.column_config.NumberColumn(format="$ %.2f"),
                "Justification": st.column_config.TextColumn("Justificativa Técnica", width="medium")
            }
        )

    with tab_export:
        col_exp_info, col_exp_btn = st.columns([2, 1])
        
        with col_exp_info:
            with st.expander("📚 Entenda o Cálculo do Relatório", expanded=True):
                st.markdown("""
                **Metodologia de Cálculo:**
                1. **Preço Base:** Obtido das APIs públicas (AWS Price List, Azure Retail, GCP Catalog).
                2. **Mensalização:** Recursos cobrados por hora são multiplicados por **730h** (média mensal).
                3. **Conversão Cambial:** Utiliza a taxa PTAX de venda do dia (`AwesomeAPI`).
                4. **Margem de Segurança:** O valor final em BRL sugere um buffer de **10%** para cobrir impostos (IOF) e flutuação do dólar.
                """)
        
        with col_exp_btn:
            st.markdown("### 📥 Download")
            st.write("Gere o PDF oficial para enviar à diretoria.")
            pdf_bytes = create_pdf(st.session_state.cart, total_usd, total_brl, dolar_ptax)
            st.download_button(
                label="Baixar Orçamento (PDF)",
                data=bytes(pdf_bytes),
                file_name="orcamento_cloud_master.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                icon="📄"
            )

else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.info("👈 **Comece agora:** Utilize o menu lateral esquerdo para selecionar um Provedor e adicionar recursos ao seu projeto.")
        st.image("https://cdn-icons-png.flaticon.com/512/4728/4728043.png", width=100)
        st.markdown("<center><small>Selecione AWS, Azure ou GCP para iniciar</small></center>", unsafe_allow_html=True)