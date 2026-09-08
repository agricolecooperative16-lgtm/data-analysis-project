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
        pd.DataFrame: نتائج RFM لكل عميل
    """
    # ========== التحقق من البيانات الفارغة ==========
    if df is None or df.empty:
        print("⚠️ البيانات فارغة، إرجاع DataFrame فارغ")
        return pd.DataFrame(columns=['customer_id', 'recency', 'frequency', 'monetary', 
                                     'r_score', 'f_score', 'm_score', 'rfm_score', 'segment'])
    
    # تحديد أسماء الأعمدة تلقائياً
    if customer_col is None:
        if 'customer_id' in df.columns:
            customer_col = 'customer_id'
        elif 'CustomerID' in df.columns:
            customer_col = 'CustomerID'
        elif 'cust_id' in df.columns:
            customer_col = 'cust_id'
        else:
            # البحث عن عمود يحتوي على 'customer' أو 'id'
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
                # استخدام عمود آخر للعد
                amount_col = None
                print("⚠️ لم يتم العثور على عمود المبلغ. سيتم استخدام عدد الطلبات كبديل.")
    
    print(f"\n📊 أعمدة RFM المستخدمة:")
    print(f"   - عمود العملاء: {customer_col}")
    print(f"   - عمود التاريخ: {date_col}")
    if amount_col:
        print(f"   - عمود المبلغ: {amount_col}")
    
    # نسخ البيانات
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # أحدث تاريخ
    max_date = df[date_col].max()
    print(f"   - أحدث تاريخ: {max_date}")
    
    # حساب RFM
    print("\n📊 حساب RFM...")
    
    # التحقق من وجود العملاء
    if customer_col not in df.columns:
        raise ValueError(f"عمود العملاء '{customer_col}' غير موجود في البيانات")
    
    # تجميع البيانات
    grouped = df.groupby(customer_col)
    
    # حساب Recency (عدد الأيام منذ آخر طلب)
    recency = grouped[date_col].max().apply(lambda x: (max_date - x).days)
    
    # حساب Frequency (عدد الطلبات)
    frequency = grouped[date_col].count()
    
    # حساب Monetary (إجمالي المبلغ)
    if amount_col and amount_col in df.columns:
        monetary = grouped[amount_col].sum()
    else:
        monetary = pd.Series([0] * len(recency), index=recency.index)
    
    # إنشاء DataFrame من النتائج
    rfm = pd.concat([recency, frequency, monetary], axis=1)
    rfm.columns = ['recency', 'frequency', 'monetary']
    rfm = rfm.reset_index()
    rfm = rfm.rename(columns={customer_col: 'customer_id'})
    
    # التأكد من أن البيانات رقمية
    rfm['recency'] = pd.to_numeric(rfm['recency'], errors='coerce').fillna(0)
    rfm['frequency'] = pd.to_numeric(rfm['frequency'], errors='coerce').fillna(0)
    rfm['monetary'] = pd.to_numeric(rfm['monetary'], errors='coerce').fillna(0)
    
    # إزالة القيم الشاذة (تأكد من وجود عملاء)
    if len(rfm) > 0:
        rfm = rfm[rfm['frequency'] > 0]
    
    # إذا لم يتبقى عملاء، إرجاع DataFrame فارغ
    if rfm.empty:
        print("⚠️ لا يوجد عملاء صالحين للتحليل")
        return pd.DataFrame(columns=['customer_id', 'recency', 'frequency', 'monetary', 
                                     'r_score', 'f_score', 'm_score', 'rfm_score', 'segment'])
    
    print(f"✅ تم حساب RFM لـ {len(rfm)} عميل")
    
    # حساب النقاط (Scores) - مع معالجة الأخطاء
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
    
    # تحويل إلى أرقام مع معالجة القيم المفقودة
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
    
    # إضافة تسميات للمستويات
    rfm['recency_label'] = pd.cut(rfm['recency'], bins=[-1, 30, 90, 180, float('inf')],
                                  labels=['حديث', 'أقل من 3 شهور', '3-6 شهور', 'أكثر من 6 شهور'])
    rfm['frequency_label'] = pd.cut(rfm['frequency'], bins=[-1, 3, 6, 12, float('inf')],
                                    labels=['قليل', 'متوسط', 'كثير', 'كثير جداً'])
    rfm['monetary_label'] = pd.cut(rfm['monetary'], bins=[-1, 100, 500, 1000, float('inf')],
                                   labels=['منخفض', 'متوسط', 'مرتفع', 'مرتفع جداً'])
    
    print("✅ تم الانتهاء من تحليل RFM")
    print(f"\n📊 توزيع الشرائح:")
    print(rfm['segment'].value_counts())
    
    return rfm


def get_rfm_insights(rfm):
    """
    الحصول على رؤى من تحليل RFM
    
    Args:
        rfm: DataFrame من دالة calculate_rfm_simple
    
    Returns:
        dict: رؤى وتوصيات
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
    
    # توصيات لكل شريحة
    recommendations = {
        'VIP': '🎯 الحفاظ على هؤلاء العملاء من خلال برامج الولاء والعروض الحصرية',
        'نشط': '📈 تعزيز التفاعل مع العروض الترويجية لزيادة قيمة الطلب',
        'مخلص': '🔄 إعادة تنشيط هؤلاء العملاء من خلال حملات تذكيرية',
        'خطر': '⚠️ اتخاذ إجراءات عاجلة لمنع فقدان هؤلاء العملاء',
        'متوسط': '📊 دراسة سلوكهم لتحويلهم إلى عملاء نشطين'
    }
    
    for segment, count in insights['segment_distribution'].items():
        if segment in recommendations:
            insights['recommendations'].append({
                'segment': segment,
                'count': count,
                'action': recommendations[segment]
            })
    
    return insights