import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_clv(df: pd.DataFrame,
                  customer_col: str,
                  revenue_col: str,
                  date_col: str,
                  method: str = 'historical') -> pd.DataFrame:
    """
    حساب القيمة الدائمة للعميل (CLV) باستخدام المنهجية الصحيحة
    
    Args:
        df: DataFrame مع بيانات العملاء
        customer_col: اسم عمود معرف العميل
        revenue_col: اسم عمود الإيرادات
        date_col: اسم عمود التاريخ
        method: طريقة الحساب ('historical', 'predictive', 'simple')
    
    Returns:
        pd.DataFrame: CLV لكل عميل
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    if method == 'historical':
        # الطريقة التاريخية: إجمالي الإيرادات حتى الآن
        clv = df.groupby(customer_col)[revenue_col].sum().reset_index()
        clv.columns = [customer_col, 'clv_historical']
        clv['clv_method'] = 'historical'
        
    elif method == 'simple':
        # الطريقة المبسطة: متوسط القيمة × عدد المعاملات
        customer_stats = df.groupby(customer_col).agg({
            revenue_col: ['mean', 'sum', 'count'],
            date_col: ['min', 'max']
        })
        
        # حساب العمر الافتراضي للعميل
        customer_stats[('date_col', 'lifetime_days')] = (
            customer_stats[('date_col', 'max')] - 
            customer_stats[('date_col', 'min')]
        ).dt.days
        
        # CLV = متوسط الإيرادات × عدد المعاملات
        clv = pd.DataFrame({
            customer_col: customer_stats.index,
            'avg_order_value': customer_stats[(revenue_col, 'mean')].fillna(0),
            'purchase_frequency': customer_stats[(revenue_col, 'count')].fillna(0),
            'lifetime_days': customer_stats[('date_col', 'lifetime_days')].fillna(0),
            'clv_simple': customer_stats[(revenue_col, 'mean')].fillna(0) * 
                         customer_stats[(revenue_col, 'count')].fillna(0)
        })
        clv['clv_method'] = 'simple'
        
    elif method == 'predictive':
        # الطريقة التنبؤية (نموذج مبسط)
        # CLV = (متوسط قيمة الطلب × عدد الطلبات في السنة) × متوسط عمر العميل
        
        today = datetime.now()
        
        customer_stats = df.groupby(customer_col).agg({
            revenue_col: ['mean', 'sum', 'count'],
            date_col: ['min', 'max']
        })
        
        # حساب متوسط عمر العميل (بالسنوات)
        customer_stats[('date_col', 'lifetime_years')] = (
            (customer_stats[('date_col', 'max')] - 
             customer_stats[('date_col', 'min')]).dt.days / 365.25
        )
        
        # حساب عدد المعاملات في السنة
        customer_stats[('date_col', 'years')] = (
            (today - customer_stats[('date_col', 'min')]).dt.days / 365.25
        )
        
        # تجنب القسمة على صفر
        years = customer_stats[('date_col', 'years')].replace(0, 1)
        annual_transactions = customer_stats[(revenue_col, 'count')] / years
        
        # CLV التنبؤي
        clv = pd.DataFrame({
            customer_col: customer_stats.index,
            'avg_order_value': customer_stats[(revenue_col, 'mean')].fillna(0),
            'annual_transactions': annual_transactions.fillna(0),
            'avg_customer_lifetime_years': customer_stats[('date_col', 'lifetime_years')].fillna(0),
            'clv_predictive': customer_stats[(revenue_col, 'mean')].fillna(0) * 
                             annual_transactions.fillna(0) * 
                             customer_stats[('date_col', 'lifetime_years')].fillna(1)
        })
        clv['clv_method'] = 'predictive'
    
    else:
        raise ValueError(f"طريقة غير مدعومة: {method}. استخدم 'historical', 'simple', أو 'predictive'")
    
    return clv


def segment_customers_by_clv(clv_df: pd.DataFrame,
                             clv_col: str,
                             n_segments: int = 4) -> pd.DataFrame:
    """
    تقسيم العملاء حسب CLV
    
    Args:
        clv_df: DataFrame مع CLV لكل عميل
        clv_col: اسم عمود CLV
        n_segments: عدد الشرائح
    
    Returns:
        pd.DataFrame: العملاء مع تصنيف الشريحة
    """
    df = clv_df.copy()
    
    # استخدام التقسيم بناءً على الربعيات
    labels = ['منخفض', 'متوسط', 'مرتفع', 'VIP']
    if n_segments > len(labels):
        labels = [f'شريحة {i+1}' for i in range(n_segments)]
    
    df['clv_segment'] = pd.qcut(df[clv_col], 
                                q=n_segments, 
                                labels=labels[:n_segments])
    
    return df