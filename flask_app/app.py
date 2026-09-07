"""
Flask Dashboard - نظام تحليل المبيعات والعملاء
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import io
import base64
import json
import warnings
import os
from datetime import datetime, timedelta
import random
import numpy as np

warnings.filterwarnings('ignore')

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent))

# إنشاء تطبيق Flask
app = Flask(__name__, 
            template_folder='templates',
            static_folder='../static',
            static_url_path='/static')

# ============ متغيرات عامة ============
orders_df = None
customers_df = None
data = None

# ============ دالة توليد البيانات ============
def generate_sample_data(n_customers=100, n_orders=1000):
    """
    إنشاء بيانات نموذجية للمبيعات والعملاء
    """
    np.random.seed(42)
    random.seed(42)
    
    print(f"\n📦 توليد بيانات نموذجية...")
    
    # بيانات العملاء
    customers = {
        'customer_id': [f'CUST_{i:04d}' for i in range(1, n_customers + 1)],
        'customer_name': [f'عميل {i}' for i in range(1, n_customers + 1)],
        'join_date': [datetime.now() - timedelta(days=random.randint(30, 730)) 
                     for _ in range(n_customers)],
        'email': [f'customer{i}@example.com' for i in range(1, n_customers + 1)],
        'city': [random.choice(['الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام', 'الخبر', 'القاهرة', 'دبي']) 
                for _ in range(n_customers)],
        'segment': [random.choice(['VIP', 'نشط', 'مخلص', 'خطر', 'متوسط']) 
                   for _ in range(n_customers)]
    }
    
    customer_df = pd.DataFrame(customers)
    
    # بيانات المنتجات
    products = ['منتج A', 'منتج B', 'منتج C', 'منتج D', 'منتج E', 
                'منتج F', 'منتج G', 'منتج H']
    categories = ['الكترونيات', 'ملابس', 'منزل', 'مكتب', 'هدايا', 'طعام']
    
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

# ============ تحميل البيانات ============
# ============ تحميل البيانات ============
# ============ تحميل البيانات ============
def load_data():
    """تحميل البيانات من ملفات CSV الموجودة"""
    global orders_df, customers_df, data
    
    orders_df = None
    customers_df = None
    
    # قائمة الملفات المحددة للتحميل
    file_mappings = {
        'orders': ['data/raw/orders.csv', 'data/raw/sales.csv', 'data/raw/sales_data.csv', 'data/processed/orders_clean.csv'],
        'customers': ['data/raw/customers.csv', 'data/processed/customers_clean.csv']
    }
    
    print("\n🔍 تحميل ملفات البيانات...")
    
    # تحميل ملفات الطلبات
    for file_path in file_mappings['orders']:
        path = Path(file_path)
        if path.exists():
            try:
                print(f"📂 تحميل: {file_path}")
                df = pd.read_csv(path)
                print(f"   ✅ {len(df)} صف, {len(df.columns)} عمود")
                
                if orders_df is None:
                    orders_df = df
                else:
                    # دمج إذا كانت الأعمدة متطابقة
                    if set(orders_df.columns) == set(df.columns):
                        orders_df = pd.concat([orders_df, df], ignore_index=True)
                        print(f"   ✅ تم دمج مع البيانات السابقة")
                    else:
                        print(f"   ⚠️ تنسيق مختلف، تم تجاهل الملف")
            except Exception as e:
                print(f"   ❌ خطأ: {e}")
    
    # تحميل ملفات العملاء
    for file_path in file_mappings['customers']:
        path = Path(file_path)
        if path.exists():
            try:
                print(f"📂 تحميل: {file_path}")
                df = pd.read_csv(path)
                print(f"   ✅ {len(df)} صف, {len(df.columns)} عمود")
                
                if customers_df is None:
                    customers_df = df
                else:
                    if set(customers_df.columns) == set(df.columns):
                        customers_df = pd.concat([customers_df, df], ignore_index=True)
                        print(f"   ✅ تم دمج مع البيانات السابقة")
            except Exception as e:
                print(f"   ❌ خطأ: {e}")
    
    # إذا لم يتم العثور على بيانات، إنشاء بيانات نموذجية
    if orders_df is None:
        print("❌ لم يتم العثور على بيانات الطلبات")
        print("📦 إنشاء بيانات نموذجية...")
        return generate_sample_data()
    
    # توحيد أسماء الأعمدة في بيانات الطلبات
    print("\n📊 معالجة بيانات الطلبات...")
    
    # إعادة تسمية الأعمدة إذا لزم الأمر
    column_mapping = {
        'CustomerID': 'customer_id',
        'OrderDate': 'order_date',
        'OrderID': 'order_id',
        'Amount': 'amount',
        'Product': 'product',
        'Category': 'category',
        'Quantity': 'quantity'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in orders_df.columns:
            orders_df = orders_df.rename(columns={old_name: new_name})
    
    # التأكد من وجود الأعمدة الأساسية
    if 'customer_id' not in orders_df.columns:
        # البحث عن عمود يحتوي على 'id' أو 'customer'
        for col in orders_df.columns:
            if 'id' in col.lower() or 'customer' in col.lower():
                orders_df['customer_id'] = orders_df[col]
                break
        else:
            # استخدام أول عمود
            orders_df['customer_id'] = orders_df.iloc[:, 0]
    
    if 'order_date' not in orders_df.columns:
        for col in orders_df.columns:
            if 'date' in col.lower():
                orders_df['order_date'] = pd.to_datetime(orders_df[col])
                break
        else:
            orders_df['order_date'] = pd.Timestamp.now()
    else:
        try:
            orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
        except:
            orders_df['order_date'] = pd.Timestamp.now()
    
    if 'amount' not in orders_df.columns:
        for col in orders_df.columns:
            if any(x in col.lower() for x in ['amount', 'price', 'revenue', 'total', 'value']):
                orders_df['amount'] = pd.to_numeric(orders_df[col], errors='coerce').fillna(0)
                break
        else:
            orders_df['amount'] = 1.0
    
    if 'order_id' not in orders_df.columns:
        orders_df['order_id'] = [f'ORD_{i}' for i in range(len(orders_df))]
    
    # معالجة بيانات العملاء
    if customers_df is not None:
        print("\n📊 معالجة بيانات العملاء...")
        
        # إعادة تسمية الأعمدة
        for old_name, new_name in column_mapping.items():
            if old_name in customers_df.columns:
                customers_df = customers_df.rename(columns={old_name: new_name})
        
        if 'customer_id' not in customers_df.columns:
            for col in customers_df.columns:
                if 'id' in col.lower() or 'customer' in col.lower():
                    customers_df['customer_id'] = customers_df[col]
                    break
            else:
                customers_df['customer_id'] = [f'CUST_{i}' for i in range(len(customers_df))]
        
        if 'customer_name' not in customers_df.columns:
            for col in customers_df.columns:
                if 'name' in col.lower() or 'customer' in col.lower():
                    customers_df['customer_name'] = customers_df[col]
                    break
            else:
                customers_df['customer_name'] = [f'عميل {i}' for i in range(len(customers_df))]
    else:
        # إنشاء بيانات عملاء من بيانات الطلبات
        print("\n📦 إنشاء بيانات عملاء من الطلبات...")
        unique_customers = orders_df['customer_id'].unique()
        customers_df = pd.DataFrame({
            'customer_id': unique_customers,
            'customer_name': [f'عميل {i}' for i in range(1, len(unique_customers) + 1)],
            'city': ['الرياض'] * len(unique_customers)
        })
    
    # دمج البيانات
    try:
        if 'customer_id' in orders_df.columns and 'customer_id' in customers_df.columns:
            # اختيار الأعمدة المتاحة للدمج
            merge_cols = ['customer_id']
            if 'customer_name' in customers_df.columns:
                merge_cols.append('customer_name')
            if 'city' in customers_df.columns:
                merge_cols.append('city')
            
            data = orders_df.merge(customers_df[merge_cols], on='customer_id', how='left')
            print(f"\n✅ تم دمج البيانات: {len(data)} صف")
        else:
            data = orders_df
    except Exception as e:
        print(f"⚠️ خطأ في دمج البيانات: {e}")
        data = orders_df
    
    # عرض ملخص البيانات
    print("\n" + "=" * 50)
    print("📊 ملخص البيانات المحملة:")
    print("=" * 50)
    print(f"📋 عدد الطلبات: {len(orders_df):,}")
    print(f"👤 عدد العملاء: {orders_df['customer_id'].nunique():,}")
    print(f"💰 إجمالي الإيرادات: {orders_df['amount'].sum():,.2f}")
    print(f"📊 متوسط قيمة الطلب: {orders_df['amount'].mean():,.2f}")
    print(f"📅 الفترة: {orders_df['order_date'].min()} إلى {orders_df['order_date'].max()}")
    print(f"📂 أعمدة البيانات: {list(data.columns)}")
    print("=" * 50)
    
    return orders_df, customers_df

# ============ دالة التنبؤ ============
def run_forecast(df, date_col='order_date', amount_col='amount', forecast_days=14):
    """التنبؤ بالمبيعات المستقبلية"""
    try:
        print(f"\n📈 إجراء التنبؤ بالمبيعات لـ {forecast_days} يوم...")
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        if df.empty:
            raise ValueError("لا توجد بيانات للتنبؤ")
        
        # تجميع المبيعات اليومية
        daily_sales = df.groupby(df[date_col].dt.date)[amount_col].sum().reset_index()
        daily_sales.columns = ['date', 'sales']
        daily_sales = daily_sales.sort_values('date')
        
        if len(daily_sales) < 7:
            avg_sales = daily_sales['sales'].mean()
            last_date = daily_sales['date'].max()
            future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
            forecast_df = pd.DataFrame({
                'date': future_dates,
                'forecast': [avg_sales] * forecast_days
            })
            return forecast_df
        
        # المتوسطات المتحركة
        window_7 = min(7, len(daily_sales) - 1)
        window_30 = min(30, len(daily_sales) - 1)
        
        daily_sales['ma_7'] = daily_sales['sales'].rolling(window=window_7, min_periods=1).mean()
        daily_sales['ma_30'] = daily_sales['sales'].rolling(window=window_30, min_periods=1).mean()
        
        last_ma_30 = daily_sales['ma_30'].iloc[-1] if not pd.isna(daily_sales['ma_30'].iloc[-1]) else daily_sales['sales'].mean()
        last_ma_7 = daily_sales['ma_7'].iloc[-1] if not pd.isna(daily_sales['ma_7'].iloc[-1]) else daily_sales['sales'].mean()
        
        base_forecast = (last_ma_30 * 0.7 + last_ma_7 * 0.3)
        
        last_date = daily_sales['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
        
        trend = 0.01
        daily_change = 1 + trend
        
        forecast_values = []
        current = base_forecast
        
        for i in range(forecast_days):
            noise = np.random.normal(0, current * 0.05)
            current = max(0, current * daily_change + noise)
            forecast_values.append(current)
        
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'forecast': forecast_values
        })
        
        return forecast_df
        
    except Exception as e:
        print(f"❌ خطأ في التنبؤ: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame({'date': [], 'forecast': []})

# ============ دالة RFM ============
def calculate_rfm_simple(df, customer_col='customer_id', date_col='order_date', amount_col='amount'):
    """حساب تحليل RFM"""
    try:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        max_date = df[date_col].max()
        
        grouped = df.groupby(customer_col)
        recency = grouped[date_col].max().apply(lambda x: (max_date - x).days)
        frequency = grouped[date_col].count()
        monetary = grouped[amount_col].sum()
        
        rfm = pd.concat([recency, frequency, monetary], axis=1)
        rfm.columns = ['recency', 'frequency', 'monetary']
        rfm = rfm.reset_index()
        rfm = rfm.rename(columns={customer_col: 'customer_id'})
        
        rfm['recency'] = pd.to_numeric(rfm['recency'], errors='coerce').fillna(0)
        rfm['frequency'] = pd.to_numeric(rfm['frequency'], errors='coerce').fillna(0)
        rfm['monetary'] = pd.to_numeric(rfm['monetary'], errors='coerce').fillna(0)
        rfm = rfm[rfm['frequency'] > 0]
        
        # حساب النقاط
        try:
            rfm['r_score'] = pd.qcut(rfm['recency'], q=4, labels=[4, 3, 2, 1], duplicates='drop')
            rfm['f_score'] = pd.qcut(rfm['frequency'], q=4, labels=[1, 2, 3, 4], duplicates='drop')
            rfm['m_score'] = pd.qcut(rfm['monetary'], q=4, labels=[1, 2, 3, 4], duplicates='drop')
        except:
            rfm['r_score'] = pd.cut(rfm['recency'], bins=[-1, 30, 90, 180, float('inf')], labels=[4, 3, 2, 1])
            rfm['f_score'] = pd.cut(rfm['frequency'], bins=[0, 3, 6, 12, float('inf')], labels=[1, 2, 3, 4])
            rfm['m_score'] = pd.cut(rfm['monetary'], bins=[-1, 100, 500, 1000, float('inf')], labels=[1, 2, 3, 4])
        
        rfm['r_score'] = pd.to_numeric(rfm['r_score'], errors='coerce').fillna(2).astype(int)
        rfm['f_score'] = pd.to_numeric(rfm['f_score'], errors='coerce').fillna(2).astype(int)
        rfm['m_score'] = pd.to_numeric(rfm['m_score'], errors='coerce').fillna(2).astype(int)
        rfm['r_score'] = rfm['r_score'].clip(1, 4)
        rfm['f_score'] = rfm['f_score'].clip(1, 4)
        rfm['m_score'] = rfm['m_score'].clip(1, 4)
        
        rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
        
        def get_segment(row):
            r, f, m = row['r_score'], row['f_score'], row['m_score']
            if r >= 3 and f >= 3 and m >= 3:
                return 'VIP'
            elif r >= 3 and f >= 2:
                return 'نشط'
            elif r <= 2 and f >= 3:
                return 'مخلص'
            elif r <= 2 and f <= 2:
                return 'خطر'
            else:
                return 'متوسط'
        
        rfm['segment'] = rfm.apply(get_segment, axis=1)
        return rfm
        
    except Exception as e:
        print(f"❌ خطأ في RFM: {e}")
        return pd.DataFrame()

# ============ تحميل البيانات عند بدء التطبيق ============
print("\n" + "=" * 60)
print("🚀 بدء تشغيل لوحة تحليل المبيعات")
print("=" * 60)

# تحميل البيانات
orders_df, customers_df = load_data()

# التأكد من وجود أعمدة customer_id
if orders_df is not None:
    if 'customer_id' not in orders_df.columns and 'CustomerID' in orders_df.columns:
        orders_df = orders_df.rename(columns={'CustomerID': 'customer_id'})
    elif 'customer_id' not in orders_df.columns and 'cust_id' in orders_df.columns:
        orders_df = orders_df.rename(columns={'cust_id': 'customer_id'})
    
    # التأكد من وجود عمود المبلغ
    if 'amount' not in orders_df.columns and 'Amount' in orders_df.columns:
        orders_df = orders_df.rename(columns={'Amount': 'amount'})
    elif 'amount' not in orders_df.columns and 'revenue' in orders_df.columns:
        orders_df = orders_df.rename(columns={'revenue': 'amount'})
    
    # التأكد من وجود عمود التاريخ
    if 'order_date' not in orders_df.columns and 'OrderDate' in orders_df.columns:
        orders_df = orders_df.rename(columns={'OrderDate': 'order_date'})
    elif 'order_date' not in orders_df.columns and 'date' in orders_df.columns:
        orders_df = orders_df.rename(columns={'date': 'order_date'})
    
    # التأكد من وجود عمود order_id
    if 'order_id' not in orders_df.columns:
        orders_df['order_id'] = [f'ORD_{i}' for i in range(len(orders_df))]
    
    print(f"\n📊 أعمدة بيانات الطلبات: {list(orders_df.columns)}")
    print(f"   - عدد الصفوف: {len(orders_df)}")
    print(f"   - عدد العملاء: {orders_df['customer_id'].nunique() if 'customer_id' in orders_df.columns else 'غير محدد'}")

# دمج البيانات
try:
    if orders_df is not None and customers_df is not None and 'customer_id' in orders_df.columns:
        if 'customer_id' in customers_df.columns:
            data = orders_df.merge(customers_df[['customer_id', 'customer_name', 'city']], 
                                   on='customer_id', how='left')
        else:
            data = orders_df
        print(f"✅ تم دمج البيانات: {len(data)} صف")
    else:
        data = orders_df if orders_df is not None else pd.DataFrame()
        print(f"✅ استخدام بيانات الطلبات فقط: {len(data)} صف")
except Exception as e:
    print(f"⚠️ خطأ في دمج البيانات: {e}")
    data = orders_df if orders_df is not None else pd.DataFrame()

print("=" * 60)

# ============ Routes ============

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html', 
                          total_orders=len(data) if data is not None else 0,
                          total_customers=customers_df['customer_id'].nunique() if customers_df is not None else 0)

@app.route('/dashboard')
def dashboard():
    """لوحة التحكم الرئيسية"""
    return render_template('dashboard.html')

@app.route('/rfm')
def rfm_page():
    """صفحة تحليل RFM"""
    return render_template('rfm.html')

@app.route('/forecast')
def forecast_page():
    """صفحة التنبؤ"""
    return render_template('forecast.html')

@app.route('/seasonal')
def seasonal_page():
    """صفحة التحليل الموسمي"""
    return render_template('seasonal.html')

# ============ APIs ============

@app.route('/api/files')
def list_files():
    """عرض الملفات المتاحة للتحميل"""
    try:
        files = []
        search_dirs = ['.', 'data', 'data/raw', 'data/processed']
        
        for dir_name in search_dirs:
            path = Path(dir_name)
            if path.exists():
                for file in path.glob('*.csv'):
                    files.append({
                        'name': file.name,
                        'path': str(file),
                        'size': file.stat().st_size,
                        'modified': file.stat().st_mtime
                    })
        
        return jsonify({
            'success': True,
            'files': files,
            'total': len(files)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/data')
def get_data():
    """الحصول على البيانات الخام"""
    try:
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        return jsonify({
            'success': True,
            'data': data.head(100).to_dict('records'),
            'columns': list(data.columns),
            'total_rows': len(data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/customers')
def get_customers():
    """الحصول على بيانات العملاء"""
    try:
        if customers_df is not None:
            return jsonify({
                'success': True,
                'customers': customers_df.to_dict('records'),
                'total_customers': len(customers_df)
            })
        else:
            return jsonify({'success': False, 'error': 'لا توجد بيانات عملاء'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """الحصول على إحصائيات عامة"""
    try:
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        stats = {
            'total_orders': len(data),
            'total_customers': data['customer_id'].nunique() if 'customer_id' in data.columns else 0,
            'total_revenue': float(data['amount'].sum()) if 'amount' in data.columns else 0,
            'avg_order_value': float(data['amount'].mean()) if 'amount' in data.columns else 0,
            'total_cities': customers_df['city'].nunique() if customers_df is not None else 0,
            'date_range': {
                'start': data['order_date'].min() if 'order_date' in data.columns else None,
                'end': data['order_date'].max() if 'order_date' in data.columns else None
            }
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rfm')
def get_rfm():
    """تحليل RFM"""
    try:
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        rfm = calculate_rfm_simple(data)
        
        if rfm.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات كافية لتحليل RFM'})
        
        rfm_data = rfm.head(50).to_dict('records')
        segment_distribution = rfm['segment'].value_counts().to_dict()
        
        # إنشاء رسم بياني
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c', '#95a5a6']
        segment_counts = rfm['segment'].value_counts()
        segment_counts.plot(kind='bar', ax=ax, color=colors[:len(segment_counts)])
        ax.set_title('توزيع شرائح العملاء', fontsize=14)
        ax.set_xlabel('الشريحة')
        ax.set_ylabel('عدد العملاء')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
        
        return jsonify({
            'success': True,
            'rfm': rfm_data,
            'total_customers': len(rfm),
            'segment_distribution': segment_distribution,
            'avg_recency': float(rfm['recency'].mean()),
            'avg_frequency': float(rfm['frequency'].mean()),
            'avg_monetary': float(rfm['monetary'].mean()),
            'plot': plot_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/forecast')
def get_forecast():
    """التنبؤ بالمبيعات"""
    try:
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        days = request.args.get('days', 14, type=int)
        forecast = run_forecast(data, forecast_days=days)
        
        if forecast.empty:
            return jsonify({'success': False, 'error': 'فشل التنبؤ'})
        
        forecast_data = forecast.to_dict('records')
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(forecast['date'], forecast['forecast'], 
                marker='o', linestyle='-', color='#e74c3c', linewidth=2, markersize=8)
        ax.set_title(f'التنبؤ بالمبيعات لـ {days} يوم قادم', fontsize=14)
        ax.set_xlabel('التاريخ')
        ax.set_ylabel('المبيعات المتوقعة')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'days': len(forecast),
            'avg_forecast': float(forecast['forecast'].mean()),
            'total_forecast': float(forecast['forecast'].sum()),
            'plot': plot_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/seasonal')
def get_seasonal():
    """التحليل الموسمي"""
    try:
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        df = data.copy()
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['month'] = df['order_date'].dt.month
        df['year'] = df['order_date'].dt.year
        
        monthly_total = df.groupby('month')['amount'].sum().reset_index()
        monthly_total.columns = ['month', 'total_amount']
        monthly_avg = df.groupby('month')['amount'].mean().reset_index()
        monthly_avg.columns = ['month', 'avg_amount']
        
        best_month = monthly_total.loc[monthly_total['total_amount'].idxmax()]
        
        # إنشاء رسم بياني
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        colors = plt.cm.viridis(monthly_total['total_amount'] / monthly_total['total_amount'].max())
        ax1.bar(monthly_total['month'], monthly_total['total_amount'], color=colors)
        ax1.set_title('إجمالي المبيعات الشهرية', fontsize=14)
        ax1.set_xlabel('الشهر')
        ax1.set_ylabel('إجمالي المبيعات')
        ax1.set_xticks(range(1, 13))
        
        ax2.bar(monthly_avg['month'], monthly_avg['avg_amount'], color='#3498db', alpha=0.7)
        ax2.set_title('متوسط المبيعات الشهرية', fontsize=14)
        ax2.set_xlabel('الشهر')
        ax2.set_ylabel('متوسط المبيعات')
        ax2.set_xticks(range(1, 13))
        
        plt.tight_layout()
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close(fig)
        
        return jsonify({
            'success': True,
            'total_by_month': monthly_total.to_dict('records'),
            'avg_by_month': monthly_avg.to_dict('records'),
            'best_month': int(best_month['month']),
            'best_month_total': float(best_month['total_amount']),
            'total_yearly': float(monthly_total['total_amount'].sum()),
            'avg_monthly': float(monthly_total['total_amount'].mean()),
            'plot': plot_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export')
def export_data():
    """تصدير البيانات"""
    try:
        format_type = request.args.get('format', 'csv')
        export_type = request.args.get('type', 'all')
        
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات'})
        
        if export_type == 'customers':
            data_to_export = customers_df
        elif export_type == 'rfm':
            data_to_export = calculate_rfm_simple(data)
        elif export_type == 'forecast':
            data_to_export = run_forecast(data, forecast_days=14)
        elif export_type == 'seasonal':
            df = data.copy()
            df['order_date'] = pd.to_datetime(df['order_date'])
            df['month'] = df['order_date'].dt.month
            data_to_export = df.groupby('month')['amount'].sum().reset_index()
        else:
            data_to_export = data
        
        if data_to_export is None or data_to_export.empty:
            return jsonify({'success': False, 'error': 'لا توجد بيانات للتصدير'})
        
        if format_type == 'csv':
            return data_to_export.to_csv(index=False), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename={export_type}.csv'
            }
        elif format_type == 'json':
            return jsonify(data_to_export.to_dict('records'))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)