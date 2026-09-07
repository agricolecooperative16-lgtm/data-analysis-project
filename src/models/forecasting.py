# إضافة إلى src/models/forecasting.py
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def advanced_forecast(df, date_col='order_date', amount_col='amount', forecast_days=30):
    """
    تنبؤ متقدم باستخدام نماذج متعددة
    """
    # تجهيز البيانات
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # تجميع يومي
    daily = df.groupby(df[date_col].dt.date)[amount_col].sum().reset_index()
    daily.columns = ['date', 'sales']
    daily['date'] = pd.to_datetime(daily['date'])
    
    # إنشاء ميزات الوقت
    daily['day_of_week'] = daily['date'].dt.dayofweek
    daily['month'] = daily['date'].dt.month
    daily['quarter'] = daily['date'].dt.quarter
    daily['day_of_year'] = daily['date'].dt.dayofyear
    
    # ميزات التأخير
    for lag in [1, 7, 14, 30]:
        daily[f'sales_lag_{lag}'] = daily['sales'].shift(lag)
    
    # إزالة القيم المفقودة
    daily = daily.dropna()
    
    # تقسيم البيانات
    train_size = int(len(daily) * 0.8)
    train = daily[:train_size]
    test = daily[train_size:]
    
    # تدريب النماذج
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    results = {}
    for name, model in models.items():
        model.fit(train[['day_of_week', 'month', 'quarter', 'day_of_year', 
                        'sales_lag_1', 'sales_lag_7', 'sales_lag_14']], 
                 train['sales'])
        
        # تقييم على test
        y_pred = model.predict(test[['day_of_week', 'month', 'quarter', 'day_of_year', 
                                    'sales_lag_1', 'sales_lag_7', 'sales_lag_14']])
        
        mae = mean_absolute_error(test['sales'], y_pred)
        rmse = np.sqrt(mean_squared_error(test['sales'], y_pred))
        r2 = r2_score(test['sales'], y_pred)
        
        results[name] = {
            'model': model,
            'mae': mae,
            'rmse': rmse,
            'r2': r2
        }
    
    # أفضل نموذج
    best = min(results.keys(), key=lambda x: results[x]['mae'])
    
    # التنبؤ للمستقبل
    last_date = daily['date'].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
    
    # إنشاء بيانات التنبؤ
    forecast_data = []
    for i, date in enumerate(future_dates):
        forecast_data.append({
            'date': date,
            'day_of_week': date.dayofweek,
            'month': date.month,
            'quarter': date.quarter,
            'day_of_year': date.dayofyear,
            'sales_lag_1': daily['sales'].iloc[-1] if i == 0 else forecast_data[-1]['sales'],
            'sales_lag_7': daily['sales'].iloc[-7] if len(daily) >= 7 else daily['sales'].mean(),
            'sales_lag_14': daily['sales'].iloc[-14] if len(daily) >= 14 else daily['sales'].mean()
        })
    
    forecast_df = pd.DataFrame(forecast_data)
    
    # تطبيق أفضل نموذج
    best_model = results[best]['model']
    forecast_df['forecast'] = best_model.predict(forecast_df[['day_of_week', 'month', 'quarter', 
                                                              'day_of_year', 'sales_lag_1', 
                                                              'sales_lag_7', 'sales_lag_14']])
    
    return forecast_df, results, best