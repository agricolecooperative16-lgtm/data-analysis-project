# src/__init__.py

"""
Data Analysis Project - Source Code
"""

__version__ = '1.0.0'
__author__ = 'agricolecooperative16-lgtm'

# Import all modules for easy access
from .data_loader import DataLoader
from .data_cleaning import DataCleaner
from .data_validation import DataValidator

__all__ = [
    'DataLoader',
    'DataCleaner',
    'DataValidator'
]