"""
إنشاء بيانات نموذجية للاختبار
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# إنشاء مجلد البيانات إذا لم يكن موجوداً
Path("data/raw").mkdir(parents=True, exist_ok=True)

# عدد السجلات
n_records = 1000

# تواريخ عشوائية على مدار سنة
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)
dates = [start_date + timedelta(days=np.random.randint(0, 365)) for _ in range(n_records)]

# بيانات العملاء
customers = [f"C{str(i).zfill(4)}" for i in np.random.randint(1, 200, n_records)]

# بيانات المنتجات
products = [f"P{str(i).zfill(3)}" for i in np.random.randint(1, 50, n_records)]

# الكميات والأسعار
quantities = np.random.randint(1, 10, n_records)
prices = np.random.uniform(5, 500, n_records)
total_amounts = quantities * prices

# إنشاء DataFrame
df = pd.DataFrame({
    'transaction_id': [f"T{str(i).zfill(6)}" for i in range(1, n_records + 1)],
    'customer_id': customers,
    'product_id': products,
    'transaction_date': dates,
    'quantity': quantities,
    'unit_price': prices.round(2),
    'total_amount': total_amounts.round(2)
})

# ترتيب حسب التاريخ
df = df.sort_values('transaction_date').reset_index(drop=True)

# حفظ الملف
file_path = "data/raw/sales_data.csv"
df.to_csv(file_path, index=False, encoding='utf-8')
print(f"✅ تم إنشاء {len(df)} سجل في {file_path}")
print("\nعينة من البيانات:")
print(df.head(10))
print("\nإحصائيات سريعة:")
print(df.describe())