"""
دوال الرسم البياني والتصور
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Plotter:
    """فئة لإنشاء التصورات"""
    
    def __init__(self, fig_size: Tuple[int, int] = (12, 8),
                 palette: str = "Set2",
                 dpi: int = 100,
                 save_figures: bool = True,
                 figure_format: str = "png"):
        """
        تهيئة كائن التصور
        
        Args:
            fig_size: حجم الشكل
            palette: لوحة الألوان
            dpi: دقة الشكل
            save_figures: حفظ الأشكال
            figure_format: صيغة حفظ الأشكال
        """
        self.fig_size = fig_size
        self.palette = palette
        self.dpi = dpi
        self.save_figures = save_figures
        self.figure_format = figure_format
        
        # تعيين نمط seaborn
        sns.set_style("whitegrid")
        sns.set_palette(palette)
    
    def _save_figure(self, fig, name: str):
        """حفظ الشكل"""
        if self.save_figures:
            Path("reports/figures").mkdir(parents=True, exist_ok=True)
            file_path = Path(f"reports/figures/{name}.{self.figure_format}")
            fig.savefig(file_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"تم حفظ الشكل في {file_path}")
    
    def plot_sales_trend(self, df: pd.DataFrame, 
                        date_col: str,
                        amount_col: str,
                        title: str = "اتجاه المبيعات") -> plt.Figure:
        """
        رسم اتجاه المبيعات
        
        Args:
            df: DataFrame مع البيانات
            date_col: اسم عمود التاريخ
            amount_col: اسم عمود المبلغ
            title: عنوان الرسم
        
        Returns:
            كائن Figure
        """
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # تجميع البيانات حسب التاريخ
        daily_sales = df.groupby(date_col)[amount_col].sum().reset_index()
        
        ax.plot(daily_sales[date_col], daily_sales[amount_col], 
                marker='o', linewidth=2)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel("التاريخ", fontsize=12)
        ax.set_ylabel("الإيرادات", fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # تدوير تسميات المحور السيني
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        self._save_figure(fig, "sales_trend")
        
        return fig
    
    def plot_rfm_distribution(self, rfm_df: pd.DataFrame,
                             title: str = "توزيع درجات RFM") -> plt.Figure:
        """
        رسم توزيع درجات RFM
        
        Args:
            rfm_df: DataFrame مع درجات RFM
            title: عنوان الرسم
        
        Returns:
            كائن Figure
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # رسم كل مكون
        components = ['r_score', 'f_score', 'm_score']
        titles = ['الحداثة (Recency)', 'التكرار (Frequency)', 'القيمة (Monetary)']
        
        for i, (comp, title_comp) in enumerate(zip(components, titles)):
            rfm_df[comp].value_counts().sort_index().plot(
                kind='bar', ax=axes[i], color=sns.color_palette(self.palette)[i]
            )
            axes[i].set_title(f"{title_comp}\n{title_comp}", fontsize=12)
            axes[i].set_xlabel("الدرجة", fontsize=10)
            axes[i].set_ylabel("عدد العملاء", fontsize=10)
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        self._save_figure(fig, "rfm_distribution")
        
        return fig
    
    def plot_customer_segments(self, rfm_df: pd.DataFrame,
                              title: str = "شرائح العملاء") -> plt.Figure:
        """
        رسم شرائح العملاء
        
        Args:
            rfm_df: DataFrame مع شرائح العملاء
            title: عنوان الرسم
        
        Returns:
            كائن Figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # مخطط دائري
        segment_counts = rfm_df['segment'].value_counts()
        colors = sns.color_palette(self.palette, len(segment_counts))
        wedges, texts, autotexts = ax1.pie(
            segment_counts.values,
            labels=segment_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            explode=[0.05] * len(segment_counts)
        )
        ax1.set_title("توزيع العملاء حسب الشريحة", fontsize=12)
        
        # مخطط شريطي
        segment_counts.plot(kind='bar', ax=ax2, color=colors)
        ax2.set_title("عدد العملاء في كل شريحة", fontsize=12)
        ax2.set_xlabel("الشريحة", fontsize=10)
        ax2.set_ylabel("عدد العملاء", fontsize=10)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        self._save_figure(fig, "customer_segments")
        
        return fig
    
    def plot_kpi_dashboard(self, kpis: dict) -> plt.Figure:
        """
        إنشاء لوحة معلومات مؤشرات الأداء
        
        Args:
            kpis: قاموس يحتوي على مؤشرات الأداء
        
        Returns:
            كائن Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        # قائمة KPIs الرئيسية
        main_kpis = {
            'إجمالي الإيرادات': kpis.get('total_revenue', 0),
            'متوسط قيمة السلة': kpis.get('average_basket', 0),
            'عدد العملاء الفريدين': kpis.get('unique_customers', 0),
            'عدد المعاملات': kpis.get('total_transactions', 0)
        }
        
        # رسم كل KPI
        colors = sns.color_palette(self.palette, len(main_kpis))
        
        for i, (name, value) in enumerate(main_kpis.items()):
            ax = axes[i]
            
            if isinstance(value, (int, float)):
                # عرض الرقم مع تنسيق مناسب
                if value >= 1_000_000:
                    display_value = f"{value/1_000_000:.1f}M"
                elif value >= 1_000:
                    display_value = f"{value/1_000:.1f}K"
                else:
                    display_value = f"{value:,.0f}"
                
                ax.text(0.5, 0.5, display_value,
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize=28, fontweight='bold')
                ax.text(0.5, 0.3, name,
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize=14)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_facecolor('#f0f0f0')
                ax.set_xticks([])
                ax.set_yticks([])
            else:
                ax.text(0.5, 0.5, "N/A",
                       horizontalalignment='center',
                       verticalalignment='center',
                       fontsize=20)
                ax.set_title(name, fontsize=12)
        
        plt.suptitle("لوحة معلومات مؤشرات الأداء", fontsize=16, fontweight='bold')
        plt.tight_layout()
        self._save_figure(fig, "kpi_dashboard")
        
        return fig