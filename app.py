"""
التطبيق الرئيسي لنظام تحليل المبيعات والعملاء
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys
import logging
import warnings

warnings.filterwarnings('ignore')

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data(n_customers=100, n_orders=1000):
    """
    إنشاء بيانات نموذجية للمبيعات والعملاء
    """
    import random
    np.random.seed(42)
    random.seed(42)
    
    print("\n📦 توليد بيانات نموذجية...")
    
    # بيانات العملاء
    customers = {
        'customer_id': [f'CUST_{i:04d}' for i in range(1, n_customers + 1)],
        'customer_name': [f'عميل {i}' for i in range(1, n_customers + 1)],
        'join_date': [datetime.now() - timedelta(days=random.randint(30, 730)) 
                     for _ in range(n_customers)],
        'email': [f'customer{i}@example.com' for i in range(1, n_customers + 1)],
        'city': [random.choice(['الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام', 'الخبر']) 
                for _ in range(n_customers)]
    }
    
    customer_df = pd.DataFrame(customers)
    
    # بيانات المنتجات
    products = ['منتج A', 'منتج B', 'منتج C', 'منتج D', 'منتج E', 
                'منتج F', 'منتج G', 'منتج H']
    categories = ['الكترونيات', 'ملابس', 'منزل', 'مكتب', 'هدايا']
    
    # بيانات الطلبات
    orders_data = {
        'order_id': [f'ORD_{i:06d}' for i in range(1, n_orders + 1)],
        'customer_id': [random.choice(customer_df['customer_id'].tolist()) 
                       for _ in range(n_orders)],
        'order_date': [datetime.now() - timedelta(days=random.randint(0, 365)) 
                      for _ in range(n_orders)],
        'amount': np.random.gamma(2, 50, n_orders).round(2),
        'quantity': np.random.randint(1, 20, n_orders),
        'product': [random.choice(products) for _ in range(n_orders)],
        'category': [random.choice(categories) for _ in range(n_orders)]
    }
    
    orders_df = pd.DataFrame(orders_data)
    orders_df = orders_df.sort_values('order_date')
    
    # إنشاء المجلدات وحفظ البيانات
    data_path = Path('data/raw')
    data_path.mkdir(parents=True, exist_ok=True)
    
    customer_df.to_csv(data_path / 'customers.csv', index=False)
    orders_df.to_csv(data_path / 'sales.csv', index=False)
    orders_df.to_csv(data_path / 'orders.csv', index=False)
    
    print(f"✅ تم إنشاء {len(customer_df)} عميل و {len(orders_df)} طلب")
    print(f"📁 حفظ في: {data_path.absolute()}")
    
    return orders_df, customer_df


def load_data(file_path=None):
    """
    تحميل البيانات أو إنشاء بيانات نموذجية
    """
    if file_path:
        path = Path(file_path)
        if path.exists():
            logger.info(f"تحميل البيانات من: {file_path}")
            return pd.read_csv(file_path)
        else:
            logger.warning(f"الملف غير موجود: {file_path}")
    
    # إنشاء بيانات نموذجية
    orders, customers = generate_sample_data()
    return orders


def calculate_rfm(df, customer_col='customer_id', date_col='order_date', amount_col='amount'):
    """
    حساب تحليل RFM
    """
    print("\n📊 حساب تحليل RFM...")
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # أحدث تاريخ في البيانات
    max_date = df[date_col].max()
    
    # حساب RFM
    rfm = df.groupby(customer_col).agg({
        date_col: lambda x: (max_date - x.max()).days,  # Recency
        'order_id': 'count',  # Frequency
        amount_col: 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = [customer_col, 'recency', 'frequency', 'monetary']
    
    # إضافة Scores
    rfm['r_score'] = pd.qcut(rfm['recency'], 4, labels=[4, 3, 2, 1])
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    rfm['m_score'] = pd.qcut(rfm['monetary'], 4, labels=[1, 2, 3, 4])
    
    # RFM Score
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # تقسيم العملاء
    def segment_customer(row):
        if row['r_score'] >= 3 and row['f_score'] >= 3 and row['m_score'] >= 3:
            return 'VIP'
        elif row['r_score'] >= 3 and row['f_score'] >= 2:
            return 'نشط'
        elif row['r_score'] <= 2 and row['f_score'] >= 3:
            return 'مخلص'
        elif row['r_score'] <= 2 and row['f_score'] <= 2:
            return 'خطر'
        else:
            return 'متوسط'
    
    rfm['segment'] = rfm.apply(segment_customer, axis=1)
    
    print(f"✅ تم حساب RFM لـ {len(rfm)} عميل")
    print(f"📊 توزيع الشرائح:")
    print(rfm['segment'].value_counts())
    
    return rfm


def run_forecast(df, date_col='order_date', amount_col='amount', forecast_days=14):
    """
    التنبؤ بالمبيعات المستقبلية
    """
    try:
        print(f"\n📈 إجراء التنبؤ بالمبيعات لـ {forecast_days} يوم...")
        
        # نسخ البيانات
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # التأكد من وجود البيانات
        if df.empty:
            raise ValueError("لا توجد بيانات للتنبؤ")
        
        # تجميع المبيعات اليومية
        daily_sales = df.groupby(df[date_col].dt.date)[amount_col].sum().reset_index()
        daily_sales.columns = ['date', 'sales']
        daily_sales = daily_sales.sort_values('date')
        
        # إذا كانت البيانات قليلة، استخدم المتوسط البسيط
        if len(daily_sales) < 7:
            print("⚠️ بيانات قليلة، استخدام المتوسط البسيط للتنبؤ")
            avg_sales = daily_sales['sales'].mean()
            last_date = daily_sales['date'].max()
            future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
            forecast_df = pd.DataFrame({
                'date': future_dates,
                'forecast': [avg_sales] * forecast_days
            })
            return forecast_df
        
        # حساب المتوسطات المتحركة
        window_7 = min(7, len(daily_sales) - 1)
        window_30 = min(30, len(daily_sales) - 1)
        
        daily_sales['ma_7'] = daily_sales['sales'].rolling(window=window_7, min_periods=1).mean()
        daily_sales['ma_30'] = daily_sales['sales'].rolling(window=window_30, min_periods=1).mean()
        
        # استخدام المتوسط المتحرك الأخير للتنبؤ
        last_ma_30 = daily_sales['ma_30'].iloc[-1]
        last_ma_7 = daily_sales['ma_7'].iloc[-1]
        
        # إذا كانت القيم صفرية أو مفقودة، استخدم متوسط المبيعات
        if pd.isna(last_ma_30) or last_ma_30 == 0:
            last_ma_30 = daily_sales['sales'].mean()
        if pd.isna(last_ma_7) or last_ma_7 == 0:
            last_ma_7 = daily_sales['sales'].mean()
        
        # التنبؤ باستخدام المتوسط المرجح
        base_forecast = (last_ma_30 * 0.7 + last_ma_7 * 0.3)
        
        # إضافة بعض التغير العشوائي لجعل التنبؤ أكثر واقعية
        last_date = daily_sales['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
        
        # اتجاه بسيط (نمو أو انخفاض تدريجي)
        trend = 0.01  # نمو 1% يومياً
        daily_change = 1 + trend
        
        forecast_values = []
        current = base_forecast
        
        for i in range(forecast_days):
            # إضافة تقلب عشوائي بسيط
            noise = np.random.normal(0, current * 0.05)  # 5% تقلب
            current = max(0, current * daily_change + noise)  # لا يمكن أن تكون سالبة
            forecast_values.append(current)
        
        # إنشاء DataFrame النتيجة
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecast': forecast_values
        })
        
        print(f"✅ تم التنبؤ لـ {forecast_days} يوم")
        print(f"📊 متوسط التنبؤ: {forecast_df['forecast'].mean():.2f}")
        print(f"📊 إجمالي التنبؤ: {forecast_df['forecast'].sum():.2f}")
        
        return forecast_df
        
    except Exception as e:
        print(f"❌ خطأ في التنبؤ: {e}")
        import traceback
        traceback.print_exc()
        
        # إرجاع تنبؤ بسيط في حالة الخطأ
        try:
            avg = df[amount_col].mean()
            last_date = df[date_col].max()
            future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
            return pd.DataFrame({
                'date': future_dates,
                'forecast': [avg] * forecast_days
            })
        except:
            # إذا فشل كل شيء، إرجاع DataFrame فارغ
            return pd.DataFrame({'date': [], 'forecast': []})


def save_output(data, output_path, format='csv'):
    """
    حفظ النتائج
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if isinstance(data, dict):
        for name, df in data.items():
            save_output(df, output_dir / name, format)
        return
    
    if isinstance(data, pd.DataFrame):
        if format == 'csv':
            file_path = output_dir / 'output.csv'
            data.to_csv(file_path, index=False)
        elif format == 'excel':
            file_path = output_dir / 'output.xlsx'
            data.to_excel(file_path, index=False)
        elif format == 'json':
            file_path = output_dir / 'output.json'
            data.to_json(file_path, orient='records')
        else:
            file_path = output_dir / 'output.csv'
            data.to_csv(file_path, index=False)
        
        print(f"✅ تم حفظ النتائج في: {file_path}")
    else:
        # حفظ كمحتوى نصي
        file_path = output_dir / 'output.txt'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(data))
        print(f"✅ تم حفظ النتائج في: {file_path}")


def run_analysis(df, report_type='all'):
    """
    تشغيل التحليل المطلوب
    """
    results = {}
    
    if report_type in ['rfm', 'all']:
        results['rfm'] = calculate_rfm(df)
    
    if report_type in ['forecast', 'all']:
        results['forecast'] = run_forecast(df)
    
    if report_type in ['seasonal', 'all']:
        # تحليل موسمي بسيط
        print("\n📊 تحليل موسمي...")
        df_copy = df.copy()
        df_copy['order_date'] = pd.to_datetime(df_copy['order_date'])
        df_copy['month'] = df_copy['order_date'].dt.month
        df_copy['quarter'] = df_copy['order_date'].dt.quarter
        
        seasonal = df_copy.groupby('month')['amount'].sum().reset_index()
        seasonal.columns = ['month', 'total_sales']
        results['seasonal'] = seasonal
        
        print(f"✅ تم التحليل الموسمي: {len(seasonal)} شهر")
    
    return results


def main():
    """
    التشغيل الرئيسي للتطبيق
    """
    print("=" * 60)
    print("🚀 نظام تحليل المبيعات والعملاء")
    print("=" * 60)
    
    # تحميل البيانات
    print("\n📂 تحميل البيانات...")
    data = load_data()
    
    print(f"\n📊 نظرة على البيانات:")
    print(f"   - عدد الصفوف: {len(data)}")
    print(f"   - عدد الأعمدة: {len(data.columns)}")
    print(f"   - الأعمدة: {list(data.columns)}")
    print(f"   - الفترة: {data['order_date'].min()} إلى {data['order_date'].max()}")
    
    # تشغيل التحليل
    print("\n" + "=" * 60)
    results = run_analysis(data, report_type='all')
    
    # حفظ النتائج
    print("\n" + "=" * 60)
    print("💾 حفظ النتائج...")
    save_output(results, 'reports', format='csv')
    
    # عرض ملخص
    print("\n" + "=" * 60)
    print("📋 ملخص التحليل:")
    print("=" * 60)
    
    if 'rfm' in results:
        rfm = results['rfm']
        print(f"\n📊 RFM Analysis:")
        print(f"   - عدد العملاء: {len(rfm)}")
        print(f"   - متوسط Recency: {rfm['recency'].mean():.0f} يوم")
        print(f"   - متوسط Frequency: {rfm['frequency'].mean():.1f}")
        print(f"   - متوسط Monetary: {rfm['monetary'].mean():.2f}")
    
    if 'forecast' in results:
        forecast = results['forecast']
        print(f"\n📈 Forecasting:")
        print(f"   - أيام التنبؤ: {len(forecast)}")
        print(f"   - متوسط التنبؤ: {forecast['forecast'].mean():.2f}")
    
    if 'seasonal' in results:
        seasonal = results['seasonal']
        print(f"\n📊 Seasonal Analysis:")
        print(f"   - أفضل شهر: {seasonal.loc[seasonal['total_sales'].idxmax(), 'month']}")
    
    print("\n" + "=" * 60)
    print("✅ تم الانتهاء بنجاح!")
    print("📁 النتائج في مجلد: reports/")
    print("=" * 60)
# في بداية app.py، أضف هذا الاستيراد
from src.features.rfm_fixed import calculate_rfm_simple, get_rfm_insights

# واستبدل دالة calculate_rfm بـ:
def calculate_rfm(df, customer_col=None, date_col=None, amount_col=None):
    """
    حساب تحليل RFM - استخدام الدالة المضمونة
    """
    try:
        return calculate_rfm_simple(df, customer_col, date_col, amount_col)
    except Exception as e:
        print(f"❌ خطأ في تحليل RFM: {e}")
        print("📊 محاولة التحليل التلقائي...")
        
        # محاولة اكتشاف الأعمدة تلقائياً
        df_copy = df.copy()
        
        # البحث عن أعمدة مناسبة
        customer_cols = [col for col in df_copy.columns if 'customer' in col.lower() or 'cust' in col.lower() or 'id' in col.lower()]
        date_cols = [col for col in df_copy.columns if 'date' in col.lower()]
        amount_cols = [col for col in df_copy.columns if 'amount' in col.lower() or 'revenue' in col.lower() or 'price' in col.lower()]
        
        if customer_cols:
            customer_col = customer_cols[0]
        else:
            customer_col = df_copy.columns[0]  # أول عمود
        
        if date_cols:
            date_col = date_cols[0]
        else:
            date_col = df_copy.columns[1] if len(df_copy.columns) > 1 else df_copy.columns[0]
        
        if amount_cols:
            amount_col = amount_cols[0]
        else:
            amount_col = None
        
        print(f"   - عمود العملاء: {customer_col}")
        print(f"   - عمود التاريخ: {date_col}")
        print(f"   - عمود المبلغ: {amount_col}")
        
        return calculate_rfm_simple(df_copy, customer_col, date_col, amount_col)

if __name__ == "__main__":
    main()