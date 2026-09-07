"""
تحميل البيانات من مصادر مختلفة
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, Dict, Any
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataLoader:
    """فئة لتحميل البيانات من مصادر متعددة"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_csv(self, file_path: Union[str, Path], 
                encoding: str = 'utf-8',
                **kwargs) -> pd.DataFrame:
        """
        تحميل بيانات من ملف CSV
        
        Args:
            file_path: مسار الملف
            encoding: ترميز الملف
            **kwargs: وسائط إضافية لـ pd.read_csv
        
        Returns:
            DataFrame مع البيانات المحملة
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"الملغير موجود: {file_path}")
        
        try:
            logger.info(f"تحميل البيانات من {file_path}")
            df = pd.read_csv(file_path, encoding=encoding, **kwargs)
            logger.info(f"تم تحميل {len(df)} سجل بنجاح")
            return df
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {str(e)}")
            raise
    
    def load_excel(self, file_path: Union[str, Path],
                   sheet_name: Optional[Union[str, int]] = 0,
                   **kwargs) -> pd.DataFrame:
        """
        تحميل بيانات من ملف Excel
        
        Args:
            file_path: مسار الملف
            sheet_name: اسم أو رقم الورقة
            **kwargs: وسائط إضافية لـ pd.read_excel
        
        Returns:
            DataFrame مع البيانات المحملة
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")
        
        try:
            logger.info(f"تحميل البيانات من {file_path} (ورقة: {sheet_name})")
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            logger.info(f"تم تحميل {len(df)} سجل بنجاح")
            return df
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {str(e)}")
            raise
    
    def load_all_data(self, config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        تحميل جميع ملفات البيانات بناءً على الإعدادات
        
        Args:
            config: قاموس الإعدادات
        
        Returns:
            قاموس يحتوي على DataFrames المحملة
        """
        data_path = Path(config['data']['raw_path'])
        data_files = {
            'sales': config['data']['sales_file'],
            'customers': config['data']['customers_file'],
            'products': config['data']['products_file']
        }
        
        loaded_data = {}
        
        for name, filename in data_files.items():
            file_path = data_path / filename
            if file_path.exists():
                if file_path.suffix == '.csv':
                    loaded_data[name] = self.load_csv(file_path)
                elif file_path.suffix in ['.xlsx', '.xls']:
                    loaded_data[name] = self.load_excel(file_path)
                else:
                    logger.warning(f"نوع الملف غير معروف: {file_path}")
            else:
                logger.warning(f"الملف غير موجود: {file_path}")
        
        return loaded_data