# src/pipeline.py

"""
Data Analysis Pipeline Module

This module orchestrates the end-to-end data analysis pipeline including:
- Data loading and validation
- Data cleaning with date conversion, deduplication, and amount calculation
- KPI calculations
- RFM analysis
- Visualization and export

Author: agricolecooperative16-lgtm
Date: 2026-09-08
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
import json
import yaml

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader
from src.data_cleaning import DataCleaner
from src.data_validation import DataValidator
from src.rfm_analysis import RFMAnalyzer
from src.kpi_calculator import KPICalculator
from src.visualization import Visualizer
from src.forecasting import SalesForecaster
from src.seasonal_analysis import SeasonalAnalyzer
from src.clv_analyzer import CLVAnalyzer
from src.retention_analyzer import RetentionAnalyzer


class AnalysisPipeline:
    """
    Orchestrates the complete data analysis pipeline from loading to export.
    """
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_loader = DataLoader()
        self.data_cleaner = None
        self.data_validator = DataValidator()
        self.rfm_analyzer = RFMAnalyzer()
        self.kpi_calculator = KPICalculator()
        self.visualizer = Visualizer()
        self.forecaster = SalesForecaster()
        self.seasonal_analyzer = SeasonalAnalyzer()
        self.clv_analyzer = CLVAnalyzer()
        self.retention_analyzer = RetentionAnalyzer()
        
        # State variables
        self.raw_data = None
        self.cleaned_data = None
        self.pipeline_results = {}
        
        self.logger.info("AnalysisPipeline initialized successfully")
        self.logger.info(f"Configuration loaded from: {config_path}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            self.logger.error(f"Could not load config file: {str(e)}")
            raise
    
    def setup_logging(self):
        """Configure logging for the pipeline."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        log_file = log_config.get('file', 'logs/app.log')
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=log_date_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def load_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load data from specified path or from config.
        
        Args:
            file_path: Path to data file (optional)
            
        Returns:
            Loaded DataFrame
        """
        try:
            if file_path is None:
                # Use the sales file from config
                sales_file = self.config['data'].get('sales_file', 'sales_data.csv')
                raw_path = self.config['data'].get('raw_path', 'data/raw/')
                file_path = os.path.join(raw_path, sales_file)
            
            self.logger.info(f"Loading data from: {file_path}")
            self.raw_data = self.data_loader.load_data(file_path)
            self.logger.info(f"Data loaded successfully. Shape: {self.raw_data.shape}")
            
            return self.raw_data
        except Exception as e:
            self.logger.error(f"Failed to load data: {str(e)}")
            raise
    
    def clean_data(self) -> pd.DataFrame:
        """
        Execute the data cleaning pipeline with specific steps:
        1. Convert dates to datetime
        2. Remove duplicates
        3. Calculate total amount
        
        Returns:
            Cleaned DataFrame
        """
        try:
            self.logger.info("Starting data cleaning pipeline...")
            
            if self.raw_data is None:
                raise ValueError("No data loaded. Call load_data() first.")
            
            # Initialize cleaner with raw data
            self.data_cleaner = DataCleaner(self.raw_data)
            
            # Execute cleaning steps with proper configuration
            cleaned_df = self._execute_cleaning_steps()
            
            self.cleaned_data = cleaned_df
            self.logger.info(f"Data cleaning completed. Shape: {self.cleaned_data.shape}")
            
            return self.cleaned_data
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {str(e)}")
            raise
    
    def _execute_cleaning_steps(self) -> pd.DataFrame:
        """Execute individual cleaning steps with error handling."""
        df = self.raw_data.copy()
        
        # Step 1: Convert dates
        df = self._convert_dates(df)
        
        # Step 2: Remove duplicates
        df = self._remove_duplicates(df)
        
        # Step 3: Calculate total amount
        df = self._calculate_total_amount(df)
        
        # Additional cleaning from existing DataCleaner
        if hasattr(self.data_cleaner, 'handle_missing_values'):
            df = self.data_cleaner.handle_missing_values(df)
        
        if hasattr(self.data_cleaner, 'clean_categorical'):
            df = self.data_cleaner.clean_categorical(df)
        
        if hasattr(self.data_cleaner, 'handle_outliers'):
            df = self.data_cleaner.handle_outliers(df)
        
        return df
    
    def _convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert date columns to datetime."""
        # Get date column from config
        date_col = self.config.get('analysis', {}).get('date_column', 'transaction_date')
        
        if date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                null_count = df[date_col].isnull().sum()
                self.logger.info(f"Converted '{date_col}' to datetime. Null count: {null_count}")
                
                # Log date range
                if null_count < len(df):
                    min_date = df[date_col].min()
                    max_date = df[date_col].max()
                    self.logger.info(f"Date range: {min_date} to {max_date}")
            except Exception as e:
                self.logger.warning(f"Could not convert '{date_col}' to datetime: {str(e)}")
        else:
            self.logger.warning(f"Date column '{date_col}' not found in data")
            
            # Try to find any column with 'date' in name as fallback
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                self.logger.info(f"Found potential date columns: {date_cols}")
                for col in date_cols:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        self.logger.info(f"Converted fallback column '{col}' to datetime")
                    except:
                        pass
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records."""
        # Get customer ID column from config
        customer_id_col = self.config.get('analysis', {}).get('customer_id', 'customer_id')
        
        # Check if we have a combination of columns that can identify unique transactions
        date_col = self.config.get('analysis', {}).get('date_column', 'transaction_date')
        product_col = self.config.get('analysis', {}).get('product_id', 'product_id')
        
        initial_shape = df.shape
        
        # Try to remove duplicates based on composite key if possible
        if customer_id_col in df.columns and date_col in df.columns and product_col in df.columns:
            subset_cols = [customer_id_col, date_col, product_col]
            df = df.drop_duplicates(subset=subset_cols, keep='first')
            self.logger.info(f"Removed duplicates based on '{subset_cols}'. Shape: {initial_shape} -> {df.shape}")
        elif customer_id_col in df.columns and date_col in df.columns:
            subset_cols = [customer_id_col, date_col]
            df = df.drop_duplicates(subset=subset_cols, keep='first')
            self.logger.info(f"Removed duplicates based on '{subset_cols}'. Shape: {initial_shape} -> {df.shape}")
        else:
            df = df.drop_duplicates()
            self.logger.warning(f"Removed duplicates based on all columns (no key columns found)")
        
        return df
    
    def _calculate_total_amount(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate total amount from quantity and unit price."""
        qty_col = self.config.get('analysis', {}).get('quantity_column', 'quantity')
        price_col = self.config.get('analysis', {}).get('price_column', 'unit_price')
        amount_col = self.config.get('analysis', {}).get('amount_column', 'total_amount')
        
        if qty_col in df.columns and price_col in df.columns:
            try:
                # Ensure numeric types
                df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce')
                df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
                
                # Calculate total amount
                df[amount_col] = df[qty_col] * df[price_col]
                df[amount_col] = df[amount_col].round(2)
                
                # Log statistics
                self.logger.info(f"Calculated '{amount_col}' column. Statistics:")
                self.logger.info(f"  - Sum: {df[amount_col].sum():,.2f}")
                self.logger.info(f"  - Mean: {df[amount_col].mean():,.2f}")
                self.logger.info(f"  - Median: {df[amount_col].median():,.2f}")
                self.logger.info(f"  - Missing values: {df[amount_col].isnull().sum()}")
            except Exception as e:
                self.logger.error(f"Error calculating total amount: {str(e)}")
        else:
            self.logger.warning(f"Required columns for amount calculation not found: {qty_col}, {price_col}")
        
        return df
    
    def validate_data(self) -> Dict[str, Any]:
        """
        Perform data quality validation.
        
        Returns:
            Dictionary with validation results
        """
        try:
            self.logger.info("Starting data validation...")
            
            if self.cleaned_data is None:
                raise ValueError("No cleaned data available. Run clean_data() first.")
            
            validation_results = self.data_validator.validate(self.cleaned_data)
            
            self.pipeline_results['validation'] = validation_results
            self.logger.info(f"Data validation completed. Issues found: {len(validation_results.get('issues', []))}")
            
            return validation_results
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            raise
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """
        Calculate key performance indicators.
        
        Returns:
            Dictionary with KPI results
        """
        try:
            self.logger.info("Calculating KPIs...")
            
            if self.cleaned_data is None:
                raise ValueError("No cleaned data available. Run clean_data() first.")
            
            kpi_results = self.kpi_calculator.calculate_all_kpis(self.cleaned_data)
            
            self.pipeline_results['kpis'] = kpi_results
            self.logger.info(f"KPI calculation completed. Found {len(kpi_results)} KPIs.")
            
            return kpi_results
        except Exception as e:
            self.logger.error(f"KPI calculation failed: {str(e)}")
            raise
    
    def perform_rfm_analysis(self) -> Dict[str, Any]:
        """
        Perform RFM (Recency, Frequency, Monetary) analysis.
        
        Returns:
            Dictionary with RFM results
        """
        try:
            self.logger.info("Starting RFM analysis...")
            
            if self.cleaned_data is None:
                raise ValueError("No cleaned data available. Run clean_data() first.")
            
            # Get RFM configuration
            rfm_config = self.config.get('analysis', {}).get('rfm', {})
            
            # Get column names
            customer_col = self.config.get('analysis', {}).get('customer_id', 'customer_id')
            date_col = self.config.get('analysis', {}).get('date_column', 'transaction_date')
            amount_col = self.config.get('analysis', {}).get('amount_column', 'total_amount')
            
            # Prepare RFM data
            rfm_data = self.cleaned_data[[customer_col, date_col, amount_col]].copy()
            
            # Perform RFM analysis
            rfm_results = self.rfm_analyzer.analyze(
                rfm_data,
                customer_col=customer_col,
                date_col=date_col,
                amount_col=amount_col,
                config=rfm_config
            )
            
            self.pipeline_results['rfm'] = rfm_results
            self.logger.info("RFM analysis completed successfully.")
            
            # Log segment distribution
            if 'segments' in rfm_results:
                self.logger.info("RFM Segment Distribution:")
                for segment, count in rfm_results['segments'].items():
                    self.logger.info(f"  {segment}: {count} customers")
            
            return rfm_results
        except Exception as e:
            self.logger.error(f"RFM analysis failed: {str(e)}")
            raise
    
    def perform_advanced_analytics(self) -> Dict[str, Any]:
        """
        Perform advanced analytics including:
        - Sales forecasting
        - Seasonal analysis
        - CLV calculation
        - Retention analysis
        
        Returns:
            Dictionary with advanced analytics results
        """
        try:
            self.logger.info("Starting advanced analytics...")
            
            if self.cleaned_data is None:
                raise ValueError("No cleaned data available. Run clean_data() first.")
            
            advanced_results = {}
            
            # Sales Forecasting
            try:
                forecast_config = self.config.get('models', {}).get('forecasting', {})
                models = forecast_config.get('models', ['linear_regression', 'arima', 'prophet'])
                
                advanced_results['forecast'] = self.forecaster.forecast(
                    self.cleaned_data,
                    test_size=forecast_config.get('test_size', 0.2),
                    seasonality_period=forecast_config.get('seasonality_period', 12),
                    models=models
                )
                self.logger.info(f"Sales forecasting completed using models: {models}")
            except Exception as e:
                self.logger.warning(f"Sales forecasting failed: {str(e)}")
            
            # Seasonal Analysis
            try:
                seasonal_config = self.config.get('models', {}).get('forecasting', {})
                advanced_results['seasonal'] = self.seasonal_analyzer.analyze(
                    self.cleaned_data,
                    seasonality_period=seasonal_config.get('seasonality_period', 12)
                )
                self.logger.info("Seasonal analysis completed.")
            except Exception as e:
                self.logger.warning(f"Seasonal analysis failed: {str(e)}")
            
            # CLV Analysis
            try:
                advanced_results['clv'] = self.clv_analyzer.calculate(
                    self.cleaned_data,
                    customer_id_col=self.config.get('analysis', {}).get('customer_id', 'customer_id'),
                    date_col=self.config.get('analysis', {}).get('date_column', 'transaction_date'),
                    amount_col=self.config.get('analysis', {}).get('amount_column', 'total_amount')
                )
                self.logger.info("CLV analysis completed.")
            except Exception as e:
                self.logger.warning(f"CLV analysis failed: {str(e)}")
            
            # Retention Analysis
            try:
                advanced_results['retention'] = self.retention_analyzer.analyze(
                    self.cleaned_data,
                    customer_id_col=self.config.get('analysis', {}).get('customer_id', 'customer_id'),
                    date_col=self.config.get('analysis', {}).get('date_column', 'transaction_date')
                )
                self.logger.info("Retention analysis completed.")
            except Exception as e:
                self.logger.warning(f"Retention analysis failed: {str(e)}")
            
            self.pipeline_results['advanced'] = advanced_results
            return advanced_results
        except Exception as e:
            self.logger.error(f"Advanced analytics failed: {str(e)}")
            raise
    
    def generate_visualizations(self) -> Dict[str, str]:
        """
        Generate all visualizations.
        
        Returns:
            Dictionary mapping visualization names to file paths
        """
        try:
            self.logger.info("Generating visualizations...")
            
            if self.cleaned_data is None:
                raise ValueError("No cleaned data available. Run clean_data() first.")
            
            viz_outputs = {}
            
            # Get visualization configuration
            viz_config = self.config.get('visualization', {})
            save_figures = viz_config.get('save_figures', True)
            
            if not save_figures:
                self.logger.info("Visualization saving is disabled in config.")
                return viz_outputs
            
            # Create visualizations directory
            viz_dir = 'reports/visualizations'
            os.makedirs(viz_dir, exist_ok=True)
            
            # Get figure settings
            fig_size = viz_config.get('figure_size', [12, 8])
            color_palette = viz_config.get('color_palette', 'Set2')
            dpi = viz_config.get('dpi', 100)
            fig_format = viz_config.get('figure_format', 'png')
            
            # Generate plots for KPIs
            if 'kpis' in self.pipeline_results:
                viz_outputs['kpi_dashboard'] = self.visualizer.create_kpi_dashboard(
                    self.cleaned_data,
                    self.pipeline_results['kpis'],
                    save_path=f'{viz_dir}/kpi_dashboard.{fig_format}',
                    fig_size=fig_size,
                    color_palette=color_palette,
                    dpi=dpi
                )
            
            # Generate RFM visualizations
            if 'rfm' in self.pipeline_results:
                viz_outputs['rfm_segmentation'] = self.visualizer.plot_rfm_segments(
                    self.pipeline_results['rfm'],
                    save_path=f'{viz_dir}/rfm_segments.{fig_format}',
                    fig_size=fig_size,
                    color_palette=color_palette,
                    dpi=dpi
                )
            
            # Generate time series plots
            date_col = self.config.get('analysis', {}).get('date_column', 'transaction_date')
            amount_col = self.config.get('analysis', {}).get('amount_column', 'total_amount')
            
            viz_outputs['sales_trend'] = self.visualizer.plot_sales_trend(
                self.cleaned_data,
                date_col=date_col,
                amount_col=amount_col,
                save_path=f'{viz_dir}/sales_trend.{fig_format}',
                fig_size=fig_size,
                color_palette=color_palette,
                dpi=dpi
            )
            
            # Generate distribution plots
            viz_outputs['customer_distribution'] = self.visualizer.plot_customer_distribution(
                self.cleaned_data,
                save_path=f'{viz_dir}/customer_distribution.{fig_format}',
                fig_size=fig_size,
                color_palette=color_palette,
                dpi=dpi
            )
            
            # Generate advanced plots if available
            if 'advanced' in self.pipeline_results:
                if 'forecast' in self.pipeline_results['advanced']:
                    viz_outputs['forecast'] = self.visualizer.plot_forecast(
                        self.pipeline_results['advanced']['forecast'],
                        save_path=f'{viz_dir}/forecast.{fig_format}',
                        fig_size=fig_size,
                        color_palette=color_palette,
                        dpi=dpi
                    )
                
                if 'seasonal' in self.pipeline_results['advanced']:
                    viz_outputs['seasonal'] = self.visualizer.plot_seasonal_patterns(
                        self.pipeline_results['advanced']['seasonal'],
                        save_path=f'{viz_dir}/seasonal.{fig_format}',
                        fig_size=fig_size,
                        color_palette=color_palette,
                        dpi=dpi
                    )
            
            self.pipeline_results['visualizations'] = viz_outputs
            self.logger.info(f"Visualizations generated: {len(viz_outputs)}")
            
            return viz_outputs
        except Exception as e:
            self.logger.error(f"Visualization generation failed: {str(e)}")
            raise
    
    def export_results(self, export_path: Optional[str] = None) -> Dict[str, str]:
        """
        Export all pipeline results.
        
        Args:
            export_path: Base path for exports
            
        Returns:
            Dictionary with export file paths
        """
        try:
            # Use config paths if not specified
            if export_path is None:
                export_path = self.config['data'].get('processed_path', 'data/processed/')
            
            self.logger.info(f"Exporting results to: {export_path}")
            
            # Create necessary directories
            os.makedirs(export_path, exist_ok=True)
            reports_path = 'reports'
            os.makedirs(reports_path, exist_ok=True)
            os.makedirs(f'{reports_path}/json', exist_ok=True)
            
            exports = {}
            
            # Export cleaned data
            if self.cleaned_data is not None:
                # Create processed data filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f'cleaned_data_{timestamp}.csv'
                csv_path = os.path.join(export_path, csv_filename)
                self.cleaned_data.to_csv(csv_path, index=False)
                exports['cleaned_data'] = csv_path
                self.logger.info(f"Exported cleaned data to: {csv_path}")
            
            # Export results as JSON
            json_path = f'{reports_path}/json/pipeline_results_{timestamp}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                # Convert any non-serializable objects to strings
                json.dump(self.pipeline_results, f, indent=2, default=str)
            exports['results_json'] = json_path
            self.logger.info(f"Exported results to: {json_path}")
            
            # Generate summary report
            summary_path = f'{reports_path}/summary_report_{timestamp}.txt'
            self._generate_summary_report(summary_path)
            exports['summary_report'] = summary_path
            self.logger.info(f"Generated summary report: {summary_path}")
            
            return exports
        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            raise
    
    def _generate_summary_report(self, file_path: str):
        """Generate a comprehensive summary report."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DATA ANALYSIS PIPELINE - SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Data Summary
            if self.cleaned_data is not None:
                f.write("DATA SUMMARY\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Records: {len(self.cleaned_data):,}\n")
                f.write(f"Total Features: {len(self.cleaned_data.columns)}\n")
                f.write(f"Columns: {', '.join(self.cleaned_data.columns)}\n\n")
                
                # Check for required columns
                date_col = self.config.get('analysis', {}).get('date_column', 'transaction_date')
                customer_col = self.config.get('analysis', {}).get('customer_id', 'customer_id')
                amount_col = self.config.get('analysis', {}).get('amount_column', 'total_amount')
                
                if date_col in self.cleaned_data.columns:
                    f.write(f"Date Range: {self.cleaned_data[date_col].min()} to {self.cleaned_data[date_col].max()}\n")
                
                if customer_col in self.cleaned_data.columns:
                    f.write(f"Unique Customers: {self.cleaned_data[customer_col].nunique():,}\n")
                
                if amount_col in self.cleaned_data.columns:
                    f.write(f"Total Sales: ${self.cleaned_data[amount_col].sum():,.2f}\n")
                    f.write(f"Average Transaction: ${self.cleaned_data[amount_col].mean():,.2f}\n")
                f.write("\n")
            
            # KPI Summary
            if 'kpis' in self.pipeline_results:
                f.write("KPI SUMMARY\n")
                f.write("-" * 40 + "\n")
                for kpi, value in self.pipeline_results['kpis'].items():
                    if isinstance(value, (int, float)):
                        if 'percent' in kpi.lower() or 'rate' in kpi.lower():
                            f.write(f"{kpi}: {value:.2f}%\n")
                        elif 'amount' in kpi.lower() or 'revenue' in kpi.lower() or 'sales' in kpi.lower():
                            f.write(f"{kpi}: ${value:,.2f}\n")
                        else:
                            f.write(f"{kpi}: {value:,.2f}\n")
                    else:
                        f.write(f"{kpi}: {value}\n")
                f.write("\n")
            
            # RFM Summary
            if 'rfm' in self.pipeline_results:
                rfm = self.pipeline_results['rfm']
                f.write("RFM ANALYSIS SUMMARY\n")
                f.write("-" * 40 + "\n")
                
                if 'segments' in rfm:
                    f.write("Customer Segments Distribution:\n")
                    total_customers = sum(rfm['segments'].values()) if rfm['segments'] else 0
                    for segment, count in rfm['segments'].items():
                        percentage = (count / total_customers * 100) if total_customers > 0 else 0
                        f.write(f"  {segment.capitalize()}: {count:,} customers ({percentage:.1f}%)\n")
                    
                    # Get segment definitions from config
                    segments_config = self.config.get('analysis', {}).get('rfm', {}).get('segments', {})
                    if segments_config:
                        f.write("\nSegment Definitions:\n")
                        for segment, scores in segments_config.items():
                            f.write(f"  {segment.capitalize()}: RFM Score {scores[0]}-{scores[1]}\n")
                f.write("\n")
            
            # Advanced Analytics Summary
            if 'advanced' in self.pipeline_results:
                f.write("ADVANCED ANALYTICS SUMMARY\n")
                f.write("-" * 40 + "\n")
                
                if 'forecast' in self.pipeline_results['advanced']:
                    forecast_data = self.pipeline_results['advanced']['forecast']
                    f.write(f"Sales Forecasting: Using {len(forecast_data.get('models', []))} models\n")
                    if 'best_model' in forecast_data:
                        f.write(f"  Best Model: {forecast_data['best_model']}\n")
                        f.write(f"  Model Performance (RMSE): {forecast_data.get('best_score', 'N/A')}\n")
                
                if 'clv' in self.pipeline_results['advanced']:
                    clv_data = self.pipeline_results['advanced']['clv']
                    if isinstance(clv_data, dict):
                        if 'average_clv' in clv_data:
                            f.write(f"\nCustomer Lifetime Value (CLV):\n")
                            f.write(f"  Average CLV: ${clv_data['average_clv']:,.2f}\n")
                            if 'median_clv' in clv_data:
                                f.write(f"  Median CLV: ${clv_data['median_clv']:,.2f}\n")
                            if 'total_clv' in clv_data:
                                f.write(f"  Total CLV: ${clv_data['total_clv']:,.2f}\n")
                
                if 'retention' in self.pipeline_results['advanced']:
                    retention_data = self.pipeline_results['advanced']['retention']
                    if isinstance(retention_data, dict) and 'retention_rate' in retention_data:
                        f.write(f"\nCustomer Retention:\n")
                        f.write(f"  Retention Rate: {retention_data['retention_rate']:.2f}%\n")
                        if 'churn_rate' in retention_data:
                            f.write(f"  Churn Rate: {retention_data['churn_rate']:.2f}%\n")
                        if 'retention_periods' in retention_data:
                            f.write(f"  Retention Periods: {retention_data['retention_periods']}\n")
                f.write("\n")
            
            # Visualization Summary
            if 'visualizations' in self.pipeline_results:
                f.write("VISUALIZATION SUMMARY\n")
                f.write("-" * 40 + "\n")
                for viz_name, viz_path in self.pipeline_results['visualizations'].items():
                    f.write(f"  {viz_name}: {viz_path}\n")
                f.write("\n")
            
            # Execution Metadata
            if 'metadata' in self.pipeline_results:
                f.write("EXECUTION METADATA\n")
                f.write("-" * 40 + "\n")
                metadata = self.pipeline_results['metadata']
                if 'execution_time' in metadata:
                    f.write(f"Execution Time: {metadata['execution_time']:.2f} seconds\n")
                if 'execution_date' in metadata:
                    f.write(f"Execution Date: {metadata['execution_date']}\n")
                if 'data_shape' in metadata and metadata['data_shape']:
                    f.write(f"Final Data Shape: {metadata['data_shape']}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
    
    def run_pipeline(self, data_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the complete analysis pipeline.
        
        Args:
            data_path: Optional path to data file
            
        Returns:
            Dictionary with all pipeline results
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting Complete Analysis Pipeline")
        self.logger.info("=" * 80)
        
        try:
            # Step 1: Load data
            start_time = datetime.now()
            self.load_data(data_path)
            
            # Step 2: Clean data
            self.clean_data()
            
            # Step 3: Validate data
            self.validate_data()
            
            # Step 4: Calculate KPIs
            self.calculate_kpis()
            
            # Step 5: Perform RFM analysis
            self.perform_rfm_analysis()
            
            # Step 6: Perform advanced analytics
            self.perform_advanced_analytics()
            
            # Step 7: Generate visualizations
            self.generate_visualizations()
            
            # Step 8: Export results
            exports = self.export_results()
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
            self.logger.info("=" * 80)
            
            # Add execution metadata
            self.pipeline_results['metadata'] = {
                'execution_time': elapsed_time,
                'execution_date': datetime.now().isoformat(),
                'data_shape': self.cleaned_data.shape if self.cleaned_data is not None else None,
                'config_used': {
                    'data': self.config.get('data', {}),
                    'analysis': self.config.get('analysis', {})
                }
            }
            
            self.pipeline_results['exports'] = exports
            
            return self.pipeline_results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def run_cleaning_only(self, data_path: Optional[str] = None) -> pd.DataFrame:
        """
        Run only the data cleaning part of the pipeline.
        Useful when you just need cleaned data.
        
        Args:
            data_path: Optional path to data file
            
        Returns:
            Cleaned DataFrame
        """
        self.logger.info("Running cleaning-only pipeline...")
        self.load_data(data_path)
        self.clean_data()
        return self.cleaned_data


def main():
    """
    Main entry point for the pipeline.
    """
    # Initialize pipeline with config
    try:
        pipeline = AnalysisPipeline('config/config.yaml')
        
        # Run complete pipeline
        results = pipeline.run_pipeline()
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE EXECUTION SUCCESSFUL")
        print("=" * 60)
        
        if 'metadata' in results:
            metadata = results['metadata']
            print(f"📊 Data processed: {metadata.get('data_shape', 'N/A')}")
            print(f"⏱️  Execution time: {metadata.get('execution_time', 0):.2f} seconds")
        
        if 'exports' in results:
            print(f"📁 Exports: {', '.join(results['exports'].keys())}")
            
        if 'kpis' in results:
            print("\n📈 Key KPIs:")
            kpis = results['kpis']
            for kpi, value in list(kpis.items())[:5]:  # Show first 5 KPIs
                if isinstance(value, (int, float)):
                    if 'amount' in kpi.lower() or 'revenue' in kpi.lower():
                        print(f"  {kpi}: ${value:,.2f}")
                    else:
                        print(f"  {kpi}: {value:,.2f}")
        
        if 'rfm' in results and 'segments' in results['rfm']:
            print("\n👥 Customer Segments:")
            for segment, count in results['rfm']['segments'].items():
                print(f"  {segment.capitalize()}: {count:,} customers")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()