import unittest
import sys
import inspect
import time
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDataLoaderSingleton(unittest.TestCase):
    """اختبارات للتحقق من استخدام Singleton في DataLoader"""
    
    @classmethod
    def setUpClass(cls):
        """تحميل DataLoader مرة واحدة لجميع الاختبارات"""
        try:
            from src.data.loader import DataLoader
            cls.DataLoader = DataLoader
            print("\n✅ تم استيراد DataLoader من src.data.loader")
        except ImportError as e:
            cls.DataLoader = None
            print(f"❌ فشل استيراد DataLoader: {e}")
    
    def setUp(self):
        """التحقق من توفر DataLoader قبل كل اختبار"""
        if self.DataLoader is None:
            self.skipTest("DataLoader غير متوفر")
    
    def test_singleton_usage(self):
        """اختبار أساسي: هل يستخدم DataLoader نمط Singleton؟"""
        print("\n📌 اختبار 1: التحقق من استخدام Singleton")
        
        # إنشاء نسختين
        loader1 = self.DataLoader()
        loader2 = self.DataLoader()
        
        # التحقق من الهوية
        is_singleton = (loader1 is loader2)
        
        print(f"  loader1 is loader2: {is_singleton}")
        print(f"  عنوان loader1: {id(loader1)}")
        print(f"  عنوان loader2: {id(loader2)}")
        
        if is_singleton:
            print("  ⚠️ يستخدم Singleton (جميع النسخ تشير لنفس الكائن)")
        else:
            print("  ✅ لا يستخدم Singleton (كل نسخة كائن مستقل)")
        
        self.assertTrue(True)  # اختبار إعلامي فقط
    
    def test_shared_state(self):
        """اختبار: هل توجد حالة مشتركة بين النسخ؟"""
        print("\n📌 اختبار 2: التحقق من الحالة المشتركة")
        
        loader1 = self.DataLoader()
        loader2 = self.DataLoader()
        
        # محاولة إضافة خاصية للنسخة الأولى
        try:
            loader1._test_attr = "test_value"
            has_shared = hasattr(loader2, "_test_attr")
            
            print(f"  loader1._test_attr = 'test_value'")
            print(f"  loader2 لديه _test_attr: {has_shared}")
            
            if has_shared:
                print("  ⚠️ توجد حالة مشتركة (Shared State)")
                print("     → هذا قد يبرر استخدام Singleton")
            else:
                print("  ✅ لا توجد حالة مشتركة")
                print("     → Singleton غير ضروري هنا")
                
        except Exception as e:
            print(f"  ⚠️ لا يمكن اختبار الحالة: {e}")
        
        self.assertTrue(True)
    
    def test_instance_attributes(self):
        """اختبار: ما هي خصائص الحالة الموجودة في DataLoader؟"""
        print("\n📌 اختبار 3: فحص خصائص DataLoader")
        
        loader = self.DataLoader()
        
        # الحصول على جميع الخصائص (غير الدوال)
        attrs = [attr for attr in dir(loader) 
                if not attr.startswith('__') 
                and not callable(getattr(loader, attr))]
        
        # البحث عن خصائص تخزين البيانات
        data_attrs = [attr for attr in attrs 
                     if any(key in attr.lower() for key in ['data', 'cache', 'state', 'store', 'buffer'])]
        
        print(f"  عدد الخصائص الكلي: {len(attrs)}")
        if attrs:
            print(f"  الخصائص: {attrs}")
        
        if data_attrs:
            print(f"  📦 خصائص تخزين البيانات: {data_attrs}")
            print("     → DataLoader يحتفظ بحالة (لديه خصائص تخزين)")
            print("     → استخدام Singleton قد يكون مبررًا لتجنب تكرار التحميل")
        else:
            print("  ❌ لا توجد خصائص تخزين بيانات")
            print("     → DataLoader عديم الحالة (Stateless)")
            print("     → Singleton غير ضروري تمامًا!")
        
        self.assertTrue(True)
    
    def test_performance_comparison(self):
        """اختبار: مقارنة أداء إنشاء نسخ متعددة"""
        print("\n📌 اختبار 4: اختبار الأداء")
        
        # اختبار إنشاء 1000 نسخة
        start = time.time()
        instances = []
        for _ in range(1000):
            instances.append(self.DataLoader())
        end = time.time()
        
        total_time = end - start
        unique_count = len(set(instances))
        
        print(f"  وقت إنشاء 1000 نسخة: {total_time:.4f} ثانية")
        print(f"  عدد النسخ الفريدة: {unique_count} من 1000")
        
        if unique_count == 1:
            print("  ⚠️ Singleton: جميع النسخ تشير لنفس الكائن")
            print("     → استهلاك ذاكرة منخفض ولكن مرونة محدودة")
        elif unique_count < 100:
            print(f"  ⚠️ تم إنشاء {unique_count} كائنات فقط (قد يكون هناك Cache)")
        else:
            print(f"  ✅ تم إنشاء {unique_count} كائن مختلف")
            print("     → لا يوجد Singleton، كل استدعاء ينتج كائنًا جديدًا")
        
        self.assertTrue(True)
    
    def test_source_code_analysis(self):
        """اختبار: تحليل الكود المصدري للبحث عن تنفيذ Singleton"""
        print("\n📌 اختبار 5: تحليل الكود المصدري")
        
        try:
            # الحصول على مصدر الفئة
            source = inspect.getsource(self.DataLoader)
            
            # البحث عن أنماط Singleton
            patterns = {
                '__new__': '__new__' in source,
                'singleton': 'singleton' in source.lower(),
                '_instance': '_instance' in source,
                '_singleton': '_singleton' in source.lower(),
                'instance =': 'instance =' in source and 'None' in source
            }
            
            print("  🔍 أنماط Singleton في الكود:")
            for pattern, found in patterns.items():
                print(f"    - {pattern}: {'✅' if found else '❌'}")
            
            if any(patterns.values()):
                print("  ⚠️ توجد إشارات إلى Singleton في الكود المصدري")
            else:
                print("  ✅ لا توجد إشارات إلى Singleton في الكود المصدري")
                
        except Exception as e:
            print(f"  ⚠️ لا يمكن تحليل الكود المصدري: {e}")
        
        self.assertTrue(True)
    
    def test_method_behavior(self):
        """اختبار: هل تعتمد دوال DataLoader على حالة داخلية؟"""
        print("\n📌 اختبار 6: فحص دوال DataLoader")
        
        loader = self.DataLoader()
        
        # الحصول على جميع الدوال
        methods = [attr for attr in dir(loader) 
                  if not attr.startswith('__') 
                  and callable(getattr(loader, attr))]
        
        print(f"  عدد الدوال: {len(methods)}")
        print(f"  الدوال: {methods[:10]}")
        if len(methods) > 10:
            print(f"  ... و {len(methods) - 10} دوال أخرى")
        
        # البحث عن دوال تحميل البيانات
        load_methods = [m for m in methods if 'load' in m.lower() or 'read' in m.lower()]
        
        if load_methods:
            print(f"  📂 دوال التحميل: {load_methods}")
        else:
            print("  ❌ لا توجد دوال تحميل (قد تكون خارج الفئة)")
        
        self.assertTrue(True)

    def test_final_recommendation(self):
        """الاختبار النهائي: تقديم توصية بناءً على النتائج"""
        print("\n" + "="*60)
        print("📋 التوصية النهائية")
        print("="*60)
        
        # جمع النتائج من الاختبارات السابقة (محاكاة بسيطة)
        loader = self.DataLoader()
        attrs = [attr for attr in dir(loader) 
                if not attr.startswith('__') 
                and not callable(getattr(loader, attr))]
        
        has_state = bool(attrs)
        
        # الحصول على مصدر الفئة للتحقق من Singleton
        try:
            source = inspect.getsource(self.DataLoader)
            has_singleton_code = any([
                '__new__' in source,
                '_instance' in source,
                'singleton' in source.lower()
            ])
        except:
            has_singleton_code = False
        
        print(f"  🔍 النتائج:")
        print(f"    - وجود حالة (State): {'✅ نعم' if has_state else '❌ لا'}")
        print(f"    - وجود كود Singleton: {'✅ نعم' if has_singleton_code else '❌ لا'}")
        
        print(f"\n  💡 التوصية:")
        if not has_state and has_singleton_code:
            print("    ⚠️ **DataLoader يستخدم Singleton لكنه عديم الحالة!**")
            print("    → هذا غير ضروري ويُعقد الكود")
            print("    → يُنصح بإزالة Singleton واستخدام دوال ثابتة أو دوال عادية")
        elif has_state and has_singleton_code:
            print("    ✅ **DataLoader يستخدم Singleton ويحتوي على حالة**")
            print("    → استخدام Singleton مبرر لتجنب تكرار تحميل البيانات")
            print("    → يمكن الاحتفاظ به مع التأكد من إدارة الحالة بشكل صحيح")
        elif not has_state and not has_singleton_code:
            print("    ✅ **DataLoader لا يستخدم Singleton ولا يحتوي على حالة**")
            print("    → التصميم صحيح وبسيط")
        else:
            print("    ⚠️ **DataLoader يحتوي على حالة لكن لا يستخدم Singleton**")
            print("    → قد يكون مفيدًا إضافة Singleton لتجنب تكرار تحميل البيانات")
        
        print("="*60)
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)