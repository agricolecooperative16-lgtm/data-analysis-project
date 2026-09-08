import pandas as pd
import logging

class DataCleaner:
    def __init__(self, df):
        self.df = df
        self.logger = logging.getLogger(__name__)

    def clean(self):
        """Execute the entire cleaning pipeline."""
        self.logger.info("Starting data cleaning pipeline...")
        self.convert_dates()
        self.remove_duplicates()
        self.calculate_total_amount()
        # ... existing cleaning steps like handling nulls, etc.
        self.logger.info("Data cleaning pipeline finished.")
        return self.df

    def convert_dates(self):
        """Convert columns to datetime, handling errors."""
        date_columns = ['order_date', 'invoice_date'] # Update with your actual date columns
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                self.logger.info(f"Converted column '{col}' to datetime.")
            else:
                self.logger.warning(f"Date column '{col}' not found. Skipping.")

    def remove_duplicates(self):
        """Remove duplicate rows based on a unique identifier or all columns."""
        initial_shape = self.df.shape
        # Use a specific column if you have an 'invoice_id' or 'transaction_id'
        if 'invoice_id' in self.df.columns:
            self.df = self.df.drop_duplicates(subset=['invoice_id'], keep='first')
        else:
            self.df = self.df.drop_duplicates()
        self.logger.info(f"Removed duplicates. Shape changed from {initial_shape} to {self.df.shape}")

    def calculate_total_amount(self):
        """Calculate total amount from quantity and unit price."""
        if 'quantity' in self.df.columns and 'unit_price' in self.df.columns:
            self.df['total_amount'] = self.df['quantity'] * self.df['unit_price']
            self.logger.info("Calculated 'total_amount' column.")
        else:
            self.logger.warning("Columns 'quantity' and/or 'unit_price' not found for total_amount calculation.")