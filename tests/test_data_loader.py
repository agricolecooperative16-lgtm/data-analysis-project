import unittest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.loader import DataLoader, load_data

class TestDataLoader(unittest.TestCase):
    
    def test_load_csv(self):
        """اختبار تحميل CSV"""
        # إنشاء بيانات اختبار مؤقتة
        test_df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        test_file = Path("test_temp.csv")
        test_df.to_csv(test_file, index=False)
        
        try:
            loaded = DataLoader.load_csv(str(test_file))
            self.assertEqual(len(loaded), 3)
            self.assertEqual(list(loaded.columns), ['col1', 'col2'])
        finally:
            test_file.unlink(missing_ok=True)
        
        print("✅ اختبار load_csv نجح")
    
    def test_no_singleton(self):
        """اختبار عدم استخدام Singleton"""
        loader1 = DataLoader()
        loader2 = DataLoader()
        
        self.assertIsNot(loader1, loader2, 
                        "DataLoader يجب ألا يستخدم Singleton")
        print("✅ اختبار عدم استخدام Singleton نجح")
    
    def test_load_data_auto_detect(self):
        """اختبار التحميل التلقائي"""
        test_df = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})
        test_csv = Path("test_auto.csv")
        test_df.to_csv(test_csv, index=False)
        
        try:
            loaded = load_data(str(test_csv))
            self.assertTrue(isinstance(loaded, pd.DataFrame))
        finally:
            test_csv.unlink(missing_ok=True)
        
        print("✅ اختبار التحميل التلقائي نجح")

if __name__ == "__main__":
    unittest.main()