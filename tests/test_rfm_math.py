"""
اختبارات رياضية متقدمة لتحليل RFM
تتحقق من صحة الحسابات وليس فقط من تشغيل الدالة
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.rfm_fixed import calculate_rfm_simple, get_rfm_insights


class TestRFMMathematicalAccuracy(unittest.TestCase):
    """اختبارات رياضية للتحقق من دقة حسابات RFM"""
    
    def setUp(self):
        """إعداد بيانات اختبار معروفة النتائج"""
        np.random.seed(42)
        
        # إنشاء بيانات معروفة
        self.test_data = pd.DataFrame({
            'customer_id': [
                'A', 'A', 'A',  # عميل A: 3 طلبات
                'B', 'B',       # عميل B: طلبان
                'C',            # عميل C: طلب واحد
                'D', 'D', 'D', 'D', 'D'  # عميل D: 5 طلبات
            ],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 7, 1),
                datetime(2026, 8, 20),
                datetime(2026, 6, 10),
                datetime(2026, 9, 5),
                datetime(2026, 9, 7),
                datetime(2026, 8, 1),
                datetime(2026, 7, 15),
                datetime(2026, 6, 20),
                datetime(2026, 5, 1)
            ],
            'amount': [
                100, 200, 150,   # A: 450
                300, 250,        # B: 550
                400,             # C: 400
                50, 60, 70, 80, 90  # D: 350
            ]
        })
        
        # تاريخ المرجع (أحدث تاريخ)
        self.max_date = datetime(2026, 9, 7)
    
    def test_recency_calculation(self):
        """اختبار حساب Recency (حداثة الشراء)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        # التحقق من قيم Recency المتوقعة يدوياً
        expected_recency = {
            'A': (self.max_date - datetime(2026, 9, 1)).days,  # 6 أيام
            'B': (self.max_date - datetime(2026, 8, 20)).days,  # 18 يوم
            'C': (self.max_date - datetime(2026, 9, 5)).days,   # 2 يوم
            'D': (self.max_date - datetime(2026, 9, 7)).days    # 0 يوم
        }
        
        for _, row in rfm.iterrows():
            customer_id = row['customer_id']
            actual_recency = row['recency']
            expected = expected_recency.get(customer_id)
            
            if expected is not None:
                self.assertEqual(
                    actual_recency, expected,
                    f"Recency خاطئ للعميل {customer_id}: المتوقع {expected}، الحالي {actual_recency}"
                )
        
        print("✅ اختبار Recency: نجح")
    
    def test_frequency_calculation(self):
        """اختبار حساب Frequency (تكرار الشراء)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        expected_frequency = {
            'A': 3,  # 3 طلبات
            'B': 2,  # طلبان
            'C': 1,  # طلب واحد
            'D': 5   # 5 طلبات
        }
        
        for _, row in rfm.iterrows():
            customer_id = row['customer_id']
            actual_frequency = row['frequency']
            expected = expected_frequency.get(customer_id)
            
            if expected is not None:
                self.assertEqual(
                    actual_frequency, expected,
                    f"Frequency خاطئ للعميل {customer_id}: المتوقع {expected}، الحالي {actual_frequency}"
                )
        
        print("✅ اختبار Frequency: نجح")
    
    def test_monetary_calculation(self):
        """اختبار حساب Monetary (القيمة المالية)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        expected_monetary = {
            'A': 450.0,   # 100 + 200 + 150
            'B': 550.0,   # 300 + 250
            'C': 400.0,   # 400
            'D': 350.0    # 50 + 60 + 70 + 80 + 90
        }
        
        for _, row in rfm.iterrows():
            customer_id = row['customer_id']
            actual_monetary = row['monetary']
            expected = expected_monetary.get(customer_id)
            
            if expected is not None:
                self.assertAlmostEqual(
                    actual_monetary, expected, places=2,
                    msg=f"Monetary خاطئ للعميل {customer_id}: المتوقع {expected}، الحالي {actual_monetary}"
                )
        
        print("✅ اختبار Monetary: نجح")
    
    def test_r_score_distribution(self):
        """اختبار توزيع نقاط R (Recency Score)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        # R Score يجب أن يكون بين 1 و 4
        for _, row in rfm.iterrows():
            r_score = row['r_score']
            self.assertGreaterEqual(r_score, 1, f"R Score {r_score} أقل من 1")
            self.assertLessEqual(r_score, 4, f"R Score {r_score} أكبر من 4")
        
        # العملاء الأحدث يجب أن يكون لهم R Score أعلى
        # C (2 يوم) يجب أن يكون R Score أعلى من B (18 يوم)
        rfm_dict = rfm.set_index('customer_id').to_dict('index')
        
        if 'C' in rfm_dict and 'B' in rfm_dict:
            self.assertGreaterEqual(
                rfm_dict['C']['r_score'], 
                rfm_dict['B']['r_score'],
                "العميل الأحدث (C) يجب أن يكون له R Score أعلى من العميل الأقل حداثة (B)"
            )
        
        print("✅ اختبار R Score: نجح")
    
    def test_f_score_distribution(self):
        """اختبار توزيع نقاط F (Frequency Score)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        # F Score يجب أن يكون بين 1 و 4
        for _, row in rfm.iterrows():
            f_score = row['f_score']
            self.assertGreaterEqual(f_score, 1, f"F Score {f_score} أقل من 1")
            self.assertLessEqual(f_score, 4, f"F Score {f_score} أكبر من 4")
        
        # العملاء الأكثر تكراراً يجب أن يكون لهم F Score أعلى
        rfm_dict = rfm.set_index('customer_id').to_dict('index')
        
        if 'D' in rfm_dict and 'C' in rfm_dict:
            self.assertGreaterEqual(
                rfm_dict['D']['f_score'],
                rfm_dict['C']['f_score'],
                "العميل الأكثر تكراراً (D) يجب أن يكون له F Score أعلى من العميل الأقل تكراراً (C)"
            )
        
        print("✅ اختبار F Score: نجح")
    
    def test_m_score_distribution(self):
        """اختبار توزيع نقاط M (Monetary Score)"""
        rfm = calculate_rfm_simple(self.test_data)
        
        # M Score يجب أن يكون بين 1 و 4
        for _, row in rfm.iterrows():
            m_score = row['m_score']
            self.assertGreaterEqual(m_score, 1, f"M Score {m_score} أقل من 1")
            self.assertLessEqual(m_score, 4, f"M Score {m_score} أكبر من 4")
        
        # العملاء ذوو القيمة الأعلى يجب أن يكون لهم M Score أعلى
        rfm_dict = rfm.set_index('customer_id').to_dict('index')
        
        if 'B' in rfm_dict and 'D' in rfm_dict:
            self.assertGreaterEqual(
                rfm_dict['B']['m_score'],
                rfm_dict['D']['m_score'],
                "العميل ذو القيمة الأعلى (B) يجب أن يكون له M Score أعلى من العميل ذو القيمة الأقل (D)"
            )
        
        print("✅ اختبار M Score: نجح")
    
    def test_segment_assignment_logic(self):
        """اختبار منطق تعيين الشرائح"""
        rfm = calculate_rfm_simple(self.test_data)
        
        # تعريف معايير كل شريحة
        def get_expected_segment(r, f, m):
            if r >= 3 and f >= 3 and m >= 3:
                return 'VIP'
            elif r >= 3 and f >= 2:
                return 'نشط'
            elif r <= 2 and f >= 3:
                return 'مخلص'
            elif r <= 2 and f <= 2:
                return 'خطر'
            else:
                return 'متوسط'
        
        for _, row in rfm.iterrows():
            r, f, m = row['r_score'], row['f_score'], row['m_score']
            actual_segment = row['segment']
            expected_segment = get_expected_segment(r, f, m)
            
            self.assertEqual(
                actual_segment, expected_segment,
                f"شريحة خاطئة للعميل {row['customer_id']}: "
                f"R={r}, F={f}, M={m}, المتوقع {expected_segment}، الحالي {actual_segment}"
            )
        
        print("✅ اختبار تعيين الشرائح: نجح")
    
    def test_rfm_score_format(self):
        """اختبار تنسيق RFM Score"""
        rfm = calculate_rfm_simple(self.test_data)
        
        for _, row in rfm.iterrows():
            rfm_score = row['rfm_score']
            
            # يجب أن يكون 3 أرقام
            self.assertEqual(len(str(rfm_score)), 3, f"RFM Score {rfm_score} يجب أن يكون 3 أرقام")
            
            # يجب أن تكون الأرقام بين 1 و 4
            for digit in str(rfm_score):
                self.assertIn(int(digit), range(1, 5), f"رقم {digit} في RFM Score غير صالح")
        
        print("✅ اختبار تنسيق RFM Score: نجح")
    
    def test_no_negative_values(self):
        """اختبار عدم وجود قيم سالبة في النتائج"""
        rfm = calculate_rfm_simple(self.test_data)
        
        numeric_cols = ['recency', 'frequency', 'monetary', 'r_score', 'f_score', 'm_score']
        
        for col in numeric_cols:
            if col in rfm.columns:
                self.assertTrue(
                    (rfm[col] >= 0).all(),
                    f"توجد قيم سالبة في عمود {col}"
                )
        
        print("✅ اختبار عدم وجود قيم سالبة: نجح")
    
    def test_sum_of_segments_equals_total(self):
        """اختبار أن مجموع العملاء في الشرائح يساوي إجمالي العملاء"""
        rfm = calculate_rfm_simple(self.test_data)
        
        total_customers = len(rfm)
        segment_counts = rfm['segment'].value_counts().sum()
        
        self.assertEqual(
            total_customers, segment_counts,
            f"مجموع العملاء في الشرائح ({segment_counts}) لا يساوي إجمالي العملاء ({total_customers})"
        )
        
        print("✅ اختبار مجموع الشرائح: نجح")


class TestRFMDataIntegrity(unittest.TestCase):
    """اختبارات سلامة البيانات في RFM"""
    
    def test_handles_empty_data(self):
        """اختبار التعامل مع البيانات الفارغة"""
        # إنشاء DataFrame فارغ مع الأعمدة الصحيحة
        empty_df = pd.DataFrame(columns=['customer_id', 'order_date', 'amount'])
        
        try:
            rfm = calculate_rfm_simple(empty_df)
            # يجب أن يكون DataFrame فارغاً
            self.assertTrue(rfm.empty, "يجب أن تكون النتيجة DataFrame فارغاً للبيانات الفارغة")
            print("✅ اختبار البيانات الفارغة: نجح")
        except Exception as e:
            # إذا كانت الدالة ترفع خطأ، يجب أن يكون خطأ محدداً
            self.fail(f"فشل التعامل مع البيانات الفارغة: {e}")
    
    def test_handles_missing_values(self):
        """اختبار التعامل مع القيم المفقودة"""
        data = pd.DataFrame({
            'customer_id': ['A', 'A', 'B', 'B', 'C'],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 8, 20),
                None,  # تاريخ مفقود
                datetime(2026, 9, 5)
            ],
            'amount': [100, None, 300, 250, 400]  # amount مفقود
        })
        
        # يجب أن تعمل الدالة دون أخطاء
        try:
            rfm = calculate_rfm_simple(data)
            self.assertIsNotNone(rfm)
            print("✅ اختبار القيم المفقودة: نجح")
        except Exception as e:
            self.fail(f"فشل التعامل مع القيم المفقودة: {e}")
    
    def test_handles_duplicate_customer_ids(self):
        """اختبار التعامل مع معرفات العملاء المكررة"""
        data = pd.DataFrame({
            'customer_id': ['A', 'A', 'A', 'B', 'B'],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 7, 1),
                datetime(2026, 8, 20),
                datetime(2026, 6, 10)
            ],
            'amount': [100, 200, 150, 300, 250]
        })
        
        rfm = calculate_rfm_simple(data)
        
        # يجب أن يكون هناك عميلان فقط (A و B)
        unique_customers = rfm['customer_id'].nunique()
        self.assertEqual(unique_customers, 2, f"يجب أن يكون هناك عميلان فقط، لكن يوجد {unique_customers}")
        
        print("✅ اختبار المكررات: نجح")
    
    def test_handles_dataframe_without_amount(self):
        """اختبار التعامل مع DataFrame بدون عمود amount"""
        data = pd.DataFrame({
            'customer_id': ['A', 'A', 'B', 'B', 'C'],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 8, 20),
                datetime(2026, 6, 10),
                datetime(2026, 9, 5)
            ]
            # لا يوجد عمود amount
        })
        
        try:
            rfm = calculate_rfm_simple(data)
            self.assertIsNotNone(rfm)
            # monetary يجب أن يكون 0 للجميع
            self.assertTrue((rfm['monetary'] == 0).all(), "يجب أن تكون monetary = 0 عند عدم وجود عمود amount")
            print("✅ اختبار بدون عمود amount: نجح")
        except Exception as e:
            self.fail(f"فشل التعامل مع البيانات بدون amount: {e}")


class TestRFMScoreConsistency(unittest.TestCase):
    """اختبارات اتساق نقاط RFM"""
    
    def setUp(self):
        """إعداد بيانات للاختبارات"""
        np.random.seed(42)
        self.data = self.create_sample_data()
    
    def create_sample_data(self, n_customers=20, n_orders=100):
        """إنشاء بيانات عشوائية للاختبارات"""
        customers = [f'CUST_{i:04d}' for i in range(1, n_customers + 1)]
        
        data = pd.DataFrame({
            'customer_id': np.random.choice(customers, n_orders),
            'order_date': [datetime.now() - timedelta(days=np.random.randint(0, 365)) 
                          for _ in range(n_orders)],
            'amount': np.random.gamma(2, 50, n_orders).round(2)
        })
        
        return data
    
    def test_scores_are_integers(self):
        """اختبار أن النقاط هي أعداد صحيحة"""
        rfm = calculate_rfm_simple(self.data)
        
        score_cols = ['r_score', 'f_score', 'm_score']
        
        for col in score_cols:
            self.assertTrue(
                (rfm[col].apply(lambda x: isinstance(x, (int, np.integer)))).all(),
                f"عمود {col} يحتوي على قيم ليست أعداداً صحيحة"
            )
        
        print("✅ اختبار النقاط كأعداد صحيحة: نجح")
    
    def test_scores_in_range(self):
        """اختبار أن النقاط في النطاق 1-4"""
        rfm = calculate_rfm_simple(self.data)
        
        score_cols = ['r_score', 'f_score', 'm_score']
        
        for col in score_cols:
            self.assertTrue(
                (rfm[col] >= 1).all() and (rfm[col] <= 4).all(),
                f"عمود {col} يحتوي على قيم خارج النطاق 1-4"
            )
        
        print("✅ اختبار النطاق: نجح")
    
    def test_higher_value_higher_score(self):
        """اختبار أن القيم الأعلى تعطي نقاطاً أعلى (علاقة طردية)"""
        rfm = calculate_rfm_simple(self.data)
        
        # يجب أن يكون هناك على الأقل عميلان
        if len(rfm) >= 2:
            # العميل ذو Recency الأقل (أحدث) يجب أن يكون R Score أعلى
            min_recency = rfm.loc[rfm['recency'].idxmin()]
            max_recency = rfm.loc[rfm['recency'].idxmax()]
            
            self.assertGreaterEqual(
                min_recency['r_score'],
                max_recency['r_score'],
                "العميل الأحدث يجب أن يكون له R Score أعلى"
            )
            
            # العميل ذو Frequency الأعلى يجب أن يكون F Score أعلى
            max_freq = rfm.loc[rfm['frequency'].idxmax()]
            min_freq = rfm.loc[rfm['frequency'].idxmin()]
            
            self.assertGreaterEqual(
                max_freq['f_score'],
                min_freq['f_score'],
                "العميل الأكثر تكراراً يجب أن يكون له F Score أعلى"
            )
        
        print("✅ اختبار العلاقة الطردية: نجح")


if __name__ == '__main__':
    # تشغيل الاختبارات
    unittest.main(verbosity=2)