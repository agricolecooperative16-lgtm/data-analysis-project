import pandas as pd
import numpy as np

def calculate_retention_rate(df: pd.DataFrame, 
                             customer_col: str, 
                             date_col: str,
                             periods: list = None) -> pd.DataFrame:
    """
    حساب معدل الاحتفاظ بالعملاء بشكل صحيح
    
    Args:
        df: DataFrame مع بيانات العملاء
        customer_col: اسم عمود معرف العميل
        date_col: اسم عمود التاريخ
        periods: قائمة الفترات (مثل ['month', 'week'])
    
    Returns:
        pd.DataFrame: جدول الاحتفاظ لكل فترة
    """
    if periods is None:
        periods = ['month']
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    results = {}
    
    for period in periods:
        # إضافة عمود الفترة
        if period == 'month':
            df['period'] = df[date_col].dt.to_period('M')
        elif period == 'week':
            df['period'] = df[date_col].dt.to_period('W')
        elif period == 'quarter':
            df['period'] = df[date_col].dt.to_period('Q')
        else:
            raise ValueError(f"فترة غير مدعومة: {period}")
        
        # حساب العملاء النشطين لكل فترة
        active_customers = df.groupby('period')[customer_col].nunique()
        
        # حساب الاحتفاظ (نسبة العملاء الذين عادوا)
        periods_sorted = sorted(active_customers.index)
        retention_matrix = pd.DataFrame(index=periods_sorted, columns=periods_sorted)
        
        for i, p1 in enumerate(periods_sorted):
            for j, p2 in enumerate(periods_sorted):
                if i <= j:  # فقط الفترات الحالية والمستقبلية
                    # العملاء في p1 الذين عادوا في p2
                    customers_p1 = set(df[df['period'] == p1][customer_col].unique())
                    customers_p2 = set(df[df['period'] == p2][customer_col].unique())
                    
                    if len(customers_p1) > 0:
                        retention = len(customers_p1.intersection(customers_p2)) / len(customers_p1)
                    else:
                        retention = 0
                    
                    retention_matrix.loc[p1, p2] = retention
        
        results[period] = retention_matrix
    
    return results if len(periods) > 1 else results[periods[0]]


def calculate_retention_rate_by_cohort(df: pd.DataFrame,
                                        customer_col: str,
                                        date_col: str,
                                        order_col: str = None) -> pd.DataFrame:
    """
    حساب معدل الاحتفاظ حسب المجموعات (Cohort Analysis)
    
    Args:
        df: DataFrame مع بيانات العملاء
        customer_col: اسم عمود معرف العميل
        date_col: اسم عمود التاريخ
        order_col: اسم عمود رقم الطلب (اختياري)
    
    Returns:
        pd.DataFrame: جدول الاحتفاظ حسب المجموعات
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # تحديد تاريخ أول عملية لكل عميل
    first_purchase = df.groupby(customer_col)[date_col].min().reset_index()
    first_purchase.columns = [customer_col, 'first_purchase']
    
    # دمج مع البيانات الأصلية
    df = df.merge(first_purchase, on=customer_col)
    
    # حساب الفرق بالأشهر
    df['months_diff'] = (df[date_col].dt.year - df['first_purchase'].dt.year) * 12 + \
                        (df[date_col].dt.month - df['first_purchase'].dt.month)
    
    # إنشاء جدول المجموعات
    cohort_data = df.groupby([customer_col, 'months_diff']).size().reset_index(name='count')
    
    # حساب عدد العملاء لكل مجموعة
    cohort_sizes = df.groupby(customer_col)['first_purchase'].min().reset_index()
    cohort_sizes['cohort'] = cohort_sizes['first_purchase'].dt.to_period('M')
    
    # حساب الاحتفاظ
    retention = cohort_data.pivot_table(index=customer_col, 
                                        columns='months_diff', 
                                        values='count', 
                                        fill_value=0)
    
    # إضافة معلومات المجموعة
    retention = retention.merge(cohort_sizes[[customer_col, 'cohort']], 
                                on=customer_col)
    
    # حساب النسب المئوية
    retention_pct = retention.groupby('cohort').mean() * 100
    
    return retention_pct