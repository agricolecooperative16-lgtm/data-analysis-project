"""
لوحة تحكم تفاعلية لتحليل المبيعات والعملاء
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner
from src.analytics.kpis import KPIAnalyzer
from src.features.rfm import RFMAnalyzer
from src.utils.config import load_config

# إعداد الصفحة
st.set_page_config(
    page_title="نظام تحليل المبيعات والعملاء",
    page_icon="📊",
    layout="wide"
)

# عنوان التطبيق
st.title("📊 نظام تحليل المبيعات والعملاء")
st.markdown("---")

# تحميل الإعدادات
config = load_config()

# تحميل البيانات
@st.cache_data
def load_data(file_path):
    """تحميل البيانات مع التخزين المؤقت"""
    loader = DataLoader()
    if file_path.endswith('.csv'):
        return loader.load_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        return loader.load_excel(file_path)
    return None

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # اختيار ملف البيانات
    data_file = st.file_uploader(
        "تحميل ملف البيانات",
        type=['csv', 'xlsx', 'xls']
    )
    
    if data_file is not None:
        # حفظ الملف مؤقتاً
        temp_path = Path("data/raw/temp_data.csv")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        if data_file.name.endswith('.csv'):
            df = pd.read_csv(data_file)
        else:
            df = pd.read_excel(data_file)
        
        st.success(f"✅ تم تحميل {len(df)} سجل")
    else:
        # استخدام البيانات الافتراضية
        default_path = Path("data/raw/sales_data.csv")
        if default_path.exists():
            df = load_data(str(default_path))
            st.info(f"📁 استخدام البيانات الافتراضية: {len(df)} سجل")
        else:
            st.warning("⚠️ يرجى تحميل ملف بيانات")
            st.stop()

# عرض معلومات البيانات
st.sidebar.markdown("---")
st.sidebar.subheader("📊 معلومات البيانات")
st.sidebar.write(f"- عدد السجلات: {len(df):,}")
st.sidebar.write(f"- عدد الأعمدة: {len(df.columns)}")
st.sidebar.write(f"- الأعمدة: {', '.join(df.columns[:5])}...")

# تنظيف البيانات
cleaner = DataCleaner()

# تحويل التاريخ
date_col = config['analysis']['date_column']
if date_col in df.columns:
    df = cleaner.convert_dates(df, date_col)

# حساب المبلغ الإجمالي
if 'total_amount' not in df.columns:
    qty_col = config['analysis']['quantity_column']
    price_col = config['analysis']['price_column']
    if qty_col in df.columns and price_col in df.columns:
        df = cleaner.calculate_total_amount(df, qty_col, price_col)

# الحصول على أسماء الأعمدة
customer_id = config['analysis']['customer_id']
amount_col = config['analysis'].get('amount_column', 'total_amount')

# ====================
# علامات التبويب
# ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 نظرة عامة",
    "👥 تحليل العملاء",
    "📊 مؤشرات الأداء",
    "📉 اتجاهات المبيعات"
])

# ====================
# علامة التبويب 1: نظرة عامة
# ====================
with tab1:
    st.header("📈 نظرة عامة على البيانات")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 إجمالي الإيرادات",
            f"${df[amount_col].sum():,.2f}"
        )
    
    with col2:
        st.metric(
            "👥 عدد العملاء",
            f"{df[customer_id].nunique():,}"
        )
    
    with col3:
        st.metric(
            "📦 عدد المعاملات",
            f"{len(df):,}"
        )
    
    with col4:
        avg_basket = df[amount_col].sum() / len(df)
        st.metric(
            "🛒 متوسط السلة",
            f"${avg_basket:.2f}"
        )
    
    # مخطط المبيعات اليومية
    st.subheader("📈 اتجاه المبيعات اليومية")
    daily_sales = df.groupby(date_col)[amount_col].sum().reset_index()
    
    fig = px.line(
        daily_sales,
        x=date_col,
        y=amount_col,
        title="المبيعات اليومية",
        labels={date_col: "التاريخ", amount_col: "الإيرادات"}
    )
    st.plotly_chart(fig, use_container_width=True)

# ====================
# علامة التبويب 2: تحليل العملاء
# ====================
with tab2:
    st.header("👥 تحليل العملاء")
    
    # تحليل RFM
    rfm_analyzer = RFMAnalyzer()
    rfm_results = rfm_analyzer.analyze_rfm(
        df,
        customer_id,
        date_col,
        amount_col,
        config['analysis']['rfm']['segments']
    )
    
    rfm_df = rfm_results['rfm_scores']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # توزيع شرائح العملاء
        st.subheader("📊 توزيع شرائح العملاء")
        segment_counts = rfm_df['segment'].value_counts()
        
        fig = px.pie(
            values=segment_counts.values,
            names=segment_counts.index,
            title="شرائح العملاء"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # توزيع درجات RFM
        st.subheader("🎯 توزيع درجات RFM")
        rfm_scores = rfm_df[['r_score', 'f_score', 'm_score']].mean()
        
        fig = px.bar(
            x=['الحداثة (R)', 'التكرار (F)', 'القيمة (M)'],
            y=rfm_scores.values,
            title="متوسط درجات RFM",
            labels={'x': 'المعامل', 'y': 'المتوسط'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # عرض بيانات RFM
    st.subheader("📋 تفاصيل RFM للعملاء")
    st.dataframe(
        rfm_df.head(20),
        use_container_width=True,
        hide_index=True
    )

# ====================
# علامة التبويب 3: مؤشرات الأداء
# ====================
with tab3:
    st.header("📊 مؤشرات الأداء الرئيسية")
    
    # حساب الـ KPIs
    kpi_analyzer = KPIAnalyzer()
    kpis = kpi_analyzer.calculate_all_kpis(
        df,
        customer_id,
        config['analysis'].get('transaction_id', 'transaction_id'),
        date_col,
        amount_col
    )
    
    # عرض KPIs في أعمدة
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 إجمالي الإيرادات",
            f"${kpis['total_revenue']:,.2f}"
        )
        st.metric(
            "👥 العملاء الفريدين",
            f"{kpis['unique_customers']:,}"
        )
    
    with col2:
        st.metric(
            "🛒 متوسط السلة",
            f"${kpis['average_basket']:,.2f}"
        )
        st.metric(
            "📦 عدد المعاملات",
            f"{kpis['total_transactions']:,}"
        )
    
    with col3:
        st.metric(
            "💵 متوسط قيمة العميل",
            f"${kpis['avg_customer_value']:,.2f}"
        )
        st.metric(
            "🔄 معدل الاحتفاظ",
            f"{kpis['retention_rate']*100:.1f}%"
        )
    
    # أفضل 10 عملاء
    st.subheader("🏆 أفضل 10 عملاء من حيث القيمة")
    top_customers = kpis['customer_lifetime_value'].sort_values('clv', ascending=False).head(10)
    
    fig = px.bar(
        top_customers,
        x=customer_id,
        y='clv',
        title="قيمة العملاء الدائمة (CLV)",
        labels={customer_id: "العميل", 'clv': "القيمة الدائمة"}
    )
    st.plotly_chart(fig, use_container_width=True)

# ====================
# علامة التبويب 4: اتجاهات المبيعات
# ====================
with tab4:
    st.header("📉 تحليل اتجاهات المبيعات")
    
    # إضافة فلاتر
    col1, col2 = st.columns(2)
    
    with col1:
        # فلتر حسب الفترة
        period = st.selectbox(
            "الفترة الزمنية",
            ['يومي', 'أسبوعي', 'شهري', 'ربع سنوي']
        )
    
    with col2:
        # فلتر حسب التاريخ
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        date_range = st.date_input(
            "نطاق التاريخ",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    
    # تصفية البيانات حسب النطاق
    mask = (df[date_col] >= pd.to_datetime(date_range[0])) & \
           (df[date_col] <= pd.to_datetime(date_range[1]))
    filtered_df = df[mask]
    
    # تجميع حسب الفترة
    if period == 'يومي':
        grouped = filtered_df.groupby(date_col)[amount_col].sum().reset_index()
    elif period == 'أسبوعي':
        grouped = filtered_df.groupby(pd.Grouper(key=date_col, freq='W'))[amount_col].sum().reset_index()
    elif period == 'شهري':
        grouped = filtered_df.groupby(pd.Grouper(key=date_col, freq='M'))[amount_col].sum().reset_index()
    else:  # ربع سنوي
        grouped = filtered_df.groupby(pd.Grouper(key=date_col, freq='Q'))[amount_col].sum().reset_index()
    
    # رسم المبيعات
    fig = px.line(
        grouped,
        x=date_col,
        y=amount_col,
        title=f"اتجاه المبيعات ({period})",
        labels={date_col: "التاريخ", amount_col: "الإيرادات"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # إحصائيات إضافية
    st.subheader("📊 إحصائيات الفترة")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("إجمالي الإيرادات", f"${grouped[amount_col].sum():,.2f}")
    with col2:
        st.metric("متوسط الفترة", f"${grouped[amount_col].mean():,.2f}")
    with col3:
        growth = grouped[amount_col].pct_change().mean() * 100
        st.metric("متوسط النمو", f"{growth:.1f}%")

# ====================
# تذييل
# ====================
st.markdown("---")
st.caption(f"تم التحديث في: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("نظام تحليل المبيعات والعملاء - الإصدار 2.0")