"""
تحليل RFM (Recency, Frequency, Monetary)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RFMAnalyzer:
    """فئة لتحليل RFM"""
    
    def __init__(self, recency_weight: float = 0.4,
                 frequency_weight: float = 0.3,
                 monetary_weight: float = 0.3):
        """
        تهيئة محلل RFM
        
        Args:
            recency_weight: وزن معامل الحداثة
            frequency_weight: وزن معامل التكرار
            monetary_weight: وزن معامل القيمة
        """
        self.recency_weight = recency_weight
        self.frequency_weight = frequency_weight
        self.monetary_weight = monetary_weight
    
    def calculate_rfm(self, df: pd.DataFrame, 
                     customer_id: str,
                     transaction_date: str,
                     amount_col: str) -> pd.DataFrame:
        """
        حساب درجات RFM للعملاء
        """
        # التحقق من وجود الأعمدة
        required_cols = [customer_id, transaction_date, amount_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"الأعمدة التالية مفقودة: {missing_cols}")
        
        # نسخ البيانات
        df_copy = df.copy()
        
        # التأكد من أن التاريخ من نوع datetime
        if not pd.api.types.is_datetime64_any_dtype(df_copy[transaction_date]):
            df_copy[transaction_date] = pd.to_datetime(df_copy[transaction_date])
        
        # أحدث تاريخ
        max_date = df_copy[transaction_date].max()
        
        # حساب RFM
        rfm = df_copy.groupby(customer_id).agg({
            transaction_date: lambda x: (max_date - x.max()).days,
            amount_col: ['count', 'sum']
        }).reset_index()
        
        # إعادة تسمية الأعمدة
        rfm.columns = [customer_id, 'recency', 'frequency', 'monetary']
        
        logger.info(f"تم حساب RFM لـ {len(rfm)} عميل")
        return rfm
    
    def assign_scores(self, rfm_df: pd.DataFrame) -> pd.DataFrame:
        """
        تعيين درجات RFM (من 1 إلى 5)
        """
        df = rfm_df.copy()
        
        # التأكد من عدم وجود قيم صفرية أو سالبة
        df['recency'] = df['recency'].clip(lower=0)
        df['frequency'] = df['frequency'].clip(lower=0)
        df['monetary'] = df['monetary'].clip(lower=0)
        
        # تعيين الدرجات حسب الترتيب
        try:
            df['r_score'] = pd.qcut(df['recency'].rank(method='first'), 
                                   5, labels=[5, 4, 3, 2, 1])
            df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), 
                                   5, labels=[1, 2, 3, 4, 5])
            df['m_score'] = pd.qcut(df['monetary'].rank(method='first'), 
                                   5, labels=[1, 2, 3, 4, 5])
        except ValueError as e:
            logger.warning(f"خطأ في تقسيم الدرجات: {e}. استخدام طريقة بديلة.")
            # طريقة بديلة باستخدام النسب المئوية
            df['r_score'] = pd.cut(df['recency'], 
                                  bins=5, 
                                  labels=[5, 4, 3, 2, 1])
            df['f_score'] = pd.cut(df['frequency'], 
                                  bins=5, 
                                  labels=[1, 2, 3, 4, 5])
            df['m_score'] = pd.cut(df['monetary'], 
                                  bins=5, 
                                  labels=[1, 2, 3, 4, 5])
        
        # تحويل إلى numeric
        df['r_score'] = df['r_score'].astype(int)
        df['f_score'] = df['f_score'].astype(int)
        df['m_score'] = df['m_score'].astype(int)
        
        # حساب الدرجة النهائية
        df['rfm_score'] = (self.recency_weight * df['r_score'] +
                          self.frequency_weight * df['f_score'] +
                          self.monetary_weight * df['m_score'])
        
        logger.info("تم تعيين درجات RFM للعملاء")
        return df
    
    def segment_customers(self, rfm_scores: pd.DataFrame, 
                         segments: Dict[str, List[int]]) -> pd.DataFrame:
        """
        تقسيم العملاء إلى شرائح
        """
        df = rfm_scores.copy()
        
        def get_segment(score: float) -> str:
            for segment, range_score in segments.items():
                min_score, max_score = range_score
                if min_score <= score <= max_score:
                    return segment
            return 'other'
        
        df['segment'] = df['rfm_score'].apply(get_segment)
        
        logger.info(f"تم تقسيم العملاء إلى {len(df['segment'].unique())} شرائح")
        return df
    
    def analyze_rfm(self, df: pd.DataFrame,
                   customer_id: str,
                   transaction_date: str,
                   amount_col: str,
                   segments: Dict[str, List[int]]) -> Dict[str, pd.DataFrame]:
        """
        تحليل RFM كامل
        """
        # حساب RFM
        rfm_df = self.calculate_rfm(df, customer_id, transaction_date, amount_col)
        
        # تعيين الدرجات
        rfm_scores = self.assign_scores(rfm_df)
        
        # تقسيم العملاء
        rfm_segments = self.segment_customers(rfm_scores, segments)
        
        return {
            'rfm_df': rfm_df,
            'rfm_scores': rfm_scores,
            'rfm_segments': rfm_segments
        }