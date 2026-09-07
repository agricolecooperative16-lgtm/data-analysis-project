"""
نقطة الدخول الرئيسية لتطبيق تحليل البيانات
"""

import argparse
import sys
from pathlib import Path
from src.utils.logger import setup_logger
from src.utils.config import load_config
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner
from src.features.rfm import RFMAnalyzer
from src.analytics.kpis import KPIAnalyzer
from src.visualization.plots import Plotter

logger = setup_logger(__name__)


def main():
    """نقطة الدخول الرئيسية"""
    
    # تحليل وسائط سطر الأوامر
    parser = argparse.ArgumentParser(
        description="نظام تحليل المبيعات والعملاء",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  python main.py --file data/sales.csv --analyze sales
  python main.py --file data/sales.xlsx --analyze customers
  python main.py --file data/sales.csv --analyze both --output results.json
        """
    )
    
    parser.add_argument('--file', type=str, required=True,
                       help="مسار ملف البيانات (CSV أو Excel)")
    parser.add_argument('--analyze', choices=['sales', 'customers', 'both'],
                       default='both', help="نوع التحليل")
    parser.add_argument('--output', type=str, default=None,
                       help="مسار ملف النتائج (اختياري)")
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help="مسار ملف الإعدادات")
    
    args = parser.parse_args()
    
    try:
        # تحميل الإعدادات
        config = load_config(args.config)
        logger.info("تم تحميل الإعدادات بنجاح")
        
        # تحميل البيانات
        loader = DataLoader()
        
        if args.file.endswith('.csv'):
            df = loader.load_csv(args.file)
        elif args.file.endswith(('.xlsx', '.xls')):
            df = loader.load_excel(args.file)
        else:
            raise ValueError(f"نوع الملف غير معروف: {args.file}")
        
        logger.info(f"تم تحميل {len(df)} سجل")
        
        # تنظيف البيانات
        cleaner = DataCleaner()
        
        # تحويل التاريخ
        date_col = config['analysis']['date_column']
        if date_col in df.columns:
            df = cleaner.convert_dates(df, date_col)
        
        # إزالة المكررات
        df = cleaner.remove_duplicates(df)
        
        # حساب المبلغ الإجمالي
        if 'total_amount' not in df.columns:
            qty_col = config['analysis']['quantity_column']
            price_col = config['analysis']['price_column']
            if qty_col in df.columns and price_col in df.columns:
                df = cleaner.calculate_total_amount(
                    df, qty_col, price_col, 'total_amount'
                )
        
        # الحصول على أسماء الأعمدة من الإعدادات
        customer_id = config['analysis']['customer_id']
        transaction_id = config['analysis'].get('transaction_id', 'transaction_id')
        date_col = config['analysis']['date_column']
        amount_col = config['analysis'].get('amount_column', 'total_amount')
        
        # إجراء التحليل
        results = {}
        
        if args.analyze in ['sales', 'both']:
            logger.info("بدء تحليل المبيعات...")
            kpi_analyzer = KPIAnalyzer()
            kpis = kpi_analyzer.calculate_all_kpis(
                df, customer_id, transaction_id, date_col, amount_col
            )
            results['kpis'] = kpis
            logger.info(f"تم حساب الـ KPIs: {len(kpis)} مؤشر")
        
        if args.analyze in ['customers', 'both']:
            logger.info("بدء تحليل العملاء...")
            rfm_analyzer = RFMAnalyzer()
            rfm_results = rfm_analyzer.analyze_rfm(
                df, customer_id, date_col, amount_col,
                config['analysis']['rfm']['segments']
            )
            results['rfm'] = rfm_results
            logger.info("تم تحليل RFM بنجاح")
        
        # إنشاء التصورات
        logger.info("بدء إنشاء التصورات...")
        plotter = Plotter(
            fig_size=tuple(config['visualization']['figure_size']),
            palette=config['visualization']['color_palette'],
            dpi=config['visualization']['dpi'],
            save_figures=config['visualization']['save_figures'],
            figure_format=config['visualization']['figure_format']
        )
        
        # رسم المخططات
        if 'kpis' in results:
            plotter.plot_kpi_dashboard(results['kpis'])
        
        if 'rfm' in results:
            plotter.plot_rfm_distribution(results['rfm']['rfm_scores'])
            plotter.plot_customer_segments(results['rfm']['rfm_segments'])
        
        logger.info("تم إنشاء التصورات بنجاح")
        
        # حفظ النتائج
        if args.output:
            # هنا يمكن إضافة كود حفظ النتائج (JSON, CSV, إلخ)
            logger.info(f"سيتم حفظ النتائج في {args.output}")
            # TODO: حفظ النتائج
        
        logger.info("✅ تم إنجاز التحليل بنجاح!")
        
    except Exception as e:
        logger.error(f"❌ فشل تنفيذ التحليل: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())