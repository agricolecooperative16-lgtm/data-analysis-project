"""
واجهة تفاعلية باستخدام Gradio - بديل خفيف لـ Streamlit
"""

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))

from app import load_data, generate_sample_data, calculate_rfm, run_forecast

# تحميل البيانات
try:
    data = load_data()
    print(f"✅ تم تحميل {len(data)} صف من البيانات")
except Exception as e:
    print(f"⚠️ خطأ في تحميل البيانات: {e}")
    print("📦 إنشاء بيانات جديدة...")
    data, _ = generate_sample_data()
    data = load_data()

def analyze_rfm():
    """تحليل RFM"""
    try:
        # استخدام دالة RFM المحسنة
        from src.features.rfm_fixed import calculate_rfm_simple
        rfm = calculate_rfm_simple(data)
        
        # إنشاء رسم بياني لتوزيع الشرائح
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c', '#95a5a6']
        rfm['segment'].value_counts().plot(kind='bar', ax=ax, color=colors)
        ax.set_title('توزيع شرائح العملاء', fontsize=16)
        ax.set_xlabel('الشريحة')
        ax.set_ylabel('عدد العملاء')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()
        
        # إحصائيات
        stats = f"""
📊 **نتائج تحليل RFM**
- عدد العملاء: {len(rfm)}
- متوسط Recency: {rfm['recency'].mean():.0f} يوم
- متوسط Frequency: {rfm['frequency'].mean():.1f}
- متوسط Monetary: {rfm['monetary'].mean():.2f}

**توزيع الشرائح:**
{rfm['segment'].value_counts().to_string()}
        """
        
        return fig, stats
    except Exception as e:
        print(f"❌ خطأ في تحليل RFM: {e}")
        # إنشاء رسم بياني فارغ
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'خطأ في التحليل: {str(e)}', 
                ha='center', va='center', fontsize=14)
        return fig, f"❌ خطأ: {str(e)}"

def analyze_forecast(days=14):
    """التنبؤ بالمبيعات"""
    try:
        days = int(days)
        print(f"📈 بدء التنبؤ لـ {days} يوم...")
        
        # التحقق من وجود بيانات
        if data is None or data.empty:
            return None, "❌ لا توجد بيانات للتحليل"
        
        # استدعاء دالة التنبؤ
        forecast = run_forecast(data, forecast_days=days)
        
        # التحقق من النتيجة
        if forecast is None or forecast.empty:
            return None, "❌ فشل التنبؤ - لا توجد نتائج"
        
        # إنشاء رسم بياني
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(forecast['date'], forecast['forecast'], 
                marker='o', linestyle='-', color='#e74c3c', linewidth=2, markersize=8)
        ax.set_title(f'التنبؤ بالمبيعات لـ {days} يوم قادم', fontsize=16)
        ax.set_xlabel('التاريخ', fontsize=12)
        ax.set_ylabel('المبيعات المتوقعة', fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # إحصائيات
        stats = f"""
📈 **نتائج التنبؤ**
- أيام التنبؤ: {len(forecast)}
- متوسط التنبؤ اليومي: {forecast['forecast'].mean():.2f}
- إجمالي التنبؤ: {forecast['forecast'].sum():.2f}
- أقل توقع: {forecast['forecast'].min():.2f}
- أعلى توقع: {forecast['forecast'].max():.2f}
        """
        
        return fig, stats
        
    except Exception as e:
        print(f"❌ خطأ في التنبؤ: {e}")
        import traceback
        traceback.print_exc()
        
        # إنشاء رسم بياني يوضح الخطأ
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, f'خطأ في التنبؤ:\n{str(e)}', 
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.set_title('خطأ في التنبؤ', fontsize=16)
        return fig, f"❌ خطأ: {str(e)}"

def analyze_seasonal():
    """التحليل الموسمي"""
    try:
        df = data.copy()
        df['order_date'] = pd.to_datetime(df['order_date'])
        
        # تجميع حسب الشهر
        df['month'] = df['order_date'].dt.month
        df['year'] = df['order_date'].dt.year
        
        # حساب المبيعات الشهرية
        monthly = df.groupby(['year', 'month'])['amount'].sum().reset_index()
        
        # إذا كان هناك سنوات متعددة، احسب المتوسط لكل شهر
        if len(monthly['year'].unique()) > 1:
            monthly_avg = df.groupby('month')['amount'].mean().reset_index()
            monthly_avg.columns = ['month', 'avg_amount']
            monthly_total = df.groupby('month')['amount'].sum().reset_index()
            monthly_total.columns = ['month', 'total_amount']
        else:
            monthly_avg = df.groupby('month')['amount'].mean().reset_index()
            monthly_avg.columns = ['month', 'avg_amount']
            monthly_total = df.groupby('month')['amount'].sum().reset_index()
            monthly_total.columns = ['month', 'total_amount']
        
        # إنشاء رسم بياني
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # الرسم الأول: إجمالي المبيعات الشهرية
        colors = plt.cm.viridis(monthly_total['total_amount'] / monthly_total['total_amount'].max())
        ax1.bar(monthly_total['month'], monthly_total['total_amount'], color=colors)
        ax1.set_title('إجمالي المبيعات الشهرية', fontsize=14)
        ax1.set_xlabel('الشهر')
        ax1.set_ylabel('إجمالي المبيعات')
        ax1.set_xticks(range(1, 13))
        
        # الرسم الثاني: متوسط المبيعات الشهرية
        ax2.bar(monthly_avg['month'], monthly_avg['avg_amount'], color='#3498db', alpha=0.7)
        ax2.set_title('متوسط المبيعات الشهرية', fontsize=14)
        ax2.set_xlabel('الشهر')
        ax2.set_ylabel('متوسط المبيعات')
        ax2.set_xticks(range(1, 13))
        
        plt.tight_layout()
        
        # أفضل شهر
        best_month_total = monthly_total.loc[monthly_total['total_amount'].idxmax()]
        best_month_avg = monthly_avg.loc[monthly_avg['avg_amount'].idxmax()]
        
        stats = f"""
📊 **التحليل الموسمي**

**إجمالي المبيعات:**
- أفضل شهر (إجمالي): {best_month_total['month']}
- إجمالي المبيعات في أفضل شهر: {best_month_total['total_amount']:.2f}
- إجمالي المبيعات السنوية: {monthly_total['total_amount'].sum():.2f}
- متوسط المبيعات الشهرية: {monthly_total['total_amount'].mean():.2f}

**متوسط المبيعات:**
- أفضل شهر (متوسط): {best_month_avg['month']}
- متوسط المبيعات في أفضل شهر: {best_month_avg['avg_amount']:.2f}
- المتوسط العام: {monthly_avg['avg_amount'].mean():.2f}
        """
        
        return fig, stats
    except Exception as e:
        print(f"❌ خطأ في التحليل الموسمي: {e}")
        import traceback
        traceback.print_exc()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'خطأ في التحليل الموسمي:\n{str(e)}', 
                ha='center', va='center', fontsize=12)
        return fig, f"❌ خطأ: {str(e)}"

def show_data():
    """عرض البيانات"""
    try:
        return data.head(100)
    except Exception as e:
        return pd.DataFrame({'Error': [str(e)]})

# إنشاء واجهة Gradio
with gr.Blocks(theme=gr.themes.Soft(), title="نظام تحليل المبيعات") as demo:
    gr.Markdown("""
    # 🚀 نظام تحليل المبيعات والعملاء
    
    ### تحليل متكامل باستخدام RFM والتنبؤ والتحليل الموسمي
    """)
    
    with gr.Tabs():
        with gr.TabItem("📊 RFM Analysis"):
            gr.Markdown("### تحليل RFM - تقسيم العملاء حسب السلوك الشرائي")
            rfm_btn = gr.Button("تشغيل تحليل RFM", variant="primary")
            with gr.Row():
                rfm_plot = gr.Plot(label="توزيع الشرائح")
                rfm_stats = gr.Markdown(label="الإحصائيات")
            rfm_btn.click(analyze_rfm, outputs=[rfm_plot, rfm_stats])
        
        with gr.TabItem("📈 Forecasting"):
            gr.Markdown("### التنبؤ بالمبيعات المستقبلية")
            with gr.Row():
                days_slider = gr.Slider(7, 60, value=14, step=1, label="عدد أيام التنبؤ")
                forecast_btn = gr.Button("تشغيل التنبؤ", variant="primary")
            with gr.Row():
                forecast_plot = gr.Plot(label="التنبؤ")
                forecast_stats = gr.Markdown(label="الإحصائيات")
            forecast_btn.click(analyze_forecast, inputs=[days_slider], outputs=[forecast_plot, forecast_stats])
        
        with gr.TabItem("📊 Seasonal Analysis"):
            gr.Markdown("### التحليل الموسمي للمبيعات")
            seasonal_btn = gr.Button("تشغيل التحليل الموسمي", variant="primary")
            with gr.Row():
                seasonal_plot = gr.Plot(label="التحليل الموسمي")
                seasonal_stats = gr.Markdown(label="الإحصائيات")
            seasonal_btn.click(analyze_seasonal, outputs=[seasonal_plot, seasonal_stats])
        
        with gr.TabItem("📋 Data"):
            gr.Markdown("### عرض البيانات الخام")
            data_btn = gr.Button("عرض البيانات", variant="secondary")
            data_output = gr.Dataframe(label="البيانات")
            data_btn.click(show_data, outputs=[data_output])

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)