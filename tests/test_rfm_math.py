"""
اختبارات رياضية متقدمة لتحليل RFM
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.rfm_fixed import calculate_rfm_simple, get_rfm_insights


class TestRFMMathematicalAccuracy(unittest.TestCase):
    """اختبارات رياضية للتحقق من دقة حسابات RFM"""
    
    def setUp(self):
        np.random.seed(42)
        
        self.test_data = pd.DataFrame({
            'customer_id': [
                'A', 'A', 'A',
                'B', 'B',
                'C',
                'D', 'D', 'D', 'D', 'D'
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
                100, 200, 150,
                300, 250,
                400,
                50, 60, 70, 80, 90
            ]
        })
        
        self.max_date = datetime(2026, 9, 7)
    
    def test_recency_calculation(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        expected = {'A': 6, 'B': 18, 'C': 2, 'D': 0}
        for _, row in rfm.iterrows():
            if row['customer_id'] in expected:
                self.assertEqual(row['recency'], expected[row['customer_id']])
        
        print("✅ اختبار Recency: نجح")
    
    def test_frequency_calculation(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        expected = {'A': 3, 'B': 2, 'C': 1, 'D': 5}
        for _, row in rfm.iterrows():
            if row['customer_id'] in expected:
                self.assertEqual(row['frequency'], expected[row['customer_id']])
        
        print("✅ اختبار Frequency: نجح")
    
    def test_monetary_calculation(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        expected = {'A': 450.0, 'B': 550.0, 'C': 400.0, 'D': 350.0}
        for _, row in rfm.iterrows():
            if row['customer_id'] in expected:
                self.assertAlmostEqual(row['monetary'], expected[row['customer_id']], places=2)
        
        print("✅ اختبار Monetary: نجح")
    
    def test_r_score_distribution(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for _, row in rfm.iterrows():
            self.assertGreaterEqual(row['r_score'], 1)
            self.assertLessEqual(row['r_score'], 4)
        
        print("✅ اختبار R Score: نجح")
    
    def test_f_score_distribution(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for _, row in rfm.iterrows():
            self.assertGreaterEqual(row['f_score'], 1)
            self.assertLessEqual(row['f_score'], 4)
        
        print("✅ اختبار F Score: نجح")
    
    def test_m_score_distribution(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for _, row in rfm.iterrows():
            self.assertGreaterEqual(row['m_score'], 1)
            self.assertLessEqual(row['m_score'], 4)
        
        print("✅ اختبار M Score: نجح")
    
    def test_segment_assignment_logic(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for _, row in rfm.iterrows():
            self.assertIsNotNone(row['segment'])
            self.assertNotEqual(row['segment'], '')
        
        print("✅ اختبار تعيين الشرائح: نجح")
    
    def test_rfm_score_format(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for _, row in rfm.iterrows():
            self.assertEqual(len(str(row['rfm_score'])), 3)
        
        print("✅ اختبار تنسيق RFM Score: نجح")
    
    def test_no_negative_values(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        for col in ['recency', 'frequency', 'monetary', 'r_score', 'f_score', 'm_score']:
            self.assertTrue((rfm[col] >= 0).all())
        
        print("✅ اختبار عدم وجود قيم سالبة: نجح")
    
    def test_sum_of_segments_equals_total(self):
        rfm = calculate_rfm_simple(self.test_data)
        self.assertFalse(rfm.empty)
        
        total = len(rfm)
        segment_sum = rfm['segment'].value_counts().sum()
        self.assertEqual(total, segment_sum)
        
        print("✅ اختبار مجموع الشرائح: نجح")
    
    def test_segment_composition_based(self):
        """اختبار أن التقسيم يعتمد على تركيبة R/F/M"""
        
        test_data = pd.DataFrame({
            'customer_id': ['A'] * 7 + ['B'] * 7 + ['C'] * 7 + ['D'] * 7 + ['E'] * 7 + ['F'] * 7 + ['G'] * 7,
            'order_date': (
                # A: 7 طلبات حديثة جداً - Champion
                [datetime(2026, 9, 7), datetime(2026, 9, 6), datetime(2026, 9, 5),
                 datetime(2026, 9, 4), datetime(2026, 9, 3), datetime(2026, 9, 2),
                 datetime(2026, 9, 1)] +
                # B: 7 طلبات حديثة - Loyal
                [datetime(2026, 9, 5), datetime(2026, 9, 4), datetime(2026, 9, 3),
                 datetime(2026, 9, 2), datetime(2026, 9, 1), datetime(2026, 8, 31),
                 datetime(2026, 8, 30)] +
                # C: 7 طلبات حديثة ولكن قيمة منخفضة - New
                [datetime(2026, 9, 7), datetime(2026, 9, 6), datetime(2026, 9, 5),
                 datetime(2026, 9, 4), datetime(2026, 9, 3), datetime(2026, 9, 2),
                 datetime(2026, 9, 1)] +
                # D: 7 طلبات قديمة بقيمة عالية - At Risk
                [datetime(2026, 7, 7), datetime(2026, 7, 6), datetime(2026, 7, 5),
                 datetime(2026, 7, 4), datetime(2026, 7, 3), datetime(2026, 7, 2),
                 datetime(2026, 7, 1)] +
                # E: 7 طلبات قديمة بقيمة منخفضة - Lost
                [datetime(2026, 6, 7), datetime(2026, 6, 6), datetime(2026, 6, 5),
                 datetime(2026, 6, 4), datetime(2026, 6, 3), datetime(2026, 6, 2),
                 datetime(2026, 6, 1)] +
                # F: 7 طلبات متوسطة - Active
                [datetime(2026, 8, 15), datetime(2026, 8, 14), datetime(2026, 8, 13),
                 datetime(2026, 8, 12), datetime(2026, 8, 11), datetime(2026, 8, 10),
                 datetime(2026, 8, 9)] +
                # G: 7 طلبات متوسطة - Average
                [datetime(2026, 7, 15), datetime(2026, 7, 14), datetime(2026, 7, 13),
                 datetime(2026, 7, 12), datetime(2026, 7, 11), datetime(2026, 7, 10),
                 datetime(2026, 7, 9)]
            ),
            'amount': (
                # A: 7 طلبات بقيمة عالية - Champion
                [100, 110, 105, 115, 120, 95, 130] +
                # B: 7 طلبات بقيمة متوسطة - Loyal
                [50, 55, 45, 60, 40, 55, 50] +
                # C: 7 طلبات بقيمة منخفضة - New
                [10, 15, 5, 20, 8, 12, 18] +
                # D: 7 طلبات بقيمة عالية جداً - At Risk
                [200, 210, 195, 220, 205, 190, 215] +
                # E: 7 طلبات بقيمة منخفضة جداً - Lost
                [5, 8, 3, 10, 6, 4, 7] +
                # F: 7 طلبات بقيمة متوسطة - Active
                [30, 35, 25, 40, 28, 32, 38] +
                # G: 7 طلبات بقيمة منخفضة - Average
                [15, 12, 18, 20, 10, 14, 16]
            )
        })
        
        rfm = calculate_rfm_simple(test_data)
        
        # طباعة النتائج للتشخيص
        print("\n📊 نتائج RFM للاختبار:")
        for _, row in rfm.iterrows():
            print(f"  {row['customer_id']}: R={row['r_score']}, F={row['f_score']}, M={row['m_score']} -> {row['segment']}")
        
        self.assertFalse(rfm.empty, "النتيجة يجب ألا تكون فارغة")
        self.assertEqual(len(rfm), 7, f"يجب أن يكون هناك 7 عملاء، لكن يوجد {len(rfm)}")
        
        # تعريف الشرائح المتوقعة باستخدام منطق التقسيم الفعلي
        def get_expected_segment(r, f, m):
            if r >= 4 and f >= 4 and m >= 3:
                return '🏆 Champions'
            elif r >= 3 and f >= 4:
                return '❤️ Loyal Customers'
            elif r >= 4 and f <= 2:
                return '🌟 New Customers'
            elif r <= 2 and f >= 3 and m >= 3:
                return '⚠️ At Risk'
            elif r <= 2 and f <= 2 and m <= 2:
                return '💔 Lost'
            elif r >= 3 and f >= 3:
                return '✅ Active'
            else:
                return '📊 Average'
        
        # التحقق من كل عميل
        for _, row in rfm.iterrows():
            customer_id = row['customer_id']
            actual_segment = row['segment']
            expected_segment = get_expected_segment(
                row['r_score'], 
                row['f_score'], 
                row['m_score']
            )
            
            self.assertEqual(
                actual_segment, expected_segment,
                f"العميل {customer_id} (R={row['r_score']}, F={row['f_score']}, M={row['m_score']}) "
                f"حصل على '{actual_segment}' ولكن المتوقع '{expected_segment}'"
            )
        
        print("✅ اختبار التقسيم المبني على التركيبة: نجح")


class TestRFMDataIntegrity(unittest.TestCase):
    """اختبارات سلامة البيانات"""
    
    def test_handles_empty_data(self):
        empty_df = pd.DataFrame(columns=['customer_id', 'order_date', 'amount'])
        rfm = calculate_rfm_simple(empty_df)
        
        self.assertTrue(rfm.empty)
        self.assertIn('customer_id', rfm.columns)
        
        print("✅ اختبار البيانات الفارغة: نجح")
    
    def test_handles_missing_values(self):
        data = pd.DataFrame({
            'customer_id': ['A', 'A', 'B', 'B', 'C'],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 8, 20),
                None,
                datetime(2026, 9, 5)
            ],
            'amount': [100, None, 300, 250, 400]
        })
        
        rfm = calculate_rfm_simple(data)
        self.assertFalse(rfm.empty)
        
        print("✅ اختبار القيم المفقودة: نجح")
    
    def test_handles_duplicate_customer_ids(self):
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
        self.assertEqual(rfm['customer_id'].nunique(), 2)
        
        print("✅ اختبار المكررات: نجح")
    
    def test_handles_dataframe_without_amount(self):
        data = pd.DataFrame({
            'customer_id': ['A', 'A', 'B', 'B', 'C'],
            'order_date': [
                datetime(2026, 9, 1),
                datetime(2026, 8, 15),
                datetime(2026, 8, 20),
                datetime(2026, 6, 10),
                datetime(2026, 9, 5)
            ]
        })
        
        rfm = calculate_rfm_simple(data)
        self.assertFalse(rfm.empty)
        self.assertTrue((rfm['monetary'] == 0).all())
        
        print("✅ اختبار بدون عمود amount: نجح")


class TestRFMScoreConsistency(unittest.TestCase):
    """اختبارات اتساق النقاط"""
    
    def setUp(self):
        np.random.seed(42)
        customers = [f'CUST_{i:04d}' for i in range(1, 21)]
        self.data = pd.DataFrame({
            'customer_id': np.random.choice(customers, 100),
            'order_date': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(100)],
            'amount': np.random.gamma(2, 50, 100).round(2)
        })
    
    def test_scores_are_integers(self):
        rfm = calculate_rfm_simple(self.data)
        self.assertFalse(rfm.empty)
        
        for col in ['r_score', 'f_score', 'm_score']:
            self.assertTrue((rfm[col].apply(lambda x: isinstance(x, int))).all())
        
        print("✅ اختبار النقاط كأعداد صحيحة: نجح")
    
    def test_scores_in_range(self):
        rfm = calculate_rfm_simple(self.data)
        self.assertFalse(rfm.empty)
        
        for col in ['r_score', 'f_score', 'm_score']:
            self.assertTrue((rfm[col] >= 1).all())
            self.assertTrue((rfm[col] <= 4).all())
        
        print("✅ اختبار النطاق: نجح")
    
    def test_higher_value_higher_score(self):
        rfm = calculate_rfm_simple(self.data)
        self.assertFalse(rfm.empty)
        
        if len(rfm) >= 2:
            min_recency = rfm.loc[rfm['recency'].idxmin()]
            max_recency = rfm.loc[rfm['recency'].idxmax()]
            self.assertGreaterEqual(min_recency['r_score'], max_recency['r_score'])
        
        print("✅ اختبار العلاقة الطردية: نجح")


if __name__ == '__main__':
    unittest.main(verbosity=2)