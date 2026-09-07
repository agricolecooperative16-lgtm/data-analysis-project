import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

def detect_trend(df: pd.DataFrame,
                 value_col: str,
                 date_col: str,
                 method: str = 'linear') -> dict:
    """
    اكتشاف الاتجاهات في البيانات
    
    Args:
        df: DataFrame
        value_col: عمود القيم
        date_col: عمود التاريخ
        method: طريقة الكشف ('linear', 'mann_kendall', 'both')
    
    Returns:
        dict: نتائج تحليل الاتجاه
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    
    results = {
        'trend_direction': None,
        'trend_strength': None,
        'p_value': None,
        'slope': None,
        'intercept': None
    }
    
    if method in ['linear', 'both']:
        # الاتجاه الخطي
        x = np.arange(len(df)).reshape(-1, 1)
        y = df[value_col].values
        
        model = LinearRegression()
        model.fit(x, y)
        
        results['slope'] = model.coef_[0]
        results['intercept'] = model.intercept_
        results['r2_score'] = model.score(x, y)
        
        # تحديد اتجاه الاتجاه
        if results['slope'] > 0.01:
            results['trend_direction'] = 'صاعد'
        elif results['slope'] < -0.01:
            results['trend_direction'] = 'هابط'
        else:
            results['trend_direction'] = 'ثابت'
    
    if method in ['mann_kendall', 'both']:
        # اختبار مان-كيندال للاتجاه
        n = len(df)
        s = 0
        for i in range(n-1):
            for j in range(i+1, n):
                s += np.sign(df[value_col].iloc[j] - df[value_col].iloc[i])
        
        # حساب التباين
        var_s = n * (n-1) * (2*n + 5) / 18
        z = s / np.sqrt(var_s) if var_s > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        results['mann_kendall_s'] = s
        results['mann_kendall_z'] = z
        results['p_value'] = p_value
        results['significant'] = p_value < 0.05
    
    # قوة الاتجاه
    if results.get('r2_score') is not None:
        if results['r2_score'] > 0.7:
            results['trend_strength'] = 'قوي'
        elif results['r2_score'] > 0.4:
            results['trend_strength'] = 'متوسط'
        else:
            results['trend_strength'] = 'ضعيف'
    
    return results


def decompose_trend(df: pd.DataFrame,
                    value_col: str,
                    date_col: str,
                    period: int = 12) -> dict:
    """
    تحليل الاتجاه إلى مكونات (الاتجاه، الموسمية، الباقي)
    """
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    
    # التحليل الموسمي
    decomposition = seasonal_decompose(df[value_col], period=period, model='additive')
    
    return {
        'trend': decomposition.trend,
        'seasonal': decomposition.seasonal,
        'residual': decomposition.resid,
        'observed': decomposition.observed
    }