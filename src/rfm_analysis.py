# src/rfm_analysis.py

"""
RFM Analysis Module

Performs Recency, Frequency, Monetary analysis for customer segmentation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime


class RFMAnalyzer:
    """
    A class for performing RFM analysis.
    """
    
    def __init__(self):
        """Initialize the RFMAnalyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, df: pd.DataFrame, 
                customer_col: str = 'customer_id',
                date_col: str = 'transaction_date',
                amount_col: str = 'total_amount',
                config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform RFM analysis.
        
        Args:
            df: DataFrame with transaction data
            customer_col: Customer ID column name
            date_col: Transaction date column name
            amount_col: Transaction amount column name
            config: Optional configuration
            
        Returns:
            Dictionary with RFM results
        """
        self.logger.info("Performing RFM analysis...")
        
        # Ensure date column is datetime
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Calculate RFM metrics
        today = df[date_col].max()
        
        rfm_data = df.groupby(customer_col).agg({
            date_col: lambda x: (today - x.max()).days,
            customer_col: 'count',
            amount_col: 'sum'
        }).rename(columns={
            date_col: 'recency',
            customer_col: 'frequency',
            amount_col: 'monetary'
        })
        
        # Calculate RFM scores
        rfm_data['r_score'] = pd.qcut(rfm_data['recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
        rfm_data['f_score'] = pd.qcut(rfm_data['frequency'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        rfm_data['m_score'] = pd.qcut(rfm_data['monetary'], 5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Convert scores to numeric
        rfm_data['r_score'] = rfm_data['r_score'].astype(int)
        rfm_data['f_score'] = rfm_data['f_score'].astype(int)
        rfm_data['m_score'] = rfm_data['m_score'].astype(int)
        
        # Calculate total RFM score
        weights = config.get('rfm', {}) if config else {}
        r_weight = weights.get('recency_weight', 0.4)
        f_weight = weights.get('frequency_weight', 0.3)
        m_weight = weights.get('monetary_weight', 0.3)
        
        rfm_data['rfm_score'] = (rfm_data['r_score'] * r_weight + 
                                rfm_data['f_score'] * f_weight + 
                                rfm_data['m_score'] * m_weight)
        
        # Assign segments
        segments = config.get('rfm', {}).get('segments', {})
        if segments:
            rfm_data['segment'] = self._assign_segments(rfm_data['rfm_score'], segments)
        else:
            # Default segments
            rfm_data['segment'] = pd.cut(rfm_data['rfm_score'], 
                                        bins=5, 
                                        labels=['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'])
        
        # Calculate segment distribution
        segment_distribution = rfm_data['segment'].value_counts().to_dict()
        
        results = {
            'rfm_data': rfm_data,
            'segments': segment_distribution,
            'rfm_scores': {
                'recency': rfm_data['r_score'].mean(),
                'frequency': rfm_data['f_score'].mean(),
                'monetary': rfm_data['m_score'].mean(),
                'overall': rfm_data['rfm_score'].mean()
            },
            'total_customers': len(rfm_data)
        }
        
        self.logger.info(f"RFM analysis completed. Segments: {segment_distribution}")
        return results
    
    def _assign_segments(self, scores: pd.Series, segments: Dict) -> pd.Series:
        """Assign segment labels based on RFM scores."""
        def get_segment(score):
            for segment, thresholds in segments.items():
                if thresholds[0] <= score <= thresholds[1]:
                    return segment
            return 'other'
        
        return scores.apply(get_segment)