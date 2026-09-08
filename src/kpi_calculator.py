# src/kpi_calculator.py

"""
KPI Calculator Module

Calculates key performance indicators.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any


class KPICalculator:
    """
    A class for calculating key performance indicators.
    """
    
    def __init__(self):
        """Initialize the KPICalculator."""
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate all KPIs.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            Dictionary with KPI results
        """
        self.logger.info("Calculating KPIs...")
        
        kpis = {}
        
        # Sales KPIs
        kpis['total_sales'] = self.calculate_total_sales(df)
        kpis['average_transaction_value'] = self.calculate_average_transaction_value(df)
        kpis['average_order_value'] = kpis['average_transaction_value']
        
        # Customer KPIs
        kpis['customer_count'] = self.calculate_customer_count(df)
        kpis['average_customer_value'] = self.calculate_average_customer_value(df)
        kpis['customer_conversion_rate'] = self.calculate_conversion_rate(df)
        
        # Product KPIs
        kpis['product_count'] = self.calculate_product_count(df)
        kpis['average_price'] = self.calculate_average_price(df)
        
        # Time KPIs
        kpis['sales_growth_rate'] = self.calculate_sales_growth_rate(df)
        
        # Quality KPIs
        kpis['return_rate'] = self.calculate_return_rate(df)
        
        self.logger.info(f"Calculated {len(kpis)} KPIs")
        return kpis
    
    def calculate_total_sales(self, df: pd.DataFrame) -> float:
        """Calculate total sales."""
        amount_col = 'total_amount'
        if amount_col in df.columns:
            return df[amount_col].sum()
        return 0.0
    
    def calculate_average_transaction_value(self, df: pd.DataFrame) -> float:
        """Calculate average transaction value."""
        amount_col = 'total_amount'
        if amount_col in df.columns:
            return df[amount_col].mean()
        return 0.0
    
    def calculate_customer_count(self, df: pd.DataFrame) -> int:
        """Calculate total number of unique customers."""
        customer_col = 'customer_id'
        if customer_col in df.columns:
            return df[customer_col].nunique()
        return 0
    
    def calculate_average_customer_value(self, df: pd.DataFrame) -> float:
        """Calculate average customer value."""
        customer_col = 'customer_id'
        amount_col = 'total_amount'
        
        if customer_col in df.columns and amount_col in df.columns:
            customer_values = df.groupby(customer_col)[amount_col].sum()
            return customer_values.mean()
        return 0.0
    
    def calculate_product_count(self, df: pd.DataFrame) -> int:
        """Calculate total number of unique products."""
        product_col = 'product_id'
        if product_col in df.columns:
            return df[product_col].nunique()
        return 0
    
    def calculate_average_price(self, df: pd.DataFrame) -> float:
        """Calculate average unit price."""
        price_col = 'unit_price'
        if price_col in df.columns:
            return df[price_col].mean()
        return 0.0
    
    def calculate_conversion_rate(self, df: pd.DataFrame) -> float:
        """Calculate customer conversion rate."""
        # Simplified - actual conversion rate would need visitor data
        return 100.0  # Placeholder
    
    def calculate_sales_growth_rate(self, df: pd.DataFrame) -> float:
        """Calculate sales growth rate."""
        date_col = 'transaction_date'
        amount_col = 'total_amount'
        
        if date_col not in df.columns or amount_col not in df.columns:
            return 0.0
        
        df[date_col] = pd.to_datetime(df[date_col])
        df['month'] = df[date_col].dt.to_period('M')
        
        monthly_sales = df.groupby('month')[amount_col].sum()
        
        if len(monthly_sales) >= 2:
            recent = monthly_sales.iloc[-1]
            previous = monthly_sales.iloc[-2]
            if previous > 0:
                return ((recent - previous) / previous) * 100
        
        return 0.0
    
    def calculate_return_rate(self, df: pd.DataFrame) -> float:
        """Calculate return rate."""
        # Simplified - would need return data
        return 0.0  # Placeholder