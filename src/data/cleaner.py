"""
تنظيف ومعالجة البيانات
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Union
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataCleaner:
    """فئة لتنظيف ومعالجة البيانات"""
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, 
                             strategy: str = 'drop',
                             columns: Optional[List[str]] = None,
                             fill_value: Optional[Union[str, int, float]] = None) -> pd.DataFrame:
        """
        معالجة القيم المفقودة
        
        Args:
            df: DataFrame المراد معالجته
            strategy: استراتيجية المعالجة ('drop', 'fill', 'mean', 'median', 'mode')
            columns: الأعمدة المراد معالجتها (None للكل)
            fill_value: قيمة التعبئة (في حالة strategy='fill')
        
        Returns:
            DataFrame بعد المعالجة
        """
        df_copy = df.copy()
        columns = columns or df_copy.columns
        
        for col in columns:
            if df_copy[col].isnull().sum() == 0:
                continue
            
            missing_count = df_copy[col].isnull().sum()
            logger.info(f"معالجة القيم المفقودة في عمود {col}: {missing_count} قيمة")
            
            if strategy == 'drop':
                df_copy = df_copy.dropna(subset=[col])
            elif strategy == 'mean':
                df_copy[col] = df_copy[col].fillna(df_copy[col].mean())
            elif strategy == 'median':
                df_copy[col] = df_copy[col].fillna(df_copy[col].median())
            elif strategy == 'mode':
                df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])
            elif strategy == 'fill':
                if fill_value is None:
                    raise ValueError("يجب تحديد قيمة للتعبئة عند استخدام strategy='fill'")
                df_copy[col] = df_copy[col].fillna(fill_value)
        
        return df_copy
    
    @staticmethod
    def convert_dates(df: pd.DataFrame, date_col: str, 
                      format: Optional[str] = None) -> pd.DataFrame:
        """
        تحويل عمود إلى نوع التاريخ
        
        Args:
            df: DataFrame المراد معالجته
            date_col: اسم عمود التاريخ
            format: صيغة التاريخ (اختياري)
        
        Returns:
            DataFrame مع عمود التاريخ المحول
        """
        if date_col not in df.columns:
            raise ValueError(f"العمود {date_col} غير موجود")
        
        df_copy = df.copy()
        
        try:
            if format:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], format=format)
            else:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            
            logger.info(f"تم تحويل {date_col} إلى نوع datetime بنجاح")
            return df_copy
        except Exception as e:
            logger.error(f"خطأ في تحويل التاريخ: {str(e)}")
            raise
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, 
                         subset: Optional[List[str]] = None,
                         keep: str = 'first') -> pd.DataFrame:
        """
        إزالة البيانات المكررة
        
        Args:
            df: DataFrame المراد معالجته
            subset: الأعمدة المستخدمة لتحديد التكرار
            keep: أي نسخة للاحتفاظ ('first', 'last', False)
        
        Returns:
            DataFrame بعد إزالة المكررات
        """
        df_copy = df.copy()
        initial_len = len(df_copy)
        df_copy = df_copy.drop_duplicates(subset=subset, keep=keep)
        removed = initial_len - len(df_copy)
        
        if removed > 0:
            logger.info(f"تم إزالة {removed} سجل مكرر")
        
        return df_copy
    
    @staticmethod
    def filter_outliers(df: pd.DataFrame, col: str, 
                        method: str = 'iqr',
                        threshold: float = 1.5) -> pd.DataFrame:
        """
        تصفية القيم الشاذة
        
        Args:
            df: DataFrame المراد معالجته
            col: اسم العمود المراد تصفية قيمه
            method: طريقة التصفية ('iqr', 'zscore')
            threshold: العتبة المستخدمة
        
        Returns:
            DataFrame بعد تصفية القيم الشاذة
        """
        if col not in df.columns:
            raise ValueError(f"العمود {col} غير موجود")
        
        df_copy = df.copy()
        initial_len = len(df_copy)
        
        if method == 'iqr':
            Q1 = df_copy[col].quantile(0.25)
            Q3 = df_copy[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_copy = df_copy[(df_copy[col] >= lower_bound) & 
                             (df_copy[col] <= upper_bound)]
        
        elif method == 'zscore':
            mean = df_copy[col].mean()
            std = df_copy[col].std()
            df_copy = df_copy[abs((df_copy[col] - mean) / std) <= threshold]
        
        else:
            raise ValueError(f"الطريقة غير معروفة: {method}")
        
        removed = initial_len - len(df_copy)
        if removed > 0:
            logger.info(f"تمت إزالة {removed} قيمة شاذة من عمود {col}")
        
        return df_copy
    
    @staticmethod
    def calculate_total_amount(df: pd.DataFrame, 
                              quantity_col: str,
                              price_col: str,
                              new_col: str = 'total_amount') -> pd.DataFrame:
        """
        حساب المبلغ الإجمالي
        
        Args:
            df: DataFrame المراد معالجته
            quantity_col: اسم عمود الكمية
            price_col: اسم عمود السعر
            new_col: اسم العمود الجديد
        
        Returns:
            DataFrame مع العمود الجديد
        """
        if quantity_col not in df.columns or price_col not in df.columns:
            raise ValueError(f"الأعمدة {quantity_col} أو {price_col} غير موجودة")
        
        df_copy = df.copy()
        df_copy[new_col] = df_copy[quantity_col] * df_copy[price_col]
        logger.info(f"تم حساب العمود {new_col}")
        
        return df_copy