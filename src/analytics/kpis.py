"""
حساب مؤشرات الأداء الرئيسية (KPIs)
"""

import pandas as pd
import numpy as np
from typing import Dict, Union, Optional
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class KPIAnalyzer:
    """فئة لحساب مؤشرات الأداء"""
    
    @staticmethod
    def calculate_revenue(df: pd.DataFrame, amount_col: str) -> float:
        """
        حساب إجمالي الإيرادات
        
        Args:
            df: DataFrame مع بيانات المبيعات
            amount_col: اسم عمود المبلغ
        
        Returns:
            float: إجمالي الإيرادات
        """
        return df[amount_col].sum()
    
    @staticmethod
    def calculate_average_basket(df: pd.DataFrame, 
                                 amount_col: str,
                                 transaction_id: str) -> float:
        """
        حساب متوسط قيمة السلة
        
        Args:
            df: DataFrame مع بيانات المبيعات
            amount_col: اسم عمود المبلغ
            transaction_id: اسم عمود معرف المعاملة
        
        Returns:
            float: متوسط قيمة السلة
        """
        total_revenue = df[amount_col].sum()
        total_transactions = df[transaction_id].nunique()
        
        if total_transactions == 0:
            return 0.0
        
        return total_revenue / total_transactions
    
    @staticmethod
    def calculate_customer_lifetime_value(df: pd.DataFrame,
                                         customer_id: str,
                                         amount_col: str) -> pd.DataFrame:
        """
        حساب قيمة العميل الدائمة (CLV)
        
        Args:
            df: DataFrame مع بيانات المبيعات
            customer_id: اسم عمود معرف العميل
            amount_col: اسم عمود المبلغ
        
        Returns:
            DataFrame مع CLV لكل عميل
        """
        clv = df.groupby(customer_id)[amount_col].sum().reset_index()
        clv.columns = [customer_id, 'clv']
        return clv
    
    @staticmethod
    def calculate_retention_rate(df: pd.DataFrame,
                                 customer_id: str,
                                 date_col: str,
                                 period: str = 'M') -> float:
        """
        حساب معدل الاحتفاظ بالعملاء
        
        Args:
            df: DataFrame مع بيانات المبيعات
            customer_id: اسم عمود معرف العميل
            date_col: اسم عمود التاريخ
            period: الفترة الزمنية ('D', 'W', 'M', 'Q', 'Y')
        
        Returns:
            float: معدل الاحتفاظ
        """
        # التأكد من أن التاريخ من نوع datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col])
        
        # إضافة عمود الفترة
        df['period'] = df[date_col].dt.to_period(period)
        
        # حساب العملاء النشطين في كل فترة
        active_customers = df.groupby('period')[customer_id].nunique()
        
        # معدل الاحتفاظ
        retention_rates = active_customers.pct_change().fillna(0)
        
        # متوسط معدل الاحتفاظ
        avg_retention = retention_rates.mean()
        
        return avg_retention
    
    @staticmethod
    def calculate_all_kpis(df: pd.DataFrame,
                          customer_id: str,
                          transaction_id: str,
                          date_col: str,
                          amount_col: str) -> Dict[str, Union[float, int, pd.DataFrame]]:
        """
        حساب جميع مؤشرات الأداء
        
        Returns:
            قاموس يحتوي على جميع الـ KPIs
        """
        kpis = {}
        
        # الإيرادات
        kpis['total_revenue'] = KPIAnalyzer.calculate_revenue(df, amount_col)
        
        # متوسط السلة
        kpis['average_basket'] = KPIAnalyzer.calculate_average_basket(
            df, amount_col, transaction_id
        )
        
        # عدد العملاء الفريدين
        kpis['unique_customers'] = df[customer_id].nunique()
        
        # عدد المعاملات
        kpis['total_transactions'] = df[transaction_id].nunique()
        
        # متوسط قيمة العميل
        if kpis['unique_customers'] > 0:
            kpis['avg_customer_value'] = kpis['total_revenue'] / kpis['unique_customers']
        else:
            kpis['avg_customer_value'] = 0
        
        # قيمة العميل الدائمة
        kpis['customer_lifetime_value'] = KPIAnalyzer.calculate_customer_lifetime_value(
            df, customer_id, amount_col
        )
        
        # معدل الاحتفاظ
        kpis['retention_rate'] = KPIAnalyzer.calculate_retention_rate(
            df, customer_id, date_col
        )
        
        logger.info("تم حساب جميع مؤشرات الأداء بنجاح")
        return kpis