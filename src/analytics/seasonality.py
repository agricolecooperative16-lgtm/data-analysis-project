"""
تحليل الموسمية والاتجاهات
"""

import pandas as pd
import numpy as np
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SeasonalityAnalyzer:
    """تحليل الموسمية في البيانات"""
    
    def analyze_seasonality(self, df, date_col, amount_col):
        """
        تحليل الموسمية الشهرية والأسبوعية
        """
        results = {}
        
        # نسخ البيانات
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])
        
        # إضافة أعمدة مساعدة
        df_copy['month'] = df_copy[date_col].dt.month
        df_copy['month_name'] = df_copy[date_col].dt.strftime('%B')
        df_copy['day_of_week'] = df_copy[date_col].dt.dayofweek
        df_copy['weekday_name'] = df_copy[date_col].dt.strftime('%A')
        df_copy['quarter'] = df_copy[date_col].dt.quarter
        df_copy['year'] = df_copy[date_col].dt.year
        
        # 1. التحليل الشهري
        monthly = df_copy.groupby('month')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
        monthly.columns = ['month', 'total_sales', 'avg_sales', 'transactions']
        monthly['month_name'] = monthly['month'].apply(
            lambda x: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'][x-1]
        )
        results['monthly'] = monthly.to_dict('records')
        
        # 2. التحليل الأسبوعي
        weekly = df_copy.groupby('day_of_week')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
        weekly.columns = ['day', 'total_sales', 'avg_sales', 'transactions']
        weekly['day_name'] = weekly['day'].apply(
            lambda x: ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'][x]
        )
        results['weekly'] = weekly.to_dict('records')
        
        # 3. التحليل الربع سنوي
        quarterly = df_copy.groupby(['year', 'quarter'])[amount_col].agg(['sum', 'mean', 'count']).reset_index()
        quarterly.columns = ['year', 'quarter', 'total_sales', 'avg_sales', 'transactions']
        results['quarterly'] = quarterly.to_dict('records')
        
        # 4. أفضل وأسوأ الشهور
        monthly_sorted = pd.DataFrame(results['monthly']).sort_values('total_sales', ascending=False)
        results['best_month'] = monthly_sorted.iloc[0]['month_name']
        results['worst_month'] = monthly_sorted.iloc[-1]['month_name']
        results['seasonal_pattern'] = 'موسمي' if monthly_sorted['total_sales'].std() > monthly_sorted['total_sales'].mean() * 0.3 else 'غير موسمي'
        
        logger.info("✅ تم تحليل الموسمية بنجاح")
        return results