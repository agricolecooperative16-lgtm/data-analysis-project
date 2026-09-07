#!/usr/bin/env python
"""
سكريبت لتوليد بيانات نموذجية
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_data(n_customers=100, n_orders=1000):
    """توليد بيانات نموذجية"""
    
    np.random.seed(42)
    random.seed(42)
    
    # بيانات العملاء
    customers = {
        'customer_id': [f'CUST_{i:04d}' for i in range(1, n_customers + 1)],
        'customer_name': [f'عميل {i}' for i in range(1, n_customers + 1)],
        'join_date': [datetime.now() - timedelta(days=random.randint(30, 730)) 
                     for _ in range(n_customers)],
        'email': [f'customer{i}@example.com' for i in range(1, n_customers + 1)],
        'city': [random.choice(['الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام']) 
                for _ in range(n_customers)]
    }
    
    customer_df = pd.DataFrame(customers)
    
    # بيانات المنتجات
    products = ['منتج A', 'منتج B', 'منتج C', 'منتج D', 'منتج E', 
                'منتج F', 'منتج G', 'منتج H']
    
    # بيانات الطلبات
    orders_data = {
        'order_id': [f'ORD_{i:06d}' for i in range(1, n_orders + 1)],
        'customer_id': [random.choice(customer_df['customer_id'].tolist()) 
                       for _ in range(n_orders)],
        'order_date': [datetime.now() - timedelta(days=random.randint(0, 365)) 
                      for _ in range(n_orders)],
        'amount': np.random.gamma(2, 50, n_orders).round(2),
        'quantity': np.random.randint(1, 20, n_orders),
        'product': [random.choice(products) for _ in range(n_orders)],
        'category': [random.choice(['الكترونيات', 'ملابس', 'منزل', 'مكتب', 'هدايا']) 
                    for _ in range(n_orders)]
    }
    
    orders_df = pd.DataFrame(orders_data)
    orders_df = orders_df.sort_values('order_date')
    
    # إنشاء المجلدات
    data_path = Path('data')
    raw_path = data_path / 'raw'
    raw_path.mkdir(parents=True, exist_ok=True)
    
    # حفظ البيانات
    customer_df.to_csv(raw_path / 'customers.csv', index=False)
    orders_df.to_csv(raw_path / 'sales.csv', index=False)
    orders_df.to_csv(raw_path / 'orders.csv', index=False)
    
    # حفظ البيانات في مجلد processed أيضًا
    processed_path = data_path / 'processed'
    processed_path.mkdir(parents=True, exist_ok=True)
    
    customer_df.to_csv(processed_path / 'customers_clean.csv', index=False)
    orders_df.to_csv(processed_path / 'orders_clean.csv', index=False)
    
    print("=" * 50)
    print("✅ تم إنشاء البيانات النموذجية بنجاح!")
    print("=" * 50)
    print(f"📊 عدد العملاء: {len(customer_df)}")
    print(f"📊 عدد الطلبات: {len(orders_df)}")
    print(f"💰 إجمالي الإيرادات: {orders_df['amount'].sum():,.2f}")
    print(f"📁 الموقع: {raw_path.absolute()}")
    print("=" * 50)
    
    return orders_df, customer_df


if __name__ == "__main__":
    generate_data()