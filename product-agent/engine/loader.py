import os
import json
from typing import List, Dict, Any, Set

class CatalogError(Exception):
    """Base exception for all catalog-related errors."""
    pass

class CatalogFileNotFoundError(CatalogError, FileNotFoundError):
    """Raised when the catalog file is not found."""
    pass

class CatalogValidationError(CatalogError, ValueError):
    """Raised when the catalog JSON is malformed or violates the schema requirements."""
    pass

def load_catalog(path: str = "catalog.json") -> List[Dict[str, Any]]:
    """
    Loads and validates the product catalog from a JSON file.

    Args:
        path: Path to the catalog JSON file. Defaults to "catalog.json".

    Returns:
        A list of dictionaries representing the products.

    Raises:
        CatalogFileNotFoundError: If the file at the specified path does not exist.
        CatalogValidationError: If the JSON is malformed, not a list, or fails key validation.
    """
    if not os.path.exists(path):
        raise CatalogFileNotFoundError(f"Catalog file not found at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CatalogValidationError(f"Malformed JSON: Failed to decode catalog file. Details: {e}")
    except Exception as e:
        raise CatalogError(f"An unexpected error occurred while reading the catalog: {e}")

    if not isinstance(data, list):
        raise CatalogValidationError("Invalid catalog format: Root element must be a JSON array (list of products).")

    # Define schema expectations
    required_keys = {"id", "name", "category", "subcategory", "brand", "price", "rating", "tags"}

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise CatalogValidationError(f"Invalid product at index {idx}: Product must be a JSON object.")

        # Check for missing keys
        missing_keys = required_keys - item.keys()
        if missing_keys:
            raise CatalogValidationError(
                f"Invalid product schema at index {idx} (ID: {item.get('id', 'Unknown')}): "
                f"Missing required keys: {missing_keys}"
            )

        # Validate types for key fields
        if not isinstance(item["id"], (int, str)):
            raise CatalogValidationError(f"Invalid product ID at index {idx}: ID must be an integer or string.")
        
        if not isinstance(item["name"], str) or not item["name"].strip():
            raise CatalogValidationError(f"Invalid product name at index {idx}: Name must be a non-empty string.")

        if not isinstance(item["category"], str) or not item["category"].strip():
            raise CatalogValidationError(f"Invalid product category at index {idx}: Category must be a non-empty string.")

        if not isinstance(item["subcategory"], str) or not item["subcategory"].strip():
            raise CatalogValidationError(f"Invalid product subcategory at index {idx}: Subcategory must be a non-empty string.")

        if not isinstance(item["brand"], str) or not item["brand"].strip():
            raise CatalogValidationError(f"Invalid product brand at index {idx}: Brand must be a non-empty string.")

        if not isinstance(item["price"], (int, float)) or item["price"] < 0:
            raise CatalogValidationError(f"Invalid price at index {idx}: Price must be a non-negative number.")

        if not isinstance(item["rating"], (int, float)) or not (0 <= item["rating"] <= 5):
            raise CatalogValidationError(f"Invalid rating at index {idx}: Rating must be a number between 0 and 5.")

        if not isinstance(item["tags"], list) or not all(isinstance(tag, str) for tag in item["tags"]):
            raise CatalogValidationError(f"Invalid tags at index {idx}: Tags must be a list of strings.")

    return data

def get_categories(products: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts all unique categories from the product list, sorted alphabetically.

    Args:
        products: A list of product dictionaries.

    Returns:
        A sorted list of unique category names.
    """
    categories: Set[str] = set()
    for product in products:
        category = product.get("category")
        if isinstance(category, str) and category.strip():
            categories.add(category.strip())
    return sorted(list(categories))

def get_brands(products: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts all unique brands from the product list, sorted alphabetically.

    Args:
        products: A list of product dictionaries.

    Returns:
        A sorted list of unique brand names.
    """
    brands: Set[str] = set()
    for product in products:
        brand = product.get("brand")
        if isinstance(brand, str) and brand.strip():
            brands.add(brand.strip())
    return sorted(list(brands))

def get_subcategories(products: List[Dict[str, Any]], category: str) -> List[str]:
    """
    Extracts all unique subcategories belonging to a specific category, sorted alphabetically.
    Comparison with the category name is case-insensitive.

    Args:
        products: A list of product dictionaries.
        category: The category name to filter subcategories by.

    Returns:
        A sorted list of unique subcategory names matching the specified category.
    """
    if not category:
        return []

    target_category = category.strip().lower()
    subcategories: Set[str] = set()

    for product in products:
        prod_category = product.get("category")
        if isinstance(prod_category, str) and prod_category.strip().lower() == target_category:
            subcategory = product.get("subcategory")
            if isinstance(subcategory, str) and subcategory.strip():
                subcategories.add(subcategory.strip())

    return sorted(list(subcategories))
