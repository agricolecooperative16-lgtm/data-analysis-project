#!/usr/bin/env python
"""
تشغيل تطبيق Flask Dashboard
"""

from flask_app.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 تشغيل لوحة تحليل المبيعات")
    print("=" * 60)
    print("📊 افتح المتصفح على: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)