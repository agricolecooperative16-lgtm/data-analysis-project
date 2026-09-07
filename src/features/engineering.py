import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_time_features(df: pd.DataFrame,
                         date_col: str) -> pd.DataFrame:
    """
    إنشاء ميزات الوقت من عمود التاريخ
    
    Args:
        df: DataFrame
        date_col: اسم عمود التاريخ
    
    Returns:
        pd.DataFrame: DataFrame مع ميزات الوقت المضافة
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # ميزات الوقت الأساسية
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['quarter'] = df[date_col].dt.quarter
    df['day_of_week'] = df[date_col].dt.dayofweek
    df['day_of_month'] = df[date_col].dt.day
    df['week_of_year'] = df[date_col].dt.isocalendar().week
    
    # ميزات موسمية
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_month_start'] = (df[date_col].dt.is_month_start).astype(int)
    df['is_month_end'] = (df[date_col].dt.is_month_end).astype(int)
    df['is_quarter_start'] = (df[date_col].dt.is_quarter_start).astype(int)
    df['is_quarter_end'] = (df[date_col].dt.is_quarter_end).astype(int)
    
    # دورات جيبية للالتقاط الأنماط الموسمية
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    return df


def create_lag_features(df: pd.DataFrame,
                        target_col: str,
                        group_col: str,
                        date_col: str,
                        lags: list = None) -> pd.DataFrame:
    """
    إنشاء ميزات التأخير (Lag Features) للتنبؤ
    
    Args:
        df: DataFrame
        target_col: العمود المستهدف
        group_col: عمود التجميع
        date_col: عمود التاريخ
        lags: قائمة فترات التأخير
    
    Returns:
        pd.DataFrame: DataFrame مع ميزات التأخير
    """
    if lags is None:
        lags = [1, 2, 3, 7, 14, 30]
    
    df = df.copy()
    df = df.sort_values([group_col, date_col])
    
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df.groupby(group_col)[target_col].shift(lag)
    
    return df


def create_rolling_features(df: pd.DataFrame,
                            target_col: str,
                            group_col: str,
                            date_col: str,
                            windows: list = None) -> pd.DataFrame:
    """
    إنشاء ميزات المتوسطات المتحركة
    
    Args:
        df: DataFrame
        target_col: العمود المستهدف
        group_col: عمود التجميع
        date_col: عمود التاريخ
        windows: قائمة أحجام النوافذ
    
    Returns:
        pd.DataFrame: DataFrame مع الميزات المتحركة
    """
    if windows is None:
        windows = [3, 7, 14, 30]
    
    df = df.copy()
    df = df.sort_values([group_col, date_col])
    
    for window in windows:
        df[f'{target_col}_rolling_{window}_mean'] = (
            df.groupby(group_col)[target_col].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
        )
        df[f'{target_col}_rolling_{window}_std'] = (
            df.groupby(group_col)[target_col].transform(
                lambda x: x.rolling(window, min_periods=1).std()
            )
        )
    
    return df