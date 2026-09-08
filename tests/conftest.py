# tests/conftest.py

"""
Configuration and fixtures for pytest.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
import tempfile
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import project modules with proper error handling
try:
    from src.pipeline import AnalysisPipeline
    from src.data_loader import DataLoader
    from src.data_cleaning import DataCleaner
    from src.data_validation import DataValidator
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Project root: {project_root}")


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        'data': {
            'raw_path': 'tests/data/raw/',
            'processed_path': 'tests/data/processed/',
            'external_path': 'tests/data/external/',
            'sales_file': 'test_sales_data.csv',
            'customers_file': 'test_customers_data.csv',
            'products_file': 'test_products_data.csv'
        },
        'analysis': {
            'date_column': 'transaction_date',
            'customer_id': 'customer_id',
            'product_id': 'product_id',
            'quantity_column': 'quantity',
            'price_column': 'unit_price',
            'amount_column': 'total_amount',
            'rfm': {
                'recency_weight': 0.4,
                'frequency_weight': 0.3,
                'monetary_weight': 0.3,
                'segments': {
                    'vip': [4, 5],
                    'loyal': [3, 4],
                    'potential': [2, 3],
                    'at_risk': [1, 2],
                    'lost': [0, 1]
                }
            }
        },
        'models': {
            'segmentation': {
                'n_clusters': 4,
                'random_state': 42,
                'max_iter': 300,
                'n_init': 10
            },
            'forecasting': {
                'test_size': 0.2,
                'seasonality_period': 12,
                'models': ['linear_regression']
            }
        },
        'visualization': {
            'figure_size': [12, 8],
            'color_palette': 'Set2',
            'dpi': 100,
            'save_figures': False,
            'figure_format': 'png'
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'file': 'logs/test_app.log'
        }
    }


@pytest.fixture(scope="session")
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    
    # Create date range
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # Generate sample data
    n_records = 1000
    data = {
        'transaction_date': np.random.choice(dates, n_records),
        'customer_id': np.random.randint(1, 101, n_records),
        'product_id': np.random.randint(1, 21, n_records),
        'quantity': np.random.randint(1, 10, n_records),
        'unit_price': np.round(np.random.uniform(10, 100, n_records), 2),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], n_records)
    }
    
    df = pd.DataFrame(data)
    
    # Add some duplicates
    duplicate_rows = df.iloc[:10].copy()
    df = pd.concat([df, duplicate_rows], ignore_index=True)
    
    # Add some missing values
    df.loc[np.random.choice(df.index, 5), 'unit_price'] = np.nan
    df.loc[np.random.choice(df.index, 5), 'quantity'] = np.nan
    
    return df


@pytest.fixture(scope="session")
def sample_data_with_duplicates():
    """Create sample data with explicit duplicates."""
    data = {
        'transaction_date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-03'],
        'customer_id': [1, 1, 2, 3],
        'product_id': [101, 101, 102, 103],
        'quantity': [2, 2, 1, 3],
        'unit_price': [50.0, 50.0, 30.0, 20.0]
    }
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def temp_test_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="test_analysis_")
    yield temp_dir
    # Clean up
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def pipeline_with_test_config(test_config, temp_test_dir):
    """Create a pipeline instance with test configuration."""
    # Update config paths to use temp directory
    test_config['data']['raw_path'] = os.path.join(temp_test_dir, 'data/raw/')
    test_config['data']['processed_path'] = os.path.join(temp_test_dir, 'data/processed/')
    test_config['data']['external_path'] = os.path.join(temp_test_dir, 'data/external/')
    
    # Create directories
    for path in [
        test_config['data']['raw_path'],
        test_config['data']['processed_path'],
        test_config['data']['external_path']
    ]:
        os.makedirs(path, exist_ok=True)
    
    # Save test config
    config_path = os.path.join(temp_test_dir, 'test_config.yaml')
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(test_config, f)
    
    # Create pipeline with test config
    try:
        pipeline = AnalysisPipeline(config_path)
        return pipeline, temp_test_dir
    except ImportError as e:
        pytest.skip(f"Skipping pipeline tests: {e}")