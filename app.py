"""
تطبيق ويب متكامل لتحليل المبيعات والعملاء
"""

from flask import Flask, render_template, jsonify, send_file
import pandas as pd
import json
from pathlib import Path
from src.data.loader import DataLoader
from src.data.cleaner import DataCleaner
from src.analytics.kpis import KPIAnalyzer
from src.features.rfm import RFMAnalyzer
from src.utils.config import load_config
import traceback

app = Flask(__name__)

# تحميل الإعدادات
config = load_config()

# تحميل البيانات
loader = DataLoader()

# محاولة تحميل البيانات من ملفات مختلفة
data_file = Path("data/raw/sales_data.csv")
if not data_file.exists():
    data_file = Path("data/sales_data.csv")
    
if not data_file.exists():
    print("⚠️ ملف البيانات غير موجود!")
    print("الرجاء التأكد من وجود الملف في: data/raw/sales_data.csv")
    exit(1)

df = loader.load_csv(str(data_file))

# تنظيف البيانات
cleaner = DataCleaner()
date_col = config['analysis']['date_column']

if date_col in df.columns:
    df = cleaner.convert_dates(df, date_col)
else:
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_col = col
            df = cleaner.convert_dates(df, date_col)
            break

# حساب المبلغ الإجمالي
if 'total_amount' not in df.columns:
    qty_col = config['analysis']['quantity_column']
    price_col = config['analysis']['price_column']
    if qty_col in df.columns and price_col in df.columns:
        df = cleaner.calculate_total_amount(df, qty_col, price_col)

# الحصول على أسماء الأعمدة
customer_id = config['analysis']['customer_id']
amount_col = config['analysis'].get('amount_column', 'total_amount')

if amount_col not in df.columns:
    if 'total_amount' in df.columns:
        amount_col = 'total_amount'
    else:
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            amount_col = numeric_cols[-1]

print(f"✅ تم تحميل {len(df)} سجل")
print(f"📊 الأعمدة: {', '.join(df.columns)}")

# ====================
# الصفحة الرئيسية
# ====================
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>نظام تحليل المبيعات</title>
        <meta charset="UTF-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Arial; 
                background: #f0f2f5; 
                padding: 20px;
            }
            .container { 
                max-width: 1400px; 
                margin: auto; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { 
                color: #2c3e50; 
                border-bottom: 4px solid #3498db; 
                padding-bottom: 15px; 
                margin-bottom: 20px;
                font-size: 32px;
            }
            .nav-links {
                display: flex;
                gap: 10px;
                margin: 15px 0 25px;
                flex-wrap: wrap;
            }
            .nav-links a {
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                display: inline-block;
                transition: opacity 0.3s;
            }
            .nav-links a:hover { opacity: 0.8; }
            .btn-primary { background: #3498db; color: white; }
            .btn-success { background: #27ae60; color: white; }
            .btn-warning { background: #e67e22; color: white; }
            .btn-danger { background: #e74c3c; color: white; }
            .btn-info { background: #1abc9c; color: white; }
            .btn-report { 
                background: #8e44ad; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                font-size: 14px;
                transition: opacity 0.3s;
            }
            .btn-report:hover { opacity: 0.8; }
            .kpi-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 30px 0;
            }
            .kpi-card { 
                padding: 25px; 
                border-radius: 12px; 
                text-align: center;
                color: white;
                transition: transform 0.3s;
            }
            .kpi-card:hover { transform: translateY(-5px); }
            .kpi-card:nth-child(1) { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .kpi-card:nth-child(2) { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .kpi-card:nth-child(3) { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            .kpi-card:nth-child(4) { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
            .kpi-value { font-size: 32px; font-weight: bold; margin-bottom: 8px; }
            .kpi-label { font-size: 14px; opacity: 0.9; }
            .loading { text-align: center; padding: 50px; font-size: 18px; color: #666; }
            .data-info {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border-right: 4px solid #3498db;
            }
            .report-status {
                margin: 15px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-right: 4px solid #8e44ad;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 12px;
            }
            #chart-container {
                margin: 20px 0;
                padding: 20px;
                background: #fafafa;
                border-radius: 10px;
            }
            .btn-download {
                display: inline-block;
                padding: 8px 16px;
                background: #27ae60;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 5px;
                font-size: 12px;
            }
            .btn-download:hover { background: #219a52; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 نظام تحليل المبيعات والعملاء</h1>
            
            <div class="nav-links">
                <a href="/" class="btn-primary">📊 الرئيسية</a>
                <a href="/customers" class="btn-success">👥 تحليل العملاء (RFM)</a>
                <a href="/forecast" class="btn-warning">🔮 التنبؤ بالمبيعات</a>
                <a href="/seasonality" class="btn-info">🌦️ التحليل الموسمي</a>
                <button onclick="generateReport()" class="btn-report">📄 توليد تقرير PDF</button>
            </div>
            
            <div class="data-info">
                📁 البيانات: <span id="dataInfo">جاري التحميل...</span>
            </div>
            
            <div class="report-status" id="reportStatus">
                📄 جاهز لتوليد تقرير PDF
            </div>
            
            <div class="kpi-grid" id="kpis">
                <div class="loading">⏳ جاري تحميل المؤشرات...</div>
            </div>
            
            <div id="chart-container">
                <div class="loading">⏳ جاري تحميل الرسوم البيانية...</div>
            </div>
            
            <div class="footer">
                نظام تحليل المبيعات والعملاء | تم التحديث: <span id="updateTime"></span>
            </div>
        </div>
        
        <script>
            document.getElementById('updateTime').textContent = new Date().toLocaleString('ar-SA');
            
            // تحميل مؤشرات الأداء
            fetch('/api/kpis')
                .then(response => response.json())
                .then(data => {
                    const kpis = data.kpis;
                    const grid = document.getElementById('kpis');
                    grid.innerHTML = '';
                    
                    const items = [
                        {label: '💰 إجمالي الإيرادات', value: '$' + (kpis.total_revenue || 0).toFixed(2)},
                        {label: '👥 عدد العملاء', value: kpis.unique_customers || 0},
                        {label: '📦 عدد المعاملات', value: kpis.total_transactions || 0},
                        {label: '🛒 متوسط السلة', value: '$' + (kpis.average_basket || 0).toFixed(2)}
                    ];
                    
                    items.forEach(item => {
                        const card = document.createElement('div');
                        card.className = 'kpi-card';
                        card.innerHTML = `
                            <div class="kpi-value">${item.value}</div>
                            <div class="kpi-label">${item.label}</div>
                        `;
                        grid.appendChild(card);
                    });
                    
                    document.getElementById('dataInfo').textContent = 
                        `${kpis.total_transactions || 0} معاملة، ${kpis.unique_customers || 0} عميل`;
                })
                .catch(error => {
                    document.getElementById('kpis').innerHTML = 
                        '<div class="loading">❌ خطأ في تحميل البيانات</div>';
                });
            
            // تحميل اتجاه المبيعات
            fetch('/api/sales_trend')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('chart-container');
                    if (data.data && data.data.length > 0) {
                        const dates = data.data.map(d => d.date);
                        const values = data.data.map(d => d.sales);
                        const maxVal = Math.max(...values) * 1.1;
                        
                        const canvas = document.createElement('canvas');
                        canvas.width = 800;
                        canvas.height = 300;
                        container.innerHTML = '';
                        container.appendChild(canvas);
                        
                        const ctx = canvas.getContext('2d');
                        const width = canvas.width - 60;
                        const height = canvas.height - 60;
                        
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        
                        // رسم المحاور
                        ctx.strokeStyle = '#333';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(30, 20);
                        ctx.lineTo(30, height + 20);
                        ctx.lineTo(width + 30, height + 20);
                        ctx.stroke();
                        
                        // رسم البيانات
                        ctx.strokeStyle = '#3498db';
                        ctx.lineWidth = 3;
                        ctx.beginPath();
                        values.forEach((val, i) => {
                            const x = 30 + (i / (values.length - 1)) * width;
                            const y = height + 20 - (val / maxVal) * height;
                            if (i === 0) ctx.moveTo(x, y);
                            else ctx.lineTo(x, y);
                        });
                        ctx.stroke();
                        
                        // نقاط البيانات
                        values.forEach((val, i) => {
                            const x = 30 + (i / (values.length - 1)) * width;
                            const y = height + 20 - (val / maxVal) * height;
                            ctx.fillStyle = '#e74c3c';
                            ctx.beginPath();
                            ctx.arc(x, y, 5, 0, 2 * Math.PI);
                            ctx.fill();
                        });
                        
                        ctx.fillStyle = '#333';
                        ctx.font = '16px Arial';
                        ctx.textAlign = 'center';
                        ctx.fillText('📈 اتجاه المبيعات اليومية', canvas.width/2, 15);
                    } else {
                        container.innerHTML = '<div class="loading">📊 لا توجد بيانات كافية</div>';
                    }
                })
                .catch(error => {
                    document.getElementById('chart-container').innerHTML = 
                        '<div class="loading">❌ خطأ في تحميل الرسم البياني</div>';
                });
            
            // توليد تقرير PDF
            function generateReport() {
                if (confirm('هل تريد توليد تقرير PDF كامل؟')) {
                    const statusDiv = document.getElementById('reportStatus');
                    statusDiv.innerHTML = '⏳ جاري توليد التقرير... يرجى الانتظار...';
                    statusDiv.style.borderRightColor = '#f39c12';
                    
                    fetch('/api/generate_report')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                statusDiv.innerHTML = `
                                    ✅ تم إنشاء التقرير بنجاح! 
                                    <a href="/download_report" class="btn-download">📥 تحميل التقرير</a>
                                `;
                                statusDiv.style.borderRightColor = '#27ae60';
                            } else {
                                statusDiv.innerHTML = '❌ خطأ: ' + data.error;
                                statusDiv.style.borderRightColor = '#e74c3c';
                            }
                        })
                        .catch(error => {
                            statusDiv.innerHTML = '❌ خطأ: ' + error.message;
                            statusDiv.style.borderRightColor = '#e74c3c';
                        });
                }
            }
            
            // جعل الدالة متاحة عالمياً
            window.generateReport = generateReport;
        </script>
    </body>
    </html>
    """

# ====================
# API: مؤشرات الأداء
# ====================
@app.route('/api/kpis')
def api_kpis():
    """API لمؤشرات الأداء"""
    try:
        kpi_analyzer = KPIAnalyzer()
        
        transaction_id = config['analysis'].get('transaction_id', 'transaction_id')
        if transaction_id not in df.columns:
            transaction_id = df.columns[0]
        
        kpis = kpi_analyzer.calculate_all_kpis(
            df,
            customer_id,
            transaction_id,
            date_col,
            amount_col
        )
        
        result = {}
        for key, value in kpis.items():
            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        
        return jsonify({'kpis': result})
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# API: اتجاه المبيعات
# ====================
@app.route('/api/sales_trend')
def api_sales_trend():
    """API لاتجاه المبيعات"""
    try:
        daily_sales = df.groupby(date_col)[amount_col].sum().reset_index()
        daily_sales.columns = ['date', 'sales']
        daily_sales['date'] = daily_sales['date'].dt.strftime('%Y-%m-%d')
        
        if len(daily_sales) > 30:
            daily_sales = daily_sales.tail(30)
        
        return jsonify({
            'data': daily_sales.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# API: تحليل RFM
# ====================
@app.route('/api/rfm')
def api_rfm():
    """API لتحليل RFM"""
    try:
        rfm_analyzer = RFMAnalyzer()
        rfm_results = rfm_analyzer.analyze_rfm(
            df,
            customer_id,
            date_col,
            amount_col,
            config['analysis']['rfm']['segments']
        )
        
        rfm_df = rfm_results['rfm_scores']
        
        segment_stats = rfm_df['segment'].value_counts().to_dict()
        top_customers = rfm_df.nlargest(10, 'monetary')[[customer_id, 'monetary', 'segment', 'rfm_score']].to_dict('records')
        
        score_distribution = {
            'r_scores': rfm_df['r_score'].value_counts().sort_index().to_dict(),
            'f_scores': rfm_df['f_score'].value_counts().sort_index().to_dict(),
            'm_scores': rfm_df['m_score'].value_counts().sort_index().to_dict()
        }
        
        return jsonify({
            'segment_stats': segment_stats,
            'avg_scores': {
                'recency': float(rfm_df['r_score'].mean()),
                'frequency': float(rfm_df['f_score'].mean()),
                'monetary': float(rfm_df['m_score'].mean()),
                'overall': float(rfm_df['rfm_score'].mean())
            },
            'top_customers': top_customers,
            'score_distribution': score_distribution,
            'total_customers': len(rfm_df)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# API: التنبؤ بالمبيعات
# ====================
@app.route('/api/forecast')
def api_forecast():
    """API للتنبؤ بالمبيعات"""
    try:
        from src.models.forecasting import SalesForecaster
        
        forecaster = SalesForecaster(test_size=0.2)
        results = forecaster.forecast_all(df, date_col, amount_col)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# API: التحليل الموسمي
# ====================
@app.route('/api/seasonality')
def api_seasonality():
    """API للتحليل الموسمي"""
    try:
        from src.analytics.seasonality import SeasonalityAnalyzer
        
        analyzer = SeasonalityAnalyzer()
        results = analyzer.analyze_seasonality(df, date_col, amount_col)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# API: توليد تقرير PDF
# ====================
@app.route('/api/generate_report')
def api_generate_report():
    """توليد تقرير PDF"""
    try:
        from src.reports.generator import ReportGenerator
        from src.models.forecasting import SalesForecaster
        
        # تحليل البيانات
        kpi_analyzer = KPIAnalyzer()
        transaction_id = config['analysis'].get('transaction_id', 'transaction_id')
        if transaction_id not in df.columns:
            transaction_id = df.columns[0]
        
        kpis = kpi_analyzer.calculate_all_kpis(
            df, customer_id, transaction_id, date_col, amount_col
        )
        
        # تحليل RFM
        rfm_analyzer = RFMAnalyzer()
        rfm_results = rfm_analyzer.analyze_rfm(
            df, customer_id, date_col, amount_col,
            config['analysis']['rfm']['segments']
        )
        
        # التنبؤ
        forecaster = SalesForecaster(test_size=0.2)
        forecast_results = forecaster.forecast_all(df, date_col, amount_col)
        
        # توليد التقرير
        generator = ReportGenerator()
        report_path = generator.generate_report(
            df, kpis, rfm_results, forecast_results
        )
        
        return jsonify({
            'success': True,
            'report_path': report_path,
            'message': 'تم إنشاء التقرير بنجاح'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# تحميل التقرير
# ====================
@app.route('/download_report')
def download_report():
    """تحميل التقرير PDF"""
    try:
        report_path = Path("reports/report.pdf")
        if report_path.exists():
            return send_file(
                report_path,
                as_attachment=True,
                download_name="تقرير_تحليل_المبيعات.pdf"
            )
        else:
            return "التقرير غير موجود. يرجى توليده أولاً.", 404
    except Exception as e:
        return str(e), 500

# ====================
# صفحة تحليل العملاء
# ====================
@app.route('/customers')
def customers_page():
    """صفحة تحليل العملاء"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>تحليل العملاء - RFM</title>
        <meta charset="UTF-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Arial; background: #f0f2f5; padding: 20px; }
            .container { max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 15px; }
            h1 { color: #2c3e50; border-bottom: 4px solid #27ae60; padding-bottom: 15px; margin-bottom: 20px; }
            h2 { color: #2c3e50; margin: 25px 0 15px 0; }
            .nav-links { display: flex; gap: 10px; margin: 15px 0 25px; flex-wrap: wrap; }
            .nav-links a { padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; }
            .nav-links .btn-primary { background: #3498db; color: white; }
            .nav-links .btn-success { background: #27ae60; color: white; }
            .nav-links .btn-warning { background: #e67e22; color: white; }
            .nav-links .btn-info { background: #1abc9c; color: white; }
            .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
            .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-right: 4px solid #3498db; }
            .card h3 { color: #555; font-size: 14px; margin-bottom: 8px; }
            .card .value { font-size: 28px; font-weight: bold; color: #2c3e50; }
            .card .sub { font-size: 12px; color: #888; margin-top: 5px; }
            .segment-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
            .segment-vip { background: #ffd700; color: #333; }
            .segment-loyal { background: #4CAF50; color: white; }
            .segment-potential { background: #2196F3; color: white; }
            .segment-at_risk { background: #ff9800; color: white; }
            .segment-lost { background: #f44336; color: white; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { padding: 12px 15px; text-align: right; border-bottom: 1px solid #eee; }
            th { background: #2c3e50; color: white; }
            tr:hover { background: #f5f5f5; }
            .loading { text-align: center; padding: 40px; color: #888; font-size: 18px; }
            .score-bars { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; }
            .score-group { flex: 1; min-width: 150px; }
            .score-group h4 { text-align: center; color: #555; margin-bottom: 10px; }
            .bar-chart { display: flex; align-items: flex-end; height: 150px; gap: 8px; padding: 10px 0; justify-content: center; }
            .bar-item { display: flex; flex-direction: column; align-items: center; }
            .bar { width: 30px; border-radius: 4px 4px 0 0; min-height: 5px; transition: height 0.5s; }
            .bar-label { font-size: 11px; color: #666; margin-top: 5px; }
            @media (max-width: 768px) {
                .grid-4 { grid-template-columns: repeat(2, 1fr); }
                .grid-3 { grid-template-columns: 1fr; }
                .score-bars { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-links">
                <a href="/" class="btn-primary">📊 الرئيسية</a>
                <a href="/customers" class="btn-success">👥 تحليل العملاء (RFM)</a>
                <a href="/forecast" class="btn-warning">🔮 التنبؤ بالمبيعات</a>
                <a href="/seasonality" class="btn-info">🌦️ التحليل الموسمي</a>
            </div>
            <h1>👥 تحليل العملاء - RFM</h1>
            
            <div id="loading" class="loading">⏳ جاري تحليل بيانات العملاء...</div>
            
            <div id="content" style="display:none;">
                <div class="grid-4" id="quickStats"></div>
                <h2>📊 متوسط درجات RFM</h2>
                <div class="grid-3" id="rfmScores"></div>
                <h2>📈 توزيع شرائح العملاء</h2>
                <div class="grid-3" id="segmentDistribution"></div>
                <h2>📊 توزيع درجات RFM</h2>
                <div class="score-bars" id="scoreDistribution"></div>
                <h2>🏆 أفضل 10 عملاء</h2>
                <table>
                    <thead><tr><th>#</th><th>معرف العميل</th><th>القيمة الإجمالية</th><th>درجة RFM</th><th>الشريحة</th></tr></thead>
                    <tbody id="topCustomers"></tbody>
                </table>
            </div>
        </div>
        
        <script>
            fetch('/api/rfm')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    const stats = [
                        {label: '👥 إجمالي العملاء', value: data.total_customers},
                        {label: '📊 عدد الشرائح', value: Object.keys(data.segment_stats).length},
                        {label: '🏆 VIP', value: data.segment_stats['vip'] || 0},
                        {label: '⚠️ العملاء المهددون', value: (data.segment_stats['at_risk'] || 0) + (data.segment_stats['lost'] || 0)}
                    ];
                    const statsContainer = document.getElementById('quickStats');
                    stats.forEach(s => {
                        const div = document.createElement('div');
                        div.className = 'card';
                        div.innerHTML = `<h3>${s.label}</h3><div class="value">${s.value}</div>`;
                        statsContainer.appendChild(div);
                    });
                    
                    const scores = [
                        {label: '🔄 الحداثة (R)', value: data.avg_scores.recency.toFixed(1), sub: 'من 5'},
                        {label: '📊 التكرار (F)', value: data.avg_scores.frequency.toFixed(1), sub: 'من 5'},
                        {label: '💰 القيمة (M)', value: data.avg_scores.monetary.toFixed(1), sub: 'من 5'}
                    ];
                    const scoresContainer = document.getElementById('rfmScores');
                    scores.forEach(s => {
                        const div = document.createElement('div');
                        div.className = 'card';
                        div.innerHTML = `<h3>${s.label}</h3><div class="value">${s.value}</div><div class="sub">${s.sub}</div>`;
                        scoresContainer.appendChild(div);
                    });
                    
                    const segments = Object.keys(data.segment_stats);
                    const colors = {vip: '#ffd700', loyal: '#4CAF50', potential: '#2196F3', at_risk: '#ff9800', lost: '#f44336'};
                    const icons = {vip: '⭐', loyal: '💎', potential: '📈', at_risk: '⚠️', lost: '❌'};
                    const segContainer = document.getElementById('segmentDistribution');
                    segments.forEach(seg => {
                        const div = document.createElement('div');
                        div.className = 'card';
                        div.style.borderRightColor = colors[seg] || '#9e9e9e';
                        div.innerHTML = `<h3>${icons[seg] || '📌'} ${seg}</h3><div class="value">${data.segment_stats[seg]}</div><div class="sub">عميل</div>`;
                        segContainer.appendChild(div);
                    });
                    
                    const distContainer = document.getElementById('scoreDistribution');
                    const scoreTypes = [
                        {key: 'r_scores', label: 'الحداثة (R)'},
                        {key: 'f_scores', label: 'التكرار (F)'},
                        {key: 'm_scores', label: 'القيمة (M)'}
                    ];
                    scoreTypes.forEach(type => {
                        const group = document.createElement('div');
                        group.className = 'score-group';
                        let html = `<h4>${type.label}</h4><div class="bar-chart">`;
                        const scoresData = data.score_distribution[type.key];
                        const maxVal = Math.max(...Object.values(scoresData));
                        const barColors = ['#f44336', '#ff9800', '#2196F3', '#4CAF50', '#27ae60'];
                        for (let i = 1; i <= 5; i++) {
                            const val = scoresData[i] || 0;
                            const height = maxVal > 0 ? (val / maxVal) * 120 : 0;
                            html += `<div class="bar-item"><div class="bar" style="height: ${height}px; background: ${barColors[i-1]};"></div><div class="bar-label">${i}</div></div>`;
                        }
                        html += '</div>';
                        group.innerHTML = html;
                        distContainer.appendChild(group);
                    });
                    
                    const tbody = document.getElementById('topCustomers');
                    data.top_customers.forEach((c, i) => {
                        const row = document.createElement('tr');
                        const segClass = `segment-${c.segment}`;
                        row.innerHTML = `<td>${i+1}</td><td><strong>${c.customer_id}</strong></td><td>$${c.monetary.toFixed(2)}</td><td>${c.rfm_score.toFixed(1)}</td><td><span class="segment-badge ${segClass}">${c.segment}</span></td>`;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    document.getElementById('loading').innerHTML = '❌ خطأ: ' + error.message;
                });
        </script>
    </body>
    </html>
    """

# ====================
# صفحة التنبؤ
# ====================
@app.route('/forecast')
def forecast_page():
    """صفحة التنبؤ بالمبيعات"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>التنبؤ بالمبيعات</title>
        <meta charset="UTF-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Arial; background: #f0f2f5; padding: 20px; }
            .container { max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 15px; }
            h1 { color: #2c3e50; border-bottom: 4px solid #e67e22; padding-bottom: 15px; margin-bottom: 20px; }
            h2 { color: #2c3e50; margin: 25px 0 15px 0; }
            .nav-links { display: flex; gap: 10px; margin: 15px 0 25px; flex-wrap: wrap; }
            .nav-links a { padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; }
            .nav-links .btn-primary { background: #3498db; color: white; }
            .nav-links .btn-success { background: #27ae60; color: white; }
            .nav-links .btn-warning { background: #e67e22; color: white; }
            .nav-links .btn-info { background: #1abc9c; color: white; }
            .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-right: 4px solid #e67e22; }
            .card h3 { color: #555; font-size: 14px; margin-bottom: 8px; }
            .card .value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .card .sub { font-size: 12px; color: #888; margin-top: 5px; }
            .best { border-right-color: #27ae60; background: #e8f8f5; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { padding: 12px 15px; text-align: right; border-bottom: 1px solid #eee; }
            th { background: #2c3e50; color: white; }
            tr:hover { background: #f5f5f5; }
            .loading { text-align: center; padding: 40px; color: #888; font-size: 18px; }
            .chart-container { background: #fafafa; padding: 20px; border-radius: 10px; margin: 15px 0; }
            canvas { width: 100% !important; height: auto !important; max-height: 400px; }
            .model-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .model-best { background: #27ae60; color: white; }
            .model-other { background: #95a5a6; color: white; }
            @media (max-width: 768px) {
                .grid-3 { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-links">
                <a href="/" class="btn-primary">📊 الرئيسية</a>
                <a href="/customers" class="btn-success">👥 تحليل العملاء (RFM)</a>
                <a href="/forecast" class="btn-warning">🔮 التنبؤ بالمبيعات</a>
                <a href="/seasonality" class="btn-info">🌦️ التحليل الموسمي</a>
            </div>
            <h1>🔮 التنبؤ بالمبيعات</h1>
            
            <div id="loading" class="loading">⏳ جاري حساب التنبؤات...</div>
            
            <div id="content" style="display:none;">
                <h2>📊 مقارنة أداء النماذج</h2>
                <div class="grid-3" id="modelComparison"></div>
                
                <h2>📈 نتائج التنبؤ</h2>
                <div class="chart-container">
                    <canvas id="forecastChart"></canvas>
                </div>
                
                <h2>📋 تفاصيل النماذج</h2>
                <table>
                    <thead><tr><th>النموذج</th><th>MAE</th><th>RMSE</th><th>MAPE</th><th>R²</th><th>الحالة</th></tr></thead>
                    <tbody id="modelDetails"></tbody>
                </table>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            fetch('/api/forecast')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    const models = [
                        {key: 'linear', label: '📈 الانحدار الخطي'},
                        {key: 'polynomial', label: '📊 متعدد الحدود (deg=2)'},
                        {key: 'polynomial_3', label: '📊 متعدد الحدود (deg=3)'}
                    ];
                    
                    const compContainer = document.getElementById('modelComparison');
                    models.forEach(m => {
                        const modelData = data[m.key];
                        const div = document.createElement('div');
                        div.className = 'card' + (m.key === data.best_model ? ' best' : '');
                        div.innerHTML = `<h3>${m.label}</h3><div class="value">${modelData.mae.toFixed(2)}</div><div class="sub">MAE ${m.key === data.best_model ? '⭐ أفضل' : ''}</div>`;
                        compContainer.appendChild(div);
                    });
                    
                    const tbody = document.getElementById('modelDetails');
                    const modelNames = {linear: 'الانحدار الخطي', polynomial: 'متعدد الحدود (deg=2)', polynomial_3: 'متعدد الحدود (deg=3)'};
                    models.forEach(m => {
                        const modelData = data[m.key];
                        const row = document.createElement('tr');
                        const isBest = m.key === data.best_model;
                        row.innerHTML = `<td><strong>${modelNames[m.key]}</strong></td><td>${modelData.mae.toFixed(2)}</td><td>${modelData.rmse.toFixed(2)}</td><td>${modelData.mape.toFixed(1)}%</td><td>${(modelData.r2 * 100).toFixed(1)}%</td><td><span class="model-badge ${isBest ? 'model-best' : 'model-other'}">${isBest ? '⭐ الأفضل' : ''}</span></td>`;
                        tbody.appendChild(row);
                    });
                    
                    const best = data[data.best_model];
                    const ctx = document.getElementById('forecastChart').getContext('2d');
                    const actual = best.actual;
                    const predictions = best.predictions;
                    const labels = actual.map((_, i) => i + 1);
                    
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [
                                {label: 'القيم الفعلية', data: actual, borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,0.1)', fill: true, tension: 0.4},
                                {label: 'التنبؤات', data: predictions, borderColor: '#e67e22', backgroundColor: 'rgba(230,126,34,0.1)', fill: true, tension: 0.4, borderDash: [5, 5]}
                            ]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { position: 'top' } },
                            scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toFixed(0) } } }
                        }
                    });
                })
                .catch(error => {
                    document.getElementById('loading').innerHTML = '❌ خطأ: ' + error.message;
                });
        </script>
    </body>
    </html>
    """

# ====================
# صفحة التحليل الموسمي
# ====================
@app.route('/seasonality')
def seasonality_page():
    """صفحة التحليل الموسمي"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>التحليل الموسمي</title>
        <meta charset="UTF-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Arial; background: #f0f2f5; padding: 20px; }
            .container { max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 15px; }
            h1 { color: #2c3e50; border-bottom: 4px solid #1abc9c; padding-bottom: 15px; margin-bottom: 20px; }
            h2 { color: #2c3e50; margin: 25px 0 15px 0; }
            .nav-links { display: flex; gap: 10px; margin: 15px 0 25px; flex-wrap: wrap; }
            .nav-links a { padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; }
            .nav-links .btn-primary { background: #3498db; color: white; }
            .nav-links .btn-success { background: #27ae60; color: white; }
            .nav-links .btn-warning { background: #e67e22; color: white; }
            .nav-links .btn-info { background: #1abc9c; color: white; }
            .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
            .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
            .card { background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-right: 4px solid #1abc9c; }
            .card h3 { color: #555; font-size: 14px; margin-bottom: 8px; }
            .card .value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .card .sub { font-size: 12px; color: #888; margin-top: 5px; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th, td { padding: 12px 15px; text-align: right; border-bottom: 1px solid #eee; }
            th { background: #2c3e50; color: white; }
            tr:hover { background: #f5f5f5; }
            .loading { text-align: center; padding: 40px; color: #888; font-size: 18px; }
            .highlight-best { color: #27ae60; font-weight: bold; }
            .highlight-worst { color: #e74c3c; font-weight: bold; }
            .seasonal-tag { display: inline-block; padding: 4px 16px; border-radius: 20px; font-weight: bold; }
            .seasonal-tag.seasonal { background: #3498db; color: white; }
            .seasonal-tag.non-seasonal { background: #95a5a6; color: white; }
            @media (max-width: 768px) {
                .grid-3 { grid-template-columns: 1fr; }
                .grid-2 { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-links">
                <a href="/" class="btn-primary">📊 الرئيسية</a>
                <a href="/customers" class="btn-success">👥 تحليل العملاء (RFM)</a>
                <a href="/forecast" class="btn-warning">🔮 التنبؤ بالمبيعات</a>
                <a href="/seasonality" class="btn-info">🌦️ التحليل الموسمي</a>
            </div>
            <h1>🌦️ التحليل الموسمي</h1>
            
            <div id="loading" class="loading">⏳ جاري تحليل الموسمية...</div>
            
            <div id="content" style="display:none;">
                <!-- النتائج الرئيسية -->
                <div class="grid-3" id="seasonalStats"></div>
                
                <!-- التحليل الشهري -->
                <h2>📊 التحليل الشهري</h2>
                <table>
                    <thead><tr><th>الشهر</th><th>إجمالي المبيعات</th><th>متوسط المبيعات</th><th>عدد المعاملات</th></tr></thead>
                    <tbody id="monthlyTable"></tbody>
                </table>
                
                <!-- التحليل الأسبوعي -->
                <h2>📊 التحليل الأسبوعي</h2>
                <table>
                    <thead><tr><th>اليوم</th><th>إجمالي المبيعات</th><th>متوسط المبيعات</th><th>عدد المعاملات</th></tr></thead>
                    <tbody id="weeklyTable"></tbody>
                </table>
                
                <!-- أفضل وأسوأ الشهور -->
                <div class="grid-2">
                    <div class="card" style="border-right-color: #27ae60;">
                        <h3>🌟 أفضل شهر</h3>
                        <div class="value highlight-best" id="bestMonth">-</div>
                        <div class="sub">أعلى مبيعات</div>
                    </div>
                    <div class="card" style="border-right-color: #e74c3c;">
                        <h3>📉 أسوأ شهر</h3>
                        <div class="value highlight-worst" id="worstMonth">-</div>
                        <div class="sub">أقل مبيعات</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            fetch('/api/seasonality')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    // إحصائيات سريعة
                    const stats = [
                        {label: '📊 النمط الموسمي', value: data.seasonal_pattern || 'غير محدد', sub: data.seasonal_pattern === 'موسمي' ? '🌊 هناك موسمية' : '📊 نمط منتظم'},
                        {label: '🌟 أفضل شهر', value: data.best_month || '-'},
                        {label: '📉 أسوأ شهر', value: data.worst_month || '-'}
                    ];
                    const statsContainer = document.getElementById('seasonalStats');
                    stats.forEach(s => {
                        const div = document.createElement('div');
                        div.className = 'card';
                        const tagClass = s.value === 'موسمي' ? 'seasonal-tag seasonal' : 'seasonal-tag non-seasonal';
                        if (s.label === '📊 النمط الموسمي') {
                            div.innerHTML = `<h3>${s.label}</h3><div class="value"><span class="${tagClass}">${s.value}</span></div><div class="sub">${s.sub}</div>`;
                        } else {
                            div.innerHTML = `<h3>${s.label}</h3><div class="value">${s.value}</div><div class="sub">${s.sub || ''}</div>`;
                        }
                        statsContainer.appendChild(div);
                    });
                    
                    // التحليل الشهري
                    const monthlyTbody = document.getElementById('monthlyTable');
                    data.monthly.forEach(m => {
                        const row = document.createElement('tr');
                        const isBest = m.month_name === data.best_month;
                        const isWorst = m.month_name === data.worst_month;
                        let style = '';
                        if (isBest) style = 'background: #e8f8e8;';
                        if (isWorst) style = 'background: #fde8e8;';
                        row.style = style;
                        row.innerHTML = `
                            <td><strong>${m.month_name}</strong> ${isBest ? '🌟' : ''} ${isWorst ? '📉' : ''}</td>
                            <td>$${m.total_sales.toFixed(2)}</td>
                            <td>$${m.avg_sales.toFixed(2)}</td>
                            <td>${m.transactions}</td>
                        `;
                        monthlyTbody.appendChild(row);
                    });
                    
                    // التحليل الأسبوعي
                    const weeklyTbody = document.getElementById('weeklyTable');
                    data.weekly.forEach(w => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><strong>${w.day_name}</strong></td>
                            <td>$${w.total_sales.toFixed(2)}</td>
                            <td>$${w.avg_sales.toFixed(2)}</td>
                            <td>${w.transactions}</td>
                        `;
                        weeklyTbody.appendChild(row);
                    });
                    
                    // أفضل وأسوأ الشهور
                    document.getElementById('bestMonth').textContent = data.best_month || '-';
                    document.getElementById('worstMonth').textContent = data.worst_month || '-';
                })
                .catch(error => {
                    document.getElementById('loading').innerHTML = '❌ خطأ: ' + error.message;
                });
        </script>
    </body>
    </html>

   """
# ====================
# صفحة لوحة التحكم المتقدمة
# ====================
@app.route('/dashboard')
def dashboard_page():
    """لوحة تحكم متقدمة"""
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>لوحة التحكم المتقدمة</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Arial; 
                background: #f0f2f5; 
                padding: 15px;
            }
            .container { 
                max-width: 1600px; 
                margin: auto; 
                background: white; 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                border-bottom: 4px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 25px;
            }
            .header h1 {
                color: #2c3e50;
                font-size: 28px;
            }
            .header .date-time {
                color: #7f8c8d;
                font-size: 14px;
            }
            .nav-links {
                display: flex;
                gap: 10px;
                margin: 10px 0 20px;
                flex-wrap: wrap;
            }
            .nav-links a {
                padding: 8px 16px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 14px;
                transition: all 0.3s;
            }
            .nav-links a:hover { opacity: 0.8; transform: translateY(-2px); }
            .btn-primary { background: #3498db; color: white; }
            .btn-success { background: #27ae60; color: white; }
            .btn-warning { background: #e67e22; color: white; }
            .btn-info { background: #1abc9c; color: white; }
            .btn-danger { background: #e74c3c; color: white; }
            .btn-purple { background: #8e44ad; color: white; }
            .btn-dashboard { background: #2c3e50; color: white; }
            
            /* بطاقات الإحصائيات */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 12px;
                color: white;
                transition: transform 0.3s;
            }
            .stat-card:hover { transform: translateY(-5px); }
            .stat-card:nth-child(2) { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .stat-card:nth-child(3) { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            .stat-card:nth-child(4) { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
            .stat-card:nth-child(5) { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
            .stat-card:nth-child(6) { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); }
            .stat-card .stat-value {
                font-size: 32px;
                font-weight: bold;
            }
            .stat-card .stat-label {
                font-size: 14px;
                opacity: 0.9;
                margin-top: 5px;
            }
            .stat-card .stat-change {
                font-size: 12px;
                margin-top: 8px;
                display: inline-block;
                padding: 2px 10px;
                border-radius: 20px;
                background: rgba(255,255,255,0.2);
            }
            
            /* شبكة الرسوم البيانية */
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin: 20px 0;
            }
            .chart-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
            }
            .chart-card h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 16px;
            }
            .chart-card canvas {
                max-height: 250px;
                width: 100% !important;
            }
            
            /* جدول البيانات */
            .table-container {
                overflow-x: auto;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }
            th, td {
                padding: 10px 12px;
                text-align: right;
                border-bottom: 1px solid #eee;
            }
            th {
                background: #2c3e50;
                color: white;
                font-weight: 600;
            }
            tr:hover { background: #f5f5f5; }
            .badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: bold;
            }
            .badge-vip { background: #ffd700; color: #333; }
            .badge-loyal { background: #4CAF50; color: white; }
            .badge-potential { background: #2196F3; color: white; }
            .badge-at_risk { background: #ff9800; color: white; }
            .badge-lost { background: #f44336; color: white; }
            .badge-other { background: #9e9e9e; color: white; }
            
            /* شريط التقدم */
            .progress-bar-container {
                margin: 5px 0;
            }
            .progress-bar {
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
            }
            .progress-bar .fill {
                height: 100%;
                border-radius: 4px;
                transition: width 1s;
            }
            
            /* تذييل */
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 12px;
            }
            
            /* استجابة للجوال */
            @media (max-width: 768px) {
                .charts-grid { grid-template-columns: 1fr; }
                .header { flex-direction: column; align-items: flex-start; gap: 10px; }
                .stats-grid { grid-template-columns: repeat(2, 1fr); }
            }
            @media (max-width: 480px) {
                .stats-grid { grid-template-columns: 1fr; }
                .nav-links a { font-size: 12px; padding: 6px 12px; }
            }
            
            /* زر التحديث */
            .refresh-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                transition: opacity 0.3s;
            }
            .refresh-btn:hover { opacity: 0.8; }
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255,255,255,0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                font-size: 24px;
                color: #3498db;
            }
            .loading-overlay.hidden { display: none; }
        </style>
    </head>
    <body>
        <!-- طبقة التحميل -->
        <div id="loadingOverlay" class="loading-overlay">
            <div>⏳ جاري تحميل البيانات...</div>
        </div>
        
        <div class="container">
            <!-- الرأس -->
            <div class="header">
                <div>
                    <h1>📊 لوحة التحكم المتقدمة</h1>
                    <div style="font-size:14px;color:#7f8c8d;margin-top:5px;">
                        نظام تحليل المبيعات والعملاء
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:15px;flex-wrap:wrap;">
                    <span class="date-time" id="currentTime"></span>
                    <button class="refresh-btn" onclick="refreshData()">🔄 تحديث</button>
                </div>
            </div>
            
            <!-- روابط التنقل -->
            <div class="nav-links">
                <a href="/" class="btn-primary">🏠 الرئيسية</a>
                <a href="/dashboard" class="btn-dashboard">📊 لوحة التحكم</a>
                <a href="/customers" class="btn-success">👥 تحليل العملاء</a>
                <a href="/forecast" class="btn-warning">🔮 التنبؤ</a>
                <a href="/seasonality" class="btn-info">🌦️ التحليل الموسمي</a>
                <a href="/reports" class="btn-purple">📄 التقارير</a>
            </div>
            
            <!-- إحصائيات سريعة -->
            <div class="stats-grid" id="quickStats">
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">💰 إجمالي الإيرادات</div></div>
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">👥 إجمالي العملاء</div></div>
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">📦 عدد المعاملات</div></div>
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">🛒 متوسط السلة</div></div>
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">🔄 معدل الاحتفاظ</div></div>
                <div class="stat-card"><div class="stat-value">-</div><div class="stat-label">🏆 عدد العملاء المميزين</div></div>
            </div>
            
            <!-- الرسوم البيانية -->
            <div class="charts-grid">
                <div class="chart-card">
                    <h3>📈 اتجاه المبيعات (آخر 30 يوم)</h3>
                    <canvas id="salesTrendChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3>👥 توزيع شرائح العملاء</h3>
                    <canvas id="segmentChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3>💰 توزيع الإيرادات حسب الشهر</h3>
                    <canvas id="monthlyRevenueChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3>📊 توزيع درجات RFM</h3>
                    <canvas id="rfmDistributionChart"></canvas>
                </div>
            </div>
            
            <!-- أفضل العملاء -->
            <div class="table-container">
                <h3 style="color:#2c3e50;margin-bottom:15px;">🏆 أفضل العملاء من حيث القيمة</h3>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>معرف العميل</th>
                            <th>القيمة الإجمالية</th>
                            <th>عدد المعاملات</th>
                            <th>درجة RFM</th>
                            <th>الشريحة</th>
                            <th>آخر معاملة</th>
                        </tr>
                    </thead>
                    <tbody id="topCustomersTable"></tbody>
                </table>
            </div>
            
            <!-- تذييل -->
            <div class="footer">
                نظام تحليل المبيعات والعملاء | تم التحديث: <span id="updateTime"></span>
            </div>
        </div>
        
        <script>
            // ====================
            // دوال مساعدة
            // ====================
            
            // تحديث الوقت
            function updateTime() {
                const now = new Date();
                document.getElementById('currentTime').textContent = now.toLocaleString('ar-SA');
                document.getElementById('updateTime').textContent = now.toLocaleString('ar-SA');
            }
            updateTime();
            setInterval(updateTime, 60000);
            
            // إظهار/إخفاء التحميل
            function showLoading(show) {
                document.getElementById('loadingOverlay').classList.toggle('hidden', !show);
            }
            
            // ====================
            // تحميل البيانات
            // ====================
            
            function refreshData() {
                showLoading(true);
                Promise.all([
                    fetch('/api/dashboard_stats').then(r => r.json()),
                    fetch('/api/sales_trend').then(r => r.json()),
                    fetch('/api/rfm').then(r => r.json()),
                    fetch('/api/seasonality').then(r => r.json())
                ])
                .then(([stats, trend, rfm, seasonality]) => {
                    updateStats(stats);
                    updateCharts(trend, rfm, seasonality);
                    updateTopCustomers(rfm);
                    showLoading(false);
                })
                .catch(error => {
                    console.error('خطأ:', error);
                    showLoading(false);
                    alert('❌ خطأ في تحميل البيانات: ' + error.message);
                });
            }
            
            // ====================
            // تحديث الإحصائيات
            // ====================
            
            function updateStats(data) {
                const stats = [
                    {selector: 0, value: '$' + (data.total_revenue || 0).toFixed(2), label: '💰 إجمالي الإيرادات'},
                    {selector: 1, value: data.unique_customers || 0, label: '👥 إجمالي العملاء'},
                    {selector: 2, value: data.total_transactions || 0, label: '📦 عدد المعاملات'},
                    {selector: 3, value: '$' + (data.average_basket || 0).toFixed(2), label: '🛒 متوسط السلة'},
                    {selector: 4, value: ((data.retention_rate || 0) * 100).toFixed(1) + '%', label: '🔄 معدل الاحتفاظ'},
                    {selector: 5, value: data.vip_customers || 0, label: '🏆 عدد العملاء المميزين'}
                ];
                
                const cards = document.querySelectorAll('.stat-card');
                stats.forEach((s, i) => {
                    if (cards[i]) {
                        cards[i].innerHTML = `
                            <div class="stat-value">${s.value}</div>
                            <div class="stat-label">${s.label}</div>
                        `;
                    }
                });
            }
            
            // ====================
            // تحديث الرسوم البيانية
            // ====================
            
            let charts = {};
            
            function updateCharts(trend, rfm, seasonality) {
                // 1. اتجاه المبيعات
                if (trend.data && trend.data.length > 0) {
                    const dates = trend.data.map(d => d.date);
                    const values = trend.data.map(d => d.sales);
                    
                    if (charts.salesTrend) charts.salesTrend.destroy();
                    
                    const ctx = document.getElementById('salesTrendChart').getContext('2d');
                    charts.salesTrend = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: dates,
                            datasets: [{
                                label: 'المبيعات اليومية',
                                data: values,
                                borderColor: '#3498db',
                                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true, ticks: { callback: v => '$' + v.toFixed(0) } }
                            }
                        }
                    });
                }
                
                // 2. توزيع الشرائح
                if (rfm.segment_stats) {
                    const segments = Object.keys(rfm.segment_stats);
                    const counts = Object.values(rfm.segment_stats);
                    const colors = {
                        vip: '#ffd700',
                        loyal: '#4CAF50',
                        potential: '#2196F3',
                        at_risk: '#ff9800',
                        lost: '#f44336',
                        other: '#9e9e9e'
                    };
                    
                    if (charts.segment) charts.segment.destroy();
                    
                    const ctx2 = document.getElementById('segmentChart').getContext('2d');
                    charts.segment = new Chart(ctx2, {
                        type: 'doughnut',
                        data: {
                            labels: segments,
                            datasets: [{
                                data: counts,
                                backgroundColor: segments.map(s => colors[s] || '#9e9e9e')
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: { position: 'bottom' }
                            }
                        }
                    });
                }
                
                // 3. الإيرادات الشهرية
                if (seasonality.monthly) {
                    const months = seasonality.monthly.map(m => m.month_name);
                    const revenues = seasonality.monthly.map(m => m.total_sales);
                    
                    if (charts.monthlyRevenue) charts.monthlyRevenue.destroy();
                    
                    const ctx3 = document.getElementById('monthlyRevenueChart').getContext('2d');
                    charts.monthlyRevenue = new Chart(ctx3, {
                        type: 'bar',
                        data: {
                            labels: months,
                            datasets: [{
                                label: 'الإيرادات',
                                data: revenues,
                                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                                borderColor: '#3498db',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true, ticks: { callback: v => '$' + v.toFixed(0) } }
                            }
                        }
                    });
                }
                
                // 4. توزيع درجات RFM
                if (rfm.score_distribution) {
                    const rScores = rfm.score_distribution.r_scores || {};
                    const fScores = rfm.score_distribution.f_scores || {};
                    const mScores = rfm.score_distribution.m_scores || {};
                    
                    const scores = [1, 2, 3, 4, 5];
                    const rData = scores.map(s => rScores[s] || 0);
                    const fData = scores.map(s => fScores[s] || 0);
                    const mData = scores.map(s => mScores[s] || 0);
                    
                    if (charts.rfmDist) charts.rfmDist.destroy();
                    
                    const ctx4 = document.getElementById('rfmDistributionChart').getContext('2d');
                    charts.rfmDist = new Chart(ctx4, {
                        type: 'bar',
                        data: {
                            labels: ['1', '2', '3', '4', '5'],
                            datasets: [
                                { label: 'الحداثة (R)', data: rData, backgroundColor: '#e74c3c' },
                                { label: 'التكرار (F)', data: fData, backgroundColor: '#3498db' },
                                { label: 'القيمة (M)', data: mData, backgroundColor: '#2ecc71' }
                            ]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: { position: 'top' }
                            },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            }
            
            // ====================
            // تحديث جدول أفضل العملاء
            // ====================
            
            function updateTopCustomers(rfm) {
                const tbody = document.getElementById('topCustomersTable');
                tbody.innerHTML = '';
                
                if (!rfm.top_customers || rfm.top_customers.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;">لا توجد بيانات</td></tr>';
                    return;
                }
                
                const badges = {
                    vip: 'badge-vip',
                    loyal: 'badge-loyal',
                    potential: 'badge-potential',
                    at_risk: 'badge-at_risk',
                    lost: 'badge-lost',
                    other: 'badge-other'
                };
                
                rfm.top_customers.slice(0, 10).forEach((c, i) => {
                    const row = document.createElement('tr');
                    const badgeClass = badges[c.segment] || 'badge-other';
                    row.innerHTML = `
                        <td>${i + 1}</td>
                        <td><strong>${c.customer_id}</strong></td>
                        <td>$${c.monetary.toFixed(2)}</td>
                        <td>${c.frequency || '-'}</td>
                        <td>${c.rfm_score.toFixed(1)}</td>
                        <td><span class="badge ${badgeClass}">${c.segment}</span></td>
                        <td>${c.last_purchase || '-'}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // ====================
            // تشغيل التطبيق
            // ====================
            
            // تحميل البيانات عند تحميل الصفحة
            document.addEventListener('DOMContentLoaded', function() {
                refreshData();
            });
            
            // تحديث كل 5 دقائق
            setInterval(refreshData, 300000);
            
            // جعل الدالة متاحة عالمياً
            window.refreshData = refreshData;
        </script>
    </body>
    </html>

   """
# ====================
# API: إحصائيات لوحة التحكم
# ====================
@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    """API لإحصائيات لوحة التحكم"""
    try:
        kpi_analyzer = KPIAnalyzer()
        
        transaction_id = config['analysis'].get('transaction_id', 'transaction_id')
        if transaction_id not in df.columns:
            transaction_id = df.columns[0]
        
        kpis = kpi_analyzer.calculate_all_kpis(
            df,
            customer_id,
            transaction_id,
            date_col,
            amount_col
        )
        
        # حساب العملاء المميزين (VIP)
        rfm_analyzer = RFMAnalyzer()
        rfm_results = rfm_analyzer.analyze_rfm(
            df,
            customer_id,
            date_col,
            amount_col,
            config['analysis']['rfm']['segments']
        )
        
        rfm_df = rfm_results['rfm_scores']
        vip_count = len(rfm_df[rfm_df['segment'] == 'vip'])
        
        return jsonify({
            'total_revenue': kpis['total_revenue'],
            'unique_customers': kpis['unique_customers'],
            'total_transactions': kpis['total_transactions'],
            'average_basket': kpis['average_basket'],
            'retention_rate': kpis['retention_rate'],
            'vip_customers': vip_count,
            'avg_customer_value': kpis['avg_customer_value']
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ====================
# تشغيل التطبيق
# ====================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 تشغيل تطبيق تحليل المبيعات والعملاء")
    print("=" * 60)
    print(f"📊 عدد السجلات: {len(df)}")
    print(f"👥 عدد العملاء: {df[customer_id].nunique()}")
    print(f"💰 إجمالي الإيرادات: ${df[amount_col].sum():,.2f}")
    print("=" * 60)
    print("🌐 افتح المتصفح على: http://localhost:5000")
    print("📊 الصفحات المتاحة:")
    print("   - http://localhost:5000/          (الرئيسية)")
    print("   - http://localhost:5000/customers (تحليل العملاء RFM)")
    print("   - http://localhost:5000/forecast  (التنبؤ بالمبيعات)")
    print("   - http://localhost:5000/seasonality (التحليل الموسمي)")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)