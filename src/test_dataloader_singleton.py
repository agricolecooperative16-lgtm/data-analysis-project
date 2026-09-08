# tests/test_dataloader_singleton.py

"""
Tests for DataLoader Singleton pattern.
"""

import pytest
import os
import pandas as pd
from src.data_loader import DataLoader


class TestDataLoaderSingleton:
    """Test DataLoader Singleton functionality."""
    
    @pytest.mark.unit
    def test_singleton_pattern(self):
        """Test that DataLoader follows Singleton pattern."""
        # Create two instances
        loader1 = DataLoader()
        loader2 = DataLoader()
        
        # They should be the same object
        assert loader1 is loader2
        assert id(loader1) == id(loader2)
        
        # Check that they share state
        loader1.test_attribute = "test_value"
        assert hasattr(loader2, "test_attribute")
        assert loader2.test_attribute == "test_value"
    
    @pytest.mark.unit
    def test_singleton_with_initialization(self):
        """Test singleton with different initialization attempts."""
        # First initialization
        loader1 = DataLoader()
        
        # Try to create with different parameters
        # The singleton should ignore new parameters
        loader2 = DataLoader()
        
        assert loader1 is loader2
        
        # Check if both have the same logger
        assert loader1.logger is loader2.logger
    
    @pytest.mark.unit
    def test_singleton_state_persistence(self, temp_test_dir):
        """Test that singleton maintains state."""
        loader1 = DataLoader()
        
        # Set state through first instance
        loader1._custom_state = {"loaded_files": []}
        loader1._custom_state["loaded_files"].append("file1.csv")
        
        # Get second instance
        loader2 = DataLoader()
        
        # State should be maintained
        assert hasattr(loader2, "_custom_state")
        assert "file1.csv" in loader2._custom_state["loaded_files"]
        
        # Modify through second instance
        loader2._custom_state["loaded_files"].append("file2.csv")
        
        # First instance should reflect changes
        assert "file2.csv" in loader1._custom_state["loaded_files"]
    
    @pytest.mark.unit
    def test_singleton_clear_state(self):
        """Test clearing singleton state."""
        loader1 = DataLoader()
        loader1._custom_state = {"test": "value"}
        
        # Clear instance (for testing purposes)
        DataLoader._instance = None
        
        # Create new instance
        loader2 = DataLoader()
        
        # Should be a new instance
        assert loader1 is not loader2
        
        # Should not have old state
        assert not hasattr(loader2, "_custom_state")
    
    @pytest.mark.unit
    def test_singleton_thread_safety(self):
        """Test singleton thread safety (basic test)."""
        import threading
        
        instances = []
        
        def create_instance():
            instances.append(DataLoader())
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance
    
    @pytest.mark.unit
    def test_singleton_with_config(self, temp_test_dir):
        """Test singleton with configuration."""
        loader1 = DataLoader()
        
        # Set config through first instance
        loader1.supported_formats = ['.csv', '.xlsx']
        
        # Get second instance
        loader2 = DataLoader()
        
        # Config should be shared
        assert loader2.supported_formats == ['.csv', '.xlsx']
        
        # Modify through second instance
        loader2.supported_formats.append('.json')
        
        # First instance should reflect changes
        assert '.json' in loader1.supported_formats
    
    @pytest.mark.unit
    def test_singleton_data_loading(self, temp_test_dir, sample_data):
        """Test singleton with data loading operations."""
        loader1 = DataLoader()
        
        # Create test file
        test_file = os.path.join(temp_test_dir, 'test_data.csv')
        sample_data.to_csv(test_file, index=False)
        
        # Load data through first instance
        df1 = loader1.load_data(test_file)
        
        # Get second instance
        loader2 = DataLoader()
        
        # Load same data through second instance
        df2 = loader2.load_data(test_file)
        
        # Both should load correctly
        assert df1 is not df2  # Different DataFrames (by value, not reference)
        pd.testing.assert_frame_equal(df1, df2)
        
        # Check that loader state is shared
        assert hasattr(loader1, 'logger')
        assert hasattr(loader2, 'logger')
        assert loader1.logger is loader2.logger
    
    @pytest.mark.unit
    def test_singleton_instance_reset(self):
        """Test resetting singleton instance."""
        loader1 = DataLoader()
        loader1._test_state = "original"
        
        # Reset singleton
        DataLoader._instance = None
        DataLoader._initialized = False
        
        # Create new instance
        loader2 = DataLoader()
        
        # Should be new instance
        assert loader1 is not loader2
        
        # Should not have old state
        assert not hasattr(loader2, "_test_state")
        
        # Clean up - reset singleton for other tests
        DataLoader._instance = None
        DataLoader._initialized = False
    
    @pytest.mark.unit
    def test_singleton_with_inheritance(self):
        """Test singleton with inheritance."""
        # Create a subclass
        class CustomDataLoader(DataLoader):
            def __init__(self):
                super().__init__()
                self.custom_attribute = "custom"
        
        # Create instances
        loader1 = CustomDataLoader()
        loader2 = CustomDataLoader()
        
        # Should follow singleton pattern
        assert loader1 is loader2
        assert loader1.custom_attribute == "custom"
        assert loader2.custom_attribute == "custom"
        
        # Modify through subclass
        loader1.custom_attribute = "modified"
        assert loader2.custom_attribute == "modified"
    
    @pytest.mark.unit
    def test_singleton_cleanup_for_tests(self):
        """Test cleanup of singleton between tests."""
        # This test ensures singleton is cleaned up properly
        # Create and clear instance multiple times
        for i in range(3):
            loader = DataLoader()
            loader._test_value = i
            
            # Clear for next iteration
            DataLoader._instance = None
            DataLoader._initialized = False
        
        # Final instance should have fresh state
        final_loader = DataLoader()
        assert not hasattr(final_loader, "_test_value")
        
        # Clean up
        DataLoader._instance = None
        DataLoader._initialized = False


# Fixture to ensure singleton is reset after tests
@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton after each test."""
    yield
    # Reset singleton to ensure clean state for next test
    DataLoader._instance = None
    DataLoader._initialized = False