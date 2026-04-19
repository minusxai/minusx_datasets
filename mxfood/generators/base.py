"""Base generator class."""

import csv
import os
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

import sys
sys.path.append('..')
from config import RANDOM_SEED


class BaseGenerator(ABC):
    """Abstract base class for all generators."""

    def __init__(self, output_dir: str = "output", seed: int = None):
        """Initialize the generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed for reproducibility
        """
        self.output_dir = output_dir
        self.seed = seed or RANDOM_SEED
        self._set_seed()
        os.makedirs(output_dir, exist_ok=True)

    def _set_seed(self):
        """Set random seed for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)

    @abstractmethod
    def generate(self) -> pd.DataFrame:
        """Generate the data.

        Returns:
            DataFrame with generated data
        """
        pass

    def save(self, df: pd.DataFrame, filename: str) -> str:
        """Save DataFrame to CSV.

        Args:
            df: DataFrame to save
            filename: Output filename

        Returns:
            Full path to saved file
        """
        filepath = os.path.join(self.output_dir, filename)
        df.to_csv(filepath, index=False, quoting=csv.QUOTE_NONNUMERIC)
        print(f"Saved {len(df)} rows to {filepath}")
        return filepath

    def generate_and_save(self, filename: str) -> pd.DataFrame:
        """Generate data and save to file.

        Args:
            filename: Output filename

        Returns:
            Generated DataFrame
        """
        df = self.generate()
        self.save(df, filename)
        return df


class DataStore:
    """Central store for generated data to share between generators."""

    def __init__(self):
        """Initialize the data store."""
        self.data: Dict[str, pd.DataFrame] = {}
        self.indices: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, df: pd.DataFrame):
        """Store a DataFrame.

        Args:
            key: Storage key
            df: DataFrame to store
        """
        self.data[key] = df

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Get a stored DataFrame.

        Args:
            key: Storage key

        Returns:
            Stored DataFrame or None
        """
        return self.data.get(key)

    def get_ids(self, key: str, id_column: str) -> List[str]:
        """Get list of IDs from a stored DataFrame.

        Args:
            key: Storage key
            id_column: Name of ID column

        Returns:
            List of IDs
        """
        df = self.get(key)
        if df is None:
            return []
        return df[id_column].tolist()

    def get_random_id(self, key: str, id_column: str) -> Optional[str]:
        """Get a random ID from a stored DataFrame.

        Args:
            key: Storage key
            id_column: Name of ID column

        Returns:
            Random ID or None
        """
        ids = self.get_ids(key, id_column)
        if not ids:
            return None
        return random.choice(ids)

    def get_filtered_ids(self, key: str, id_column: str,
                         filter_column: str, filter_value: Any) -> List[str]:
        """Get filtered list of IDs.

        Args:
            key: Storage key
            id_column: Name of ID column
            filter_column: Column to filter on
            filter_value: Value to filter for

        Returns:
            List of matching IDs
        """
        df = self.get(key)
        if df is None:
            return []
        filtered = df[df[filter_column] == filter_value]
        return filtered[id_column].tolist()

    def build_index(self, key: str, index_column: str, value_column: str):
        """Build an index for fast lookups.

        Args:
            key: Storage key
            index_column: Column to index on
            value_column: Column to return values from
        """
        df = self.get(key)
        if df is None:
            return

        index_key = f"{key}_{index_column}_{value_column}"
        self.indices[index_key] = df.groupby(index_column)[value_column].apply(list).to_dict()

    def lookup(self, key: str, index_column: str, value_column: str,
               index_value: Any) -> List[Any]:
        """Look up values using an index.

        Args:
            key: Storage key
            index_column: Column that was indexed
            value_column: Column to get values from
            index_value: Value to look up

        Returns:
            List of matching values
        """
        index_key = f"{key}_{index_column}_{value_column}"
        if index_key not in self.indices:
            self.build_index(key, index_column, value_column)
        return self.indices.get(index_key, {}).get(index_value, [])
