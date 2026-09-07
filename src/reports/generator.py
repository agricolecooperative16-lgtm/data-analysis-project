"""
إنشاء تقارير PDF احترافية
"""

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
import base64
from pathlib import Path

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ReportGenerator:
    """فئة لإنشاء تقارير PDF"""
    
    def __init__(self, title="تقرير تحليل المبيعات والعملاء"):
        self.title = title
        self.styles = getSampleStyleSheet()
        self._add_arabic_styles()
        
    def _add_arabic_styles(self):
        """إضافة أنماط تدعم العربية"""
        self.styles.add(ParagraphStyle(
            name='ArabicTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica',
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        ))
        self.styles.add(ParagraphStyle(
            name='ArabicHeading',
            parent=self.styles['Heading2'],
            fontName='Helvetica',
            fontSize=16,
            alignment=TA_RIGHT,
            spaceAfter=12,
            textColor=colors.HexColor('#3498db')
        ))
        self.styles.add(ParagraphStyle(
            name='ArabicBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_RIGHT,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            name='ArabicCenter',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
    
    def _create_chart(self, df, date_col, amount_col):
        """إنشاء رسم بياني للاتجاه"""
        fig, ax = plt.subplots(figsize=(8, 4))
        
        daily_sales = df.groupby(date_col)[amount_col].sum().reset_index()
        daily_sales = daily_sales.sort_values(date_col)
        
        ax.plot(daily_sales[date_col], daily_sales[amount_col], 
                marker='o', linewidth=2, color='#3498db')
        ax.set_title('اتجاه المبيعات', fontsize=14, fontweight='bold')
        ax.set_xlabel('التاريخ', fontsize=11)
        ax.set_ylabel('الإيرادات ($)', fontsize=11)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # حفظ كصورة
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_rfm_chart(self, rfm_df):
        """إنشاء رسم بياني لتحليل RFM"""
        fig, axes = plt.subplots(1, 3, figsize=(10, 4))
        
        components = ['r_score', 'f_score', 'm_score']
        titles = ['الحداثة (R)', 'التكرار (F)', 'القيمة (M)']
        colors = ['#e74c3c', '#3498db', '#2ecc71']
        
        for i, (comp, title, color) in enumerate(zip(components, titles, colors)):
            rfm_df[comp].value_counts().sort_index().plot(
                kind='bar', ax=axes[i], color=color
            )
            axes[i].set_title(title, fontsize=12)
            axes[i].set_xlabel('الدرجة', fontsize=10)
            axes[i].set_ylabel('عدد العملاء', fontsize=10)
        
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def generate_report(self, df, kpis, rfm_results, forecast_results=None):
        """إنشاء تقرير PDF كامل"""
        
        report_path = Path("reports/report.pdf")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(
            str(report_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # العنوان
        story.append(Paragraph("📊 تقرير تحليل المبيعات والعملاء", self.styles['ArabicTitle']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"تاريخ التقرير: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", 
                              self.styles['ArabicCenter']))
        story.append(Spacer(1, 1*cm))
        
        # 1. ملخص تنفيذي
        story.append(Paragraph("📈 الملخص التنفيذي", self.styles['ArabicHeading']))
        story.append(Spacer(1, 0.3*cm))
        
        summary_data = [
            ['مؤشر الأداء', 'القيمة'],
            ['إجمالي الإيرادات', f"${kpis['total_revenue']:,.2f}"],
            ['عدد العملاء', f"{kpis['unique_customers']:,}"],
            ['عدد المعاملات', f"{kpis['total_transactions']:,}"],
            ['متوسط قيمة السلة', f"${kpis['average_basket']:,.2f}"],
            ['متوسط قيمة العميل', f"${kpis['avg_customer_value']:,.2f}"],
            ['معدل الاحتفاظ', f"{kpis['retention_rate']*100:.1f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BACKGROUND', (0, 2), (-1, -1), colors.white),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*cm))
        
        # 2. تحليل المبيعات
        story.append(Paragraph("📊 تحليل المبيعات", self.styles['ArabicHeading']))
        story.append(Spacer(1, 0.3*cm))
        
        # رسم بياني للمبيعات
        chart_img = self._create_chart(df, 
                                       date_col='transaction_date',
                                       amount_col='total_amount')
        img = Image(chart_img, width=16*cm, height=9*cm)
        story.append(img)
        story.append(Spacer(1, 0.5*cm))
        
        # 3. تحليل العملاء (RFM)
        if rfm_results:
            story.append(Paragraph("👥 تحليل العملاء (RFM)", self.styles['ArabicHeading']))
            story.append(Spacer(1, 0.3*cm))
            
            rfm_df = rfm_results['rfm_scores']
            
            # إحصائيات RFM
            rfm_data = [
                ['المعامل', 'المتوسط', 'التقييم'],
                ['الحداثة (R)', f"{rfm_df['r_score'].mean():.1f}", 'من 5'],
                ['التكرار (F)', f"{rfm_df['f_score'].mean():.1f}", 'من 5'],
                ['القيمة (M)', f"{rfm_df['m_score'].mean():.1f}", 'من 5']
            ]
            
            rfm_table = Table(rfm_data, colWidths=[3*cm, 3*cm, 3*cm])
            rfm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (2, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(rfm_table)
            story.append(Spacer(1, 0.3*cm))
            
            # رسم بياني RFM
            rfm_chart = self._create_rfm_chart(rfm_df)
            img_rfm = Image(rfm_chart, width=16*cm, height=7*cm)
            story.append(img_rfm)
            story.append(Spacer(1, 0.5*cm))
            
            # توزيع الشرائح
            segment_counts = rfm_df['segment'].value_counts()
            seg_data = [['الشريحة', 'عدد العملاء', 'النسبة المئوية']]
            for seg, count in segment_counts.items():
                seg_data.append([
                    seg,
                    str(count),
                    f"{(count/len(rfm_df)*100):.1f}%"
                ])
            
            seg_table = Table(seg_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm])
            seg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (2, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(seg_table)
            story.append(Spacer(1, 0.5*cm))
        
        # 4. التنبؤ (إذا وجد)
        if forecast_results:
            story.append(PageBreak())
            story.append(Paragraph("🔮 التنبؤ بالمبيعات", self.styles['ArabicHeading']))
            story.append(Spacer(1, 0.3*cm))
            
            best_model = forecast_results['best_model']
            best_data = forecast_results[best_model]
            
            forecast_data = [
                ['المعيار', 'القيمة'],
                ['أفضل نموذج', best_data['model']],
                ['MAE', f"{best_data['mae']:.2f}"],
                ['RMSE', f"{best_data['rmse']:.2f}"],
                ['MAPE', f"{best_data['mape']:.1f}%"],
                ['R²', f"{(best_data['r2']*100):.1f}%"]
            ]
            
            forecast_table = Table(forecast_data, colWidths=[4*cm, 4*cm])
            forecast_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(forecast_table)
        
        # بناء التقرير
        doc.build(story)
        logger.info(f"✅ تم إنشاء التقرير: {report_path}")
        
        return str(report_path)