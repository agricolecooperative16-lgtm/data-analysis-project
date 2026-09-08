# tests/test_data_loader.py

"""
Unit tests for data loader module.
"""

import pytest
import pandas as pd
import os
from src.data_loader import DataLoader


class TestDataLoader:
    """Test data loading functionality."""
    
    @pytest.mark.unit
    def test_data_loader_initialization(self):
        """Test DataLoader initialization."""
        loader = DataLoader()
        assert loader is not None
    
    @pytest.mark.unit
    def test_load_csv(self, temp_test_dir, sample_data):
        """Test loading CSV file."""
        # Create test CSV
        file_path = os.path.join(temp_test_dir, 'test_data.csv')
        sample_data.to_csv(file_path, index=False)
        
        # Load data
        loader = DataLoader()
        df = loader.load_csv(file_path)
        
        assert df is not None
        assert len(df) == len(sample_data)
        assert all(col in df.columns for col in sample_data.columns)
    
    @pytest.mark.unit
    def test_load_excel(self, temp_test_dir, sample_data):
        """Test loading Excel file."""
        # Create test Excel file
        file_path = os.path.join(temp_test_dir, 'test_data.xlsx')
        sample_data.to_excel(file_path, index=False)
        
        # Load data
        loader = DataLoader()
        df = loader.load_excel(file_path)
        
        assert df is not None
        assert len(df) == len(sample_data)
    
    @pytest.mark.unit
    def test_load_data_auto_detect(self, temp_test_dir, sample_data):
        """Test auto-detection of file format."""
        loader = DataLoader()
        
        # Test CSV
        csv_path = os.path.join(temp_test_dir, 'test.csv')
        sample_data.to_csv(csv_path, index=False)
        df_csv = loader.load_data(csv_path)
        assert df_csv is not None
        
        # Test Excel
        excel_path = os.path.join(temp_test_dir, 'test.xlsx')
        sample_data.to_excel(excel_path, index=False)
        df_excel = loader.load_data(excel_path)
        assert df_excel is not None
    
    @pytest.mark.unit
    def test_load_unsupported_format(self, temp_test_dir):
        """Test loading unsupported file format."""
        file_path = os.path.join(temp_test_dir, 'test.txt')
        with open(file_path, 'w') as f:
            f.write('test data')
        
        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.load_data(file_path)
    
    @pytest.mark.unit
    def test_load_missing_file(self):
        """Test loading missing file."""
        loader = DataLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_data('non_existent_file.csv')
    
    @pytest.mark.unit
    def test_validate_columns(self, sample_data):
        """Test column validation."""
        loader = DataLoader()
        
        required_cols = ['transaction_date', 'customer_id', 'quantity']
        # Should pass
        assert loader.validate_columns(sample_data, required_cols) is True
        
        # Should fail
        required_cols_missing = ['transaction_date', 'non_existent_column']
        assert loader.validate_columns(sample_data, required_cols_missing) is False