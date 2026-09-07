"""
وحدة تحميل البيانات (Data Loader)
مسؤولة عن تحميل البيانات من مصادر مختلفة
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union

class DataLoader:
    """
    فئة تحميل البيانات - نسخة مبسطة
    ملاحظة: هذه الفئة عديمة الحالة (Stateless) ولا تحتاج إلى Singleton
    """
    
    @staticmethod
    def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        تحميل ملف CSV
        
        Args:
            file_path: مسار ملف CSV
            
        Returns:
            pd.DataFrame: البيانات المحملة
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        return pd.read_csv(file_path)
    
    @staticmethod
    def load_excel(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        تحميل ملف Excel
        
        Args:
            file_path: مسار ملف Excel
            
        Returns:
            pd.DataFrame: البيانات المحملة
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        return pd.read_excel(file_path)
    
    @staticmethod
    def load_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        تحميل بيانات تلقائي حسب امتداد الملف
        
        Args:
            file_path: مسار الملف
            **kwargs: معاملات إضافية لـ pandas
            
        Returns:
            pd.DataFrame: البيانات المحملة
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return pd.read_csv(file_path, **kwargs)
        elif extension in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, **kwargs)
        elif extension == '.json':
            return pd.read_json(file_path, **kwargs)
        else:
            raise ValueError(f"نوع الملف غير مدعوم: {extension}")
    
    # ملاحظة: لا توجد حالة (State) في هذه الفئة
    # لذلك لا نحتاج إلى Singleton أو __new__


# دوال مساعدة على مستوى الموديول (بدون فئة)
def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
    """دالة مساعدة لتحميل CSV مباشرة"""
    return DataLoader.load_csv(file_path)

def load_excel(file_path: Union[str, Path]) -> pd.DataFrame:
    """دالة مساعدة لتحميل Excel مباشرة"""
    return DataLoader.load_excel(file_path)

def load_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """دالة مساعدة لتحميل البيانات تلقائيًا"""
    return DataLoader.load_data(file_path, **kwargs)


if __name__ == "__main__":
    # اختبار سريع
    print("✅ DataLoader جاهز للاستخدام")
    print("📌 هذه الفئة عديمة الحالة (Stateless) ولا تستخدم Singleton")