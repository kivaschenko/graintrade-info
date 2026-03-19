"""
Tripoli Land Transformer Module
----------------------------
Get data from storage, transform it to match the Commodity model, and prepare for loading.
Uses the BaseTransformer protocol for structure.
"""

import pandas as pd

class TripoliLandTransformer:
    """
    Transformer for Tripoli Land commodity data.
    Transforms raw Tripoli Land data into the Commodity model format.
    """

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        # Example transformation logic
        transformed_data = data.copy()

        # Rename columns to match Commodity model
        transformed_data.rename(columns={
            'commodity_name': 'name',
            'commodity_variety': 'variety',
            'commodity_region': 'region',
            'commodity_price': 'price',
            'price_currency': 'currency',
            'price_unit': 'unit',
            'quality_grade_info': 'quality_grade',
            'protein_pct': 'protein_content',
            'moisture_pct': 'moisture_content',
            'recorded_date': 'date',
            'data_source_type': 'source_type',
            'data_source_name': 'source_name'
        }, inplace=True)

        # Convert date column to datetime
        transformed_data['date'] = pd.to_datetime(transformed_data['date']) 
        # Ensure price is float
        transformed_data['price'] = transformed_data['price'].astype(float)
        # Additional transformations can be added here
        return transformed_data