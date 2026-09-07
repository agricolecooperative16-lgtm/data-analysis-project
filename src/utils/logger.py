"""
نظام التسجيل للمشروع
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional
import yaml


def setup_logger(name: str = "data_analysis", 
                config_file: Optional[str] = None) -> logging.Logger:
    """
    إعداد نظام التسجيل
    
    Args:
        name: اسم المسجل
        config_file: مسار ملف إعدادات التسجيل
    
    Returns:
        كائن Logger مهيأ
    """
    # إنشاء مجلد logs إن لم يكن موجوداً
    Path("logs").mkdir(exist_ok=True)
    
    if config_file and Path(config_file).exists():
        # تحميل الإعدادات من ملف
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            return logging.getLogger(name)
    
    # إعدادات افتراضية
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # منع تكرار المعالجات
    if logger.handlers:
        return logger
    
    # معالج للملف
    file_handler = logging.FileHandler(
        'logs/app.log', 
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # معالج للمخرجات
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # تنسيق الرسائل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger