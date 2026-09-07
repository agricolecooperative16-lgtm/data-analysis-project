import unittest
from src.dataloader import DataLoader  # افترض الموقع الفعلي

class TestDataLoaderSingleton(unittest.TestCase):
    
    def test_singleton_unnecessary_state(self):
        """اختبار هل الـ Singleton ضروري بالفعل؟"""
        # إنشاء نسختين
        loader1 = DataLoader()
        loader2 = DataLoader()
        
        # اختبار 1: هل تعيد النسختان نفس الكائن؟ (علامة على Singleton)
        self.assertIs(loader1, loader2, "Singleton يعيد نفس النسخة")
        
        # اختبار 2: هل هناك حالة (state) حقيقية محفوظة؟
        # استدعاء نفس الدالة مرتين يجب أن يعيد نفس النتيجة بغض النظر عن الترتيب
        result1 = loader1.load_data("sample.csv")
        result2 = loader2.load_data("sample.csv")
        
        # إذا كانت النتائج متطابقة دائمًا، الـ state غير موجود
        self.assertTrue(result1.equals(result2), 
                       "البيانات المحملة يجب أن تكون متطابقة")
        
        # اختبار 3: هل تغيير حالة أحدهما يؤثر على الآخر؟
        # (إذا لم توجد حالة، هذا الاختبار سينجح دائمًا)
        loader1.some_attribute = "test_value"
        self.assertFalse(hasattr(loader2, "some_attribute"),
                        "تغيير loader1 لا يجب أن يؤثر على loader2 إذا كانت الحالة غير مشتركة")