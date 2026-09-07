import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app import generate_sample_data, calculate_rfm, run_forecast, load_data

st.set_page_config(page_title="لوحة تحليل المبيعات", layout="wide")

st.title("🚀 لوحة تحليل المبيعات والعملاء")

# تحميل البيانات
@st.cache_data
def get_data():
    return load_data()

data = get_data()

# عرض البيانات
st.sidebar.header("📊 خيارات التحليل")
analysis_type = st.sidebar.selectbox(
    "اختر نوع التحليل:",
    ["RFM Analysis", "Forecasting", "Seasonal Analysis", "All"]
)

# عرض البيانات الخام
if st.sidebar.checkbox("عرض البيانات الخام"):
    st.subheader("📋 البيانات الخام")
    st.dataframe(data.head(100))

# تحليل RFM
if analysis_type in ["RFM Analysis", "All"]:
    st.header("📊 تحليل RFM")
    
    rfm = calculate_rfm(data)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("عدد العملاء", len(rfm))
    col2.metric("متوسط Recency", f"{rfm['recency'].mean():.0f} يوم")
    col3.metric("متوسط Monetary", f"{rfm['monetary'].mean():.2f}")
    
    # توزيع الشرائح
    fig, ax = plt.subplots(figsize=(10, 6))
    rfm['segment'].value_counts().plot(kind='bar', ax=ax)
    ax.set_title('توزيع شرائح العملاء')
    ax.set_xlabel('الشريحة')
    ax.set_ylabel('عدد العملاء')
    st.pyplot(fig)
    
    # عرض بيانات RFM
    st.subheader("بيانات RFM")
    st.dataframe(rfm)

# التنبؤ
if analysis_type in ["Forecasting", "All"]:
    st.header("📈 التنبؤ بالمبيعات")
    
    forecast_days = st.slider("عدد أيام التنبؤ:", 7, 60, 14)
    forecast = run_forecast(data, forecast_days=forecast_days)
    
    col1, col2 = st.columns(2)
    col1.metric("متوسط التنبؤ اليومي", f"{forecast['forecast'].mean():.2f}")
    col2.metric("إجمالي التنبؤ", f"{forecast['forecast'].sum():.2f}")
    
    # رسم التنبؤ
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(forecast['date'], forecast['forecast'], marker='o')
    ax.set_title('التنبؤ بالمبيعات')
    ax.set_xlabel('التاريخ')
    ax.set_ylabel('المبيعات المتوقعة')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

# التحليل الموسمي
if analysis_type in ["Seasonal Analysis", "All"]:
    st.header("📊 التحليل الموسمي")
    
    # حساب المبيعات الشهرية
    monthly = data.copy()
    monthly['order_date'] = pd.to_datetime(monthly['order_date'])
    monthly['month'] = monthly['order_date'].dt.month
    monthly_sales = monthly.groupby('month')['amount'].sum().reset_index()
    
    # رسم
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='month', y='amount', data=monthly_sales, ax=ax, palette='viridis')
    ax.set_title('المبيعات الشهرية')
    ax.set_xlabel('الشهر')
    ax.set_ylabel('إجمالي المبيعات')
    st.pyplot(fig)
    
    # أفضل شهر
    best_month = monthly_sales.loc[monthly_sales['amount'].idxmax()]
    st.success(f"🏆 أفضل شهر للمبيعات: {best_month['month']} بإجمالي {best_month['amount']:.2f}")

st.sidebar.info("تم تحديث البيانات بنجاح!")