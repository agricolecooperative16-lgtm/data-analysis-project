# src/data_validation.py

"""
Data Validation Module

Validates data quality and integrity.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional


class DataValidator:
    """
    A class for validating data quality and integrity.
    """
    
    def __init__(self):
        """Initialize the DataValidator."""
        self.logger = logging.getLogger(__name__)
    
    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive data validation.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        self.logger.info("Starting data validation...")
        
        results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'info': {}
        }
        
        # Check for empty DataFrame
        if df.empty:
            results['valid'] = False
            results['issues'].append("DataFrame is empty")
            return results
        
        # Get basic info
        results['info']['shape'] = df.shape
        results['info']['columns'] = df.columns.tolist()
        results['info']['dtypes'] = df.dtypes.to_dict()
        
        # Check for missing values
        self._check_missing_values(df, results)
        
        # Check for duplicates
        self._check_duplicates(df, results)
        
        # Check for data types
        self._check_data_types(df, results)
        
        # Check for outliers
        self._check_outliers(df, results)
        
        # Check for unreasonable values
        self._check_reasonable_values(df, results)
        
        # Summary
        results['valid'] = len(results['issues']) == 0
        results['info']['total_issues'] = len(results['issues'])
        results['info']['total_warnings'] = len(results['warnings'])
        
        self.logger.info(f"Validation completed. Issues: {len(results['issues'])}, Warnings: {len(results['warnings'])}")
        return results
    
    def _check_missing_values(self, df: pd.DataFrame, results: Dict):
        """Check for missing values."""
        missing_counts = df.isnull().sum()
        missing_cols = missing_counts[missing_counts > 0]
        
        if not missing_cols.empty:
            results['warnings'].append(f"Missing values found in {len(missing_cols)} columns")
            for col, count in missing_cols.items():
                percent = (count / len(df)) * 100
                results['warnings'].append(f"  - '{col}': {count} missing ({percent:.1f}%)")
                
                if percent > 30:
                    results['issues'].append(f"  - '{col}': High missing rate ({percent:.1f}%)")
    
    def _check_duplicates(self, df: pd.DataFrame, results: Dict):
        """Check for duplicate rows."""
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            results['warnings'].append(f"Found {duplicates} duplicate rows ({duplicates/len(df)*100:.1f}%)")
            
            if duplicates / len(df) > 0.1:
                results['issues'].append(f"High duplicate rate: {duplicates/len(df)*100:.1f}%")
    
    def _check_data_types(self, df: pd.DataFrame, results: Dict):
        """Check data types for appropriateness."""
        for col in df.columns:
            # Check if categorical column has too many unique values
            if df[col].dtype == 'object' and len(df[col].unique()) > 50:
                results['warnings'].append(f"'{col}' has {len(df[col].unique())} unique values - consider if categorical")
            
            # Check if numeric column has too few unique values
            if pd.api.types.is_numeric_dtype(df[col]) and len(df[col].unique()) < 5:
                results['warnings'].append(f"'{col}' has only {len(df[col].unique())} unique values - consider if categorical")
    
    def _check_outliers(self, df: pd.DataFrame, results: Dict, threshold: float = 3.0):
        """Check for outliers using Z-score method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            try:
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    outliers = z_scores > threshold
                    
                    if outliers.sum() > 0:
                        percent = (outliers.sum() / len(df)) * 100
                        results['warnings'].append(f"'{col}': {outliers.sum()} outliers ({percent:.1f}%) using Z-score > {threshold}")
            except Exception as e:
                self.logger.warning(f"Could not check outliers for '{col}': {str(e)}")
    
    def _check_reasonable_values(self, df: pd.DataFrame, results: Dict):
        """Check for unreasonable values."""
        # Check for negative values in amount columns
        amount_cols = ['total_amount', 'amount', 'price', 'unit_price']
        for col in amount_cols:
            if col in df.columns:
                if (df[col] < 0).any():
                    results['issues'].append(f"Negative values found in '{col}'")
        
        # Check for zero values in amount columns
        for col in amount_cols:
            if col in df.columns and (df[col] == 0).any():
                count = (df[col] == 0).sum()
                percent = (count / len(df)) * 100
                results['warnings'].append(f"'{col}': {count} zero values ({percent:.1f}%)")
        
        # Check for unrealistic dates
        date_cols = df.select_dtypes(include=['datetime64']).columns
        for col in date_cols:
            try:
                min_date = df[col].min()
                max_date = df[col].max()
                if pd.isna(min_date) or pd.isna(max_date):
                    continue
                # Check if date range is reasonable (not 100+ years)
                if max_date.year - min_date.year > 100:
                    results['warnings'].append(f"'{col}': Large date range of {max_date.year - min_date.year} years")
            except:
                pass