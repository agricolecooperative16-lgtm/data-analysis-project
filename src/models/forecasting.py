"""
نماذج التنبؤ بالمبيعات
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import PolynomialFeatures
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SalesForecaster:
    """فئة للتنبؤ بالمبيعات"""
    
    def __init__(self, test_size=0.2):
        self.test_size = test_size
        self.models = {}
        self.results = {}
    
    def prepare_data(self, df, date_col, amount_col):
        """تجهيز البيانات للتنبؤ"""
        # تجميع حسب التاريخ
        daily_sales = df.groupby(date_col)[amount_col].sum().reset_index()
        daily_sales = daily_sales.sort_values(date_col)
        daily_sales['day_index'] = range(len(daily_sales))
        
        # تقسيم البيانات
        split_idx = int(len(daily_sales) * (1 - self.test_size))
        train = daily_sales[:split_idx]
        test = daily_sales[split_idx:]
        
        return train, test
    
    def forecast_linear(self, train, test):
        """التنبؤ باستخدام الانحدار الخطي"""
        # إعداد البيانات
        X_train = train[['day_index']].values
        y_train = train['total_amount'].values
        X_test = test[['day_index']].values
        y_test = test['total_amount'].values
        
        # تدريب النموذج
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # التنبؤ
        predictions = model.predict(X_test)
        
        # حساب الدقة
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        return {
            'model': 'Linear Regression',
            'predictions': predictions.tolist(),
            'actual': y_test.tolist(),
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': model.score(X_test, y_test)
        }
    
    def forecast_polynomial(self, train, test, degree=2):
        """التنبؤ باستخدام الانحدار متعدد الحدود"""
        # إعداد البيانات
        X_train = train[['day_index']].values
        y_train = train['total_amount'].values
        X_test = test[['day_index']].values
        y_test = test['total_amount'].values
        
        # تحويل الخصائص
        poly = PolynomialFeatures(degree=degree)
        X_train_poly = poly.fit_transform(X_train)
        X_test_poly = poly.transform(X_test)
        
        # تدريب النموذج
        model = LinearRegression()
        model.fit(X_train_poly, y_train)
        
        # التنبؤ
        predictions = model.predict(X_test_poly)
        
        # حساب الدقة
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        
        return {
            'model': f'Polynomial (degree={degree})',
            'predictions': predictions.tolist(),
            'actual': y_test.tolist(),
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': model.score(X_test_poly, y_test)
        }
    
    def forecast_all(self, df, date_col, amount_col):
        """تشغيل جميع نماذج التنبؤ"""
        train, test = self.prepare_data(df, date_col, amount_col)
        
        results = {}
        
        # الانحدار الخطي
        logger.info("تشغيل نموذج الانحدار الخطي...")
        results['linear'] = self.forecast_linear(train, test)
        
        # متعدد الحدود (درجة 2)
        logger.info("تشغيل نموذج متعدد الحدود (degree=2)...")
        results['polynomial'] = self.forecast_polynomial(train, test, degree=2)
        
        # متعدد الحدود (درجة 3)
        logger.info("تشغيل نموذج متعدد الحدود (degree=3)...")
        results['polynomial_3'] = self.forecast_polynomial(train, test, degree=3)
        
        # اختيار أفضل نموذج (أقل MAE)
        best_model = min(results.keys(), key=lambda x: results[x]['mae'])
        results['best_model'] = best_model
        
        # إضافة بيانات التدريب والاختبار للرسم
        results['train_data'] = train[['day_index', 'total_amount']].to_dict('records')
        results['test_data'] = test[['day_index', 'total_amount']].to_dict('records')
        
        return results