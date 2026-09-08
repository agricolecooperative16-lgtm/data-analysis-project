# src/data_loader.py

"""
Data Loader Module

Handles loading data from various file formats (CSV, Excel, JSON).
Implements Singleton pattern to ensure only one instance exists.
"""

import os
import pandas as pd
import logging
from typing import Optional, Union, List
import threading


class DataLoader:
    """
    A class for loading data from various file formats.
    Implements Singleton pattern.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """
        Ensure only one instance exists (Singleton pattern).
        Thread-safe implementation.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize the DataLoader with default settings.
        Only runs once due to _initialized flag.
        """
        if not self._initialized:
            self._setup_logging()
            self.supported_formats = ['.csv', '.xlsx', '.xls', '.json', '.parquet']
            self._cache = {}
            self._initialized = True
    
    def _setup_logging(self):
        """Setup logging for the DataLoader."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_data(self, file_path: str, use_cache: bool = True, **kwargs) -> pd.DataFrame:
        """
        Load data from a file with automatic format detection.
        
        Args:
            file_path: Path to the data file
            use_cache: Whether to use cached data if available
            **kwargs: Additional arguments to pass to the loading function
            
        Returns:
            DataFrame containing the loaded data
        """
        # Check cache
        if use_cache and file_path in self._cache:
            self.logger.info(f"Returning cached data for: {file_path}")
            return self._cache[file_path].copy()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect file format from extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            df = self.load_csv(file_path, **kwargs)
        elif file_ext in ['.xlsx', '.xls']:
            df = self.load_excel(file_path, **kwargs)
        elif file_ext == '.json':
            df = self.load_json(file_path, **kwargs)
        elif file_ext == '.parquet':
            df = self.load_parquet(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {self.supported_formats}")
        
        # Cache the data
        if use_cache:
            self._cache[file_path] = df.copy()
        
        return df
    
    def load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            **kwargs: Additional pandas read_csv arguments
            
        Returns:
            DataFrame containing the loaded data
        """
        try:
            self.logger.info(f"Loading CSV file: {file_path}")
            # Default encoding handling
            if 'encoding' not in kwargs:
                kwargs['encoding'] = 'utf-8'
            
            df = pd.read_csv(file_path, **kwargs)
            self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            return df
        except UnicodeDecodeError:
            # Try with different encodings
            self.logger.warning("UTF-8 encoding failed, trying 'latin-1'")
            df = pd.read_csv(file_path, encoding='latin-1', **kwargs)
            return df
        except Exception as e:
            self.logger.error(f"Failed to load CSV file: {str(e)}")
            raise
    
    def load_excel(self, file_path: str, sheet_name: Union[str, int] = 0, **kwargs) -> pd.DataFrame:
        """
        Load data from an Excel file.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index to load
            **kwargs: Additional pandas read_excel arguments
            
        Returns:
            DataFrame containing the loaded data
        """
        try:
            self.logger.info(f"Loading Excel file: {file_path}, sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load Excel file: {str(e)}")
            raise
    
    def load_json(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            **kwargs: Additional pandas read_json arguments
            
        Returns:
            DataFrame containing the loaded data
        """
        try:
            self.logger.info(f"Loading JSON file: {file_path}")
            df = pd.read_json(file_path, **kwargs)
            self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load JSON file: {str(e)}")
            raise
    
    def load_parquet(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load data from a Parquet file.
        
        Args:
            file_path: Path to the Parquet file
            **kwargs: Additional pandas read_parquet arguments
            
        Returns:
            DataFrame containing the loaded data
        """
        try:
            self.logger.info(f"Loading Parquet file: {file_path}")
            df = pd.read_parquet(file_path, **kwargs)
            self.logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load Parquet file: {str(e)}")
            raise
    
    def load_multiple_files(self, file_paths: List[str], **kwargs) -> pd.DataFrame:
        """
        Load and concatenate multiple files.
        
        Args:
            file_paths: List of file paths to load
            **kwargs: Additional arguments to pass to load_data
            
        Returns:
            Combined DataFrame
        """
        dfs = []
        for file_path in file_paths:
            try:
                df = self.load_data(file_path, **kwargs)
                dfs.append(df)
            except Exception as e:
                self.logger.warning(f"Failed to load {file_path}: {str(e)}")
        
        if not dfs:
            raise ValueError("No files could be loaded")
        
        combined_df = pd.concat(dfs, ignore_index=True)
        self.logger.info(f"Combined {len(dfs)} files into {len(combined_df)} rows")
        return combined_df
    
    def validate_columns(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Validate that a DataFrame contains required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if all required columns exist, False otherwise
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.warning(f"Missing required columns: {missing_columns}")
            return False
        return True
    
    def clear_cache(self, file_path: Optional[str] = None):
        """
        Clear the data cache.
        
        Args:
            file_path: Specific file to clear from cache, or None to clear all
        """
        if file_path:
            if file_path in self._cache:
                del self._cache[file_path]
                self.logger.info(f"Cleared cache for: {file_path}")
        else:
            self._cache.clear()
            self.logger.info("Cleared all cache")
    
    def get_cache_info(self) -> dict:
        """
        Get information about the current cache.
        
        Returns:
            Dictionary with cache information
        """
        return {
            'cached_files': list(self._cache.keys()),
            'total_files': len(self._cache),
            'total_memory_estimate': sum(df.memory_usage(deep=True).sum() for df in self._cache.values())
        }
    
    def reset_instance(self):
        """
        Reset the singleton instance (for testing purposes only).
        """
        self._instance = None
        self._initialized = False
        self.logger.warning("DataLoader instance reset")