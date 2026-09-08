import pandas as pd
from pathlib import Path
import logging

# إعداد logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCleaner:
    REQUIRED_COLUMNS = ['customer_id', 'transaction_id', 'date', 'quantity', 'price', 'total_amount']
    DATETIME_COLUMNS = ['date']
    NUMERIC_COLUMNS = ['quantity', 'price', 'total_amount']

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.original_rows = len(df)
        self.cleaning_log = {
            'rows_before': self.original_rows,
            'rows_after': self.original_rows,
            'duplicates_removed': 0,
            'invalid_dates': 0,
            'missing_customers': 0,
            'negative_amounts': 0,
            'non_numeric_values': 0
        }

    def validate_columns(self):
        """التحقق من وجود جميع الأعمدة المطلوبة. في حال نقص أي عمود، يتم إيقاف التنفيذ."""
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols:
            error_msg = f"❌ الأعمدة الأساسية التالية مفقودة: {missing_cols}. لا يمكن متابعة التنظيف."
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("✅ جميع الأعمدة الأساسية موجودة.")
        return self

    # ... سيتم إضافة باقي الدوال هنا
    
    @staticmethod
    def convert_dates(df: pd.DataFrame, date_col: str, 
                      format: Optional[str] = None) -> pd.DataFrame:
        """
        تحويل عمود إلى نوع التاريخ
        
        Args:
            df: DataFrame المراد معالجته
            date_col: اسم عمود التاريخ
            format: صيغة التاريخ (اختياري)
        
        Returns:
            DataFrame مع عمود التاريخ المحول
        """
        if date_col not in df.columns:
            raise ValueError(f"العمود {date_col} غير موجود")
        
        df_copy = df.copy()
        
        try:
            if format:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], format=format)
            else:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            
            logger.info(f"تم تحويل {date_col} إلى نوع datetime بنجاح")
            return df_copy
        except Exception as e:
            logger.error(f"خطأ في تحويل التاريخ: {str(e)}")
            raise
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, 
                         subset: Optional[List[str]] = None,
                         keep: str = 'first') -> pd.DataFrame:
        """
        إزالة البيانات المكررة
        
        Args:
            df: DataFrame المراد معالجته
            subset: الأعمدة المستخدمة لتحديد التكرار
            keep: أي نسخة للاحتفاظ ('first', 'last', False)
        
        Returns:
            DataFrame بعد إزالة المكررات
        """
        df_copy = df.copy()
        initial_len = len(df_copy)
        df_copy = df_copy.drop_duplicates(subset=subset, keep=keep)
        removed = initial_len - len(df_copy)
        
        if removed > 0:
            logger.info(f"تم إزالة {removed} سجل مكرر")
        
        return df_copy
    
    @staticmethod
    def filter_outliers(df: pd.DataFrame, col: str, 
                        method: str = 'iqr',
                        threshold: float = 1.5) -> pd.DataFrame:
        """
        تصفية القيم الشاذة
        
        Args:
            df: DataFrame المراد معالجته
            col: اسم العمود المراد تصفية قيمه
            method: طريقة التصفية ('iqr', 'zscore')
            threshold: العتبة المستخدمة
        
        Returns:
            DataFrame بعد تصفية القيم الشاذة
        """
        if col not in df.columns:
            raise ValueError(f"العمود {col} غير موجود")
        
        df_copy = df.copy()
        initial_len = len(df_copy)
        
        if method == 'iqr':
            Q1 = df_copy[col].quantile(0.25)
            Q3 = df_copy[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df_copy = df_copy[(df_copy[col] >= lower_bound) & 
                             (df_copy[col] <= upper_bound)]
        
        elif method == 'zscore':
            mean = df_copy[col].mean()
            std = df_copy[col].std()
            df_copy = df_copy[abs((df_copy[col] - mean) / std) <= threshold]
        
        else:
            raise ValueError(f"الطريقة غير معروفة: {method}")
        
        removed = initial_len - len(df_copy)
        if removed > 0:
            logger.info(f"تمت إزالة {removed} قيمة شاذة من عمود {col}")
        
        return df_copy
    
    @staticmethod
    def calculate_total_amount(df: pd.DataFrame, 
                              quantity_col: str,
                              price_col: str,
                              new_col: str = 'total_amount') -> pd.DataFrame:
        """
        حساب المبلغ الإجمالي
        
        Args:
            df: DataFrame المراد معالجته
            quantity_col: اسم عمود الكمية
            price_col: اسم عمود السعر
            new_col: اسم العمود الجديد
        
        Returns:
            DataFrame مع العمود الجديد
        """
        if quantity_col not in df.columns or price_col not in df.columns:
            raise ValueError(f"الأعمدة {quantity_col} أو {price_col} غير موجودة")
        
        df_copy = df.copy()
        df_copy[new_col] = df_copy[quantity_col] * df_copy[price_col]
        logger.info(f"تم حساب العمود {new_col}")
        
        return df_copy

        def convert_and_validate_dates(self):
        """تحويل التواريخ والتحقق من صلاحيتها."""
        invalid_dates_mask = pd.to_datetime(self.df['date'], errors='coerce').isna()
        self.cleaning_log['invalid_dates'] = invalid_dates_mask.sum()
        if self.cleaning_log['invalid_dates'] > 0:
            logger.warning(f"⚠️ تم العثور على {self.cleaning_log['invalid_dates']} تاريخ غير صالح. سيتم حذف الصفوف.")
            self.df = self.df[~invalid_dates_mask]
        else:
            logger.info("✅ جميع التواريخ صالحة.")
        self.df['date'] = pd.to_datetime(self.df['date'])
        return self

    def handle_missing_customers(self):
        """معالجة قيم customer_id الفارغة."""
        missing_mask = self.df['customer_id'].isna()
        self.cleaning_log['missing_customers'] = missing_mask.sum()
        if self.cleaning_log['missing_customers'] > 0:
            logger.warning(f"⚠️ تم العثور على {self.cleaning_log['missing_customers']} customer_id فارغ. سيتم حذف الصفوف.")
            self.df = self.df[~missing_mask]
        else:
            logger.info("✅ لا توجد قيم customer_id فارغة.")
        return self

    def validate_and_clean_numerics(self):
        """التحقق من أن الأعمدة الرقمية قابلة للتحويل، وحذف الصفوف غير الصالحة."""
        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                # تحويل القيم غير الرقمية إلى NaN
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                invalid_mask = self.df[col].isna()
                self.cleaning_log['non_numeric_values'] += invalid_mask.sum()
                if invalid_mask.sum() > 0:
                    logger.warning(f"⚠️ تم العثور على {invalid_mask.sum()} قيمة غير رقمية في عمود '{col}'. سيتم حذف الصفوف.")
                    self.df = self.df[~invalid_mask]
        logger.info("✅ تم التحقق من الأعمدة الرقمية.")
        return self

    def handle_negative_values(self):
        """
        التعامل مع القيم السالبة في الأعمدة الرقمية.
        يتم تحديد ما إذا كانت سالبة تعني 'مرتجع' أم 'خطأ' بناءً على وجود عمود 'return_flag'.
        """
        # التحقق من وجود عمود يشير إلى المرتجعات، يمكنك تعديل اسم العمود حسب بياناتك
        return_col = None
        for col in self.df.columns:
            if 'return' in col.lower() or 'refund' in col.lower():
                return_col = col
                break

        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                negative_mask = self.df[col] < 0
                negative_count = negative_mask.sum()
                if negative_count > 0:
                    if return_col and return_col in self.df.columns:
                        # وجود عمود مرتجع: السالب يُعتبر مرتجعًا (نحتفظ به)
                        logger.info(f"ℹ️ تم العثور على {negative_count} قيمة سالبة في '{col}'. تم التعرف عليها كمرتجعات (بناءً على عمود '{return_col}').")
                        # يمكن هنا معالجة خاصة للمرتجعات إذا أردت
                    else:
                        # لا يوجد عمود مرتجع: السالب يُعتبر خطأ في البيانات (نحذف الصفوف)
                        self.cleaning_log['negative_amounts'] = negative_count
                        logger.warning(f"⚠️ تم العثور على {negative_count} قيمة سالبة في '{col}' (تُعتبر خطأ). سيتم حذف الصفوف.")
                        self.df = self.df[~negative_mask]
        return self

    def handle_duplicates(self):
        """معالجة المكررات بناءً على عمود 'transaction_id'."""
        if 'transaction_id' in self.df.columns:
            # التحقق من وجود مكررات في transaction_id
            duplicate_mask = self.df.duplicated(subset=['transaction_id'], keep=False)
            duplicate_count = duplicate_mask.sum()
            self.cleaning_log['duplicates_removed'] = duplicate_count
            
            if duplicate_count > 0:
                # التحقق مما إذا كانت هناك أعمدة إضافية تشير إلى منتجات مختلفة (مثل 'product_id')
                if 'product_id' in self.df.columns or 'item_id' in self.df.columns:
                    logger.info(f"ℹ️ تم العثور على {duplicate_count} صف مكرر في 'transaction_id'. ولكن توجد أعمدة منتجات، قد تكون صفوفًا لمنتجات مختلفة في نفس الطلب. سيتم الاحتفاظ بها.")
                else:
                    logger.warning(f"⚠️ تم العثور على {duplicate_count} صف مكرر في 'transaction_id' ولا توجد أعمدة منتجات. سيتم حذف المكررات (مع الاحتفاظ بالصف الأول).")
                    self.df = self.df.drop_duplicates(subset=['transaction_id'], keep='first')
        else:
            logger.info("ℹ️ لا يوجد عمود 'transaction_id'، سيتم تخطي فحص المكررات.")
        return self

    def generate_report(self):
        """إنشاء وعرض تقرير جودة البيانات."""
        self.cleaning_log['rows_after'] = len(self.df)
        report = f"""
        ==================================================
        📊 تقرير جودة البيانات (Data Quality Report)
        ==================================================
        ✅ الصفوف قبل التنظيف         : {self.cleaning_log['rows_before']:,}
        ❌ الصفوف بعد التنظيف          : {self.cleaning_log['rows_after']:,}
        --------------------------------------------------
        🗑️  المكررات المحذوفة          : {self.cleaning_log['duplicates_removed']:,}
        📅 التواريخ غير الصالحة        : {self.cleaning_log['invalid_dates']:,}
        👤 العملاء المفقودين (customer_id) : {self.cleaning_log['missing_customers']:,}
        🔢 القيم غير الرقمية           : {self.cleaning_log['non_numeric_values']:,}
        ➖ القيم السالبة (كأخطاء)     : {self.cleaning_log['negative_amounts']:,}
        ==================================================
        """
        logger.info(report)
        return self

    def clean(self):
        """تنفيذ عملية التنظيف الكاملة مع التحقق من الأعمدة."""
        try:
            self.validate_columns() \
                .convert_and_validate_dates() \
                .handle_missing_customers() \
                .validate_and_clean_numerics() \
                .handle_negative_values() \
                .handle_duplicates() \
                .generate_report()
            
            # التأكد من حساب total_amount (إذا لم يكن موجودًا)
            if 'total_amount' in self.df.columns and 'quantity' in self.df.columns and 'price' in self.df.columns:
                # مثال: إعادة حساب total_amount للتحقق
                calculated_total = self.df['quantity'] * self.df['price']
                # يمكن إضافة تحقق هنا
                pass
                
            logger.info("✅ انتهت عملية تنظيف البيانات بنجاح.")
            return self.df
        except ValueError as e:
            logger.error(f"❌ فشلت عملية التنظيف: {e}")
            raise