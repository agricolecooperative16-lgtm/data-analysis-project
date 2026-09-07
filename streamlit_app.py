"""
تطبيق Streamlit لنفس المشروع
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.data.loader import DataLoader
from src.analytics.kpis import KPIAnalyzer
from src.features.rfm import RFMAnalyzer
from src.models.forecasting import SalesForecaster
from src.utils.config import load_config

st.set_page_config(page_title="تحليل المبيعات", layout="wide")

# تحميل الإعدادات
config = load_config()

# تحميل البيانات
@st.cache_data
def load_data():
    loader = DataLoader()
    df = loader.load_csv("data/raw/sales_data.csv")
    return df

df = load_data()

# عنوان
st.title("📊 نظام تحليل المبيعات والعملاء")

# قائمة جانبية
st.sidebar.title("⚙️ القائمة")
option = st.sidebar.selectbox(
    "اختر التحليل",
    ["نظرة عامة", "تحليل العملاء (RFM)", "التنبؤ", "التحليل الموسمي"]
)

if option == "نظرة عامة":
    st.header("📈 نظرة عامة")
    # عرض مؤشرات الأداء
    kpi_analyzer = KPIAnalyzer()
    kpis = kpi_analyzer.calculate_all_kpis(
        df,
        'customer_id',
        'transaction_id',
        'transaction_date',
        'total_amount'
    )
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 إجمالي الإيرادات", f"${kpis['total_revenue']:,.2f}")
    col2.metric("👥 عدد العملاء", kpis['unique_customers'])
    col3.metric("📦 عدد المعاملات", kpis['total_transactions'])
    col4.metric("🛒 متوسط السلة", f"${kpis['average_basket']:,.2f}")
    
    # رسم بياني
    daily_sales = df.groupby('transaction_date')['total_amount'].sum().reset_index()
    fig = px.line(daily_sales, x='transaction_date', y='total_amount', 
                  title='اتجاه المبيعات')
    st.plotly_chart(fig, use_container_width=True)

elif option == "تحليل العملاء (RFM)":
    st.header("👥 تحليل العملاء - RFM")
    # ... كود تحليل RFM

elif option == "التنبؤ":
    st.header("🔮 التنبؤ بالمبيعات")
    # ... كود التنبؤ

elif option == "التحليل الموسمي":
    st.header("🌦️ التحليل الموسمي")
    # ... كود التحليل الموسمي