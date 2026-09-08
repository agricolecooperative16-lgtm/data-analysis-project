"""
تحليل RFM - نسخة مستقلة ومضمونة العمل (مُصححة بالكامل)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_rfm_simple(df, customer_col=None, date_col=None, amount_col=None):
    """
    حساب تحليل RFM بشكل بسيط ومضمون
    
    Args:
        df: DataFrame مع بيانات الطلبات
        customer_col: اسم عمود العميل (افتراضي: customer_id)
        date_col: اسم عمود التاريخ (افتراضي: order_date)
        amount_col: اسم عمود المبلغ (افتراضي: amount)
    
    Returns:
        pd.DataFrame: نتائج RFM لكل عميل (أو DataFrame فارغ إذا لم توجد بيانات)
    """
    # ========== التحقق من البيانات الفارغة ==========
    if df is None or df.empty:
        print("⚠️ البيانات فارغة، إرجاع DataFrame فارغ")
        return pd.DataFrame(columns=['customer_id', 'recency', 'frequency', 'monetary', 
                                     'r_score', 'f_score', 'm_score', 'rfm_score', 'segment'])
    
    # ========== تحديد أسماء الأعمدة ==========
    if customer_col is None:
        if 'customer_id' in df.columns:
            customer_col = 'customer_id'
        elif 'CustomerID' in df.columns:
            customer_col = 'CustomerID'
        elif 'cust_id' in df.columns:
            customer_col = 'cust_id'
        else:
            for col in df.columns:
                if 'customer' in col.lower() or 'cust' in col.lower() or 'id' in col.lower():
                    customer_col = col
                    break
            else:
                raise ValueError("لم يتم العثور على عمود العملاء. حدد customer_col يدوياً.")
    
    if date_col is None:
        if 'order_date' in df.columns:
            date_col = 'order_date'
        elif 'OrderDate' in df.columns:
            date_col = 'OrderDate'
        elif 'date' in df.columns:
            date_col = 'date'
        else:
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
            else:
                raise ValueError("لم يتم العثور على عمود التاريخ. حدد date_col يدوياً.")
    
    if amount_col is None:
        if 'amount' in df.columns:
            amount_col = 'amount'
        elif 'Amount' in df.columns:
            amount_col = 'Amount'
        elif 'revenue' in df.columns:
            amount_col = 'revenue'
        else:
            for col in df.columns:
                if 'amount' in col.lower() or 'revenue' in col.lower() or 'price' in col.lower():
                    amount_col = col
                    break
            else:
                amount_col = None
                print("⚠️ لم يتم العثور على عمود المبلغ. سيتم استخدام عدد الطلبات كبديل.")
    
    print(f"\n📊 أعمدة RFM المستخدمة:")
    print(f"   - عمود العملاء: {customer_col}")
    print(f"   - عمود التاريخ: {date_col}")
    if amount_col:
        print(f"   - عمود المبلغ: {amount_col}")
    
    # ========== معالجة البيانات ==========
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # أحدث تاريخ
    max_date = df[date_col].max()
    print(f"   - أحدث تاريخ: {max_date}")
    
    # التحقق من وجود العملاء
    if customer_col not in df.columns:
        raise ValueError(f"عمود العملاء '{customer_col}' غير موجود في البيانات")
    
    # ========== حساب RFM ==========
    print("\n📊 حساب RFM...")
    
    grouped = df.groupby(customer_col)
    
    # Recency
    recency = grouped[date_col].max().apply(lambda x: (max_date - x).days)
    
    # Frequency
    frequency = grouped[date_col].count()
    
    # Monetary
    if amount_col and amount_col in df.columns:
        monetary = grouped[amount_col].sum()
    else:
        monetary = pd.Series([0] * len(recency), index=recency.index)
    
    # إنشاء DataFrame
    rfm = pd.concat([recency, frequency, monetary], axis=1)
    rfm.columns = ['recency', 'frequency', 'monetary']
    rfm = rfm.reset_index()
    rfm = rfm.rename(columns={customer_col: 'customer_id'})
    
    # تنظيف البيانات
    rfm['recency'] = pd.to_numeric(rfm['recency'], errors='coerce').fillna(0)
    rfm['frequency'] = pd.to_numeric(rfm['frequency'], errors='coerce').fillna(0)
    rfm['monetary'] = pd.to_numeric(rfm['monetary'], errors='coerce').fillna(0)
    
    # إزالة العملاء بدون طلبات
    rfm = rfm[rfm['frequency'] > 0]
    
    if rfm.empty:
        print("⚠️ لا يوجد عملاء صالحين للتحليل")
        return pd.DataFrame(columns=['customer_id', 'recency', 'frequency', 'monetary', 
                                     'r_score', 'f_score', 'm_score', 'rfm_score', 'segment'])
    
    print(f"✅ تم حساب RFM لـ {len(rfm)} عميل")
    
    # ========== حساب النقاط ==========
    print("📊 حساب نقاط RFM...")
    
    try:
        rfm['r_score'] = pd.qcut(rfm['recency'], q=4, labels=[4, 3, 2, 1], duplicates='drop')
        rfm['f_score'] = pd.qcut(rfm['frequency'], q=4, labels=[1, 2, 3, 4], duplicates='drop')
        rfm['m_score'] = pd.qcut(rfm['monetary'], q=4, labels=[1, 2, 3, 4], duplicates='drop')
    except Exception as e:
        print(f"⚠️ تحذير في التقسيم الربعي: {e}")
        print("📊 استخدام التقسيم اليدوي...")
        
        rfm['r_score'] = pd.cut(rfm['recency'], bins=[-1, 30, 90, 180, float('inf')], labels=[4, 3, 2, 1])
        rfm['f_score'] = pd.cut(rfm['frequency'], bins=[0, 3, 6, 12, float('inf')], labels=[1, 2, 3, 4])
        rfm['m_score'] = pd.cut(rfm['monetary'], bins=[-1, 100, 500, 1000, float('inf')], labels=[1, 2, 3, 4])
    
    # تحويل إلى أرقام
    rfm['r_score'] = pd.to_numeric(rfm['r_score'], errors='coerce').fillna(2).astype(int)
    rfm['f_score'] = pd.to_numeric(rfm['f_score'], errors='coerce').fillna(2).astype(int)
    rfm['m_score'] = pd.to_numeric(rfm['m_score'], errors='coerce').fillna(2).astype(int)
    rfm['r_score'] = rfm['r_score'].clip(1, 4)
    rfm['f_score'] = rfm['f_score'].clip(1, 4)
    rfm['m_score'] = rfm['m_score'].clip(1, 4)
    
    # RFM Score
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # ========== تقسيم العملاء (النسخة المحسنة) ==========
    def get_segment(row):
        """
        تقسيم العملاء بناءً على تركيبة R/F/M الفعلية
        """
        r, f, m = row['r_score'], row['f_score'], row['m_score']
        
        # أفضل العملاء (Champions)
        if r >= 4 and f >= 4 and m >= 3:
            return '🏆 Champions'
        
        # العملاء المخلصون (Loyal Customers)
        if r >= 3 and f >= 4:
            return '❤️ Loyal Customers'
        
        # العملاء الجدد (New Customers)
        if r >= 4 and f <= 2:
            return '🌟 New Customers'
        
        # العملاء المعرضون للخطر (At Risk)
        if r <= 2 and f >= 3 and m >= 3:
            return '⚠️ At Risk'
        
        # العملاء المفقودون (Lost)
        if r <= 2 and f <= 2 and m <= 2:
            return '💔 Lost'
        
        # العملاء النشطون (Active)
        if r >= 3 and f >= 3:
            return '✅ Active'
        
        # العملاء العاديون (Average)
        return '📊 Average'
    
    rfm['segment'] = rfm.apply(get_segment, axis=1)
    
    # ========== تسميات إضافية ==========
    try:
        rfm['recency_label'] = pd.cut(rfm['recency'], bins=[-1, 30, 90, 180, float('inf')],
                                      labels=['حديث', 'أقل من 3 شهور', '3-6 شهور', 'أكثر من 6 شهور'])
        rfm['frequency_label'] = pd.cut(rfm['frequency'], bins=[-1, 3, 6, 12, float('inf')],
                                        labels=['قليل', 'متوسط', 'كثير', 'كثير جداً'])
        rfm['monetary_label'] = pd.cut(rfm['monetary'], bins=[-1, 100, 500, 1000, float('inf')],
                                       labels=['منخفض', 'متوسط', 'مرتفع', 'مرتفع جداً'])
    except:
        pass
    
    print("✅ تم الانتهاء من تحليل RFM")
    print(f"\n📊 توزيع الشرائح:")
    print(rfm['segment'].value_counts())
    
    return rfm


def get_rfm_insights(rfm):
    """
    الحصول على رؤى من تحليل RFM
    """
    if rfm is None or rfm.empty:
        return {
            'total_customers': 0,
            'avg_recency': 0,
            'avg_frequency': 0,
            'avg_monetary': 0,
            'segment_distribution': {},
            'recommendations': []
        }
    
    insights = {
        'total_customers': len(rfm),
        'avg_recency': rfm['recency'].mean(),
        'avg_frequency': rfm['frequency'].mean(),
        'avg_monetary': rfm['monetary'].mean(),
        'segment_distribution': rfm['segment'].value_counts().to_dict(),
        'recommendations': []
    }
    
    recommendations = {
        '🏆 Champions': '🎯 الحفاظ على هؤلاء العملاء من خلال برامج الولاء والعروض الحصرية',
        '❤️ Loyal Customers': '📈 تعزيز التفاعل مع العروض الترويجية لزيادة قيمة الطلب',
        '🌟 New Customers': '🤝 حملات ترحيبية وعروض للشراء الثاني',
        '⚠️ At Risk': '📞 حملات استعادة وعروض خاصة وتواصل شخصي',
        '💔 Lost': '🔄 حملات إعادة جذب وعروض استثنائية',
        '✅ Active': '📊 عروض ترويجية منتظمة وتحديثات مستمرة',
        '📊 Average': '🔍 دراسة السلوك ومحاولة رفع القيمة'
    }
    
    for segment, count in insights['segment_distribution'].items():
        if segment in recommendations:
            insights['recommendations'].append({
                'segment': segment,
                'count': count,
                'action': recommendations[segment]
            })
    
    return insights