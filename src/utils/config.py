"""
إدارة ملفات الإعدادات
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os


class Config:
    """فئة لإدارة الإعدادات"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._config = {}
        self._load_environment()
    
    def _load_environment(self):
        """تحميل متغيرات البيئة"""
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
    
    def load_config(self, config_path: str = "config/config.yaml") -> Dict[str, Any]:
        """تحميل ملف الإعدادات"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"ملف الإعدادات غير موجود: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as file:
            self._config = yaml.safe_load(file)
        
        # دمج مع متغيرات البيئة
        self._merge_env_vars()
        
        return self._config
    
    def _merge_env_vars(self):
        """دمج متغيرات البيئة مع الإعدادات"""
        for key, value in os.environ.items():
            if key.startswith('APP_'):
                config_key = key[4:].lower()
                if config_key in self._config:
                    self._config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد معين"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def config(self) -> Dict[str, Any]:
        """إرجاع جميع الإعدادات"""
        return self._config


# إنشاء نسخة واحدة من الإعدادات
config = Config()

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """دالة مساعدة لتحميل الإعدادات"""
    return config.load_config(config_path)