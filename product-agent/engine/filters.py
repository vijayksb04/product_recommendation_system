from typing import List, Dict, Any

def filter_by_category(products: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    Filters products by category (case-insensitive).

    Args:
        products: List of product dictionaries.
        category: The category name to filter by.

    Returns:
        A new list containing products matching the specified category.
    """
    if not category:
        return list(products)

    target_category = category.strip().lower()
    return [
        product for product in products
        if isinstance(product.get("category"), str) and product["category"].strip().lower() == target_category
    ]

def filter_by_budget(
    products: List[Dict[str, Any]], 
    max_price: float, 
    min_price: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Filters products within a price range (inclusive).

    Args:
        products: List of product dictionaries.
        max_price: The maximum acceptable price.
        min_price: The minimum acceptable price. Defaults to 0.0.

    Returns:
        A new list containing products within the specified price range.
    """
    return [
        product for product in products
        if isinstance(product.get("price"), (int, float)) and min_price <= product["price"] <= max_price
    ]

def filter_by_brand(products: List[Dict[str, Any]], brand: str) -> List[Dict[str, Any]]:
    """
    Filters products by brand (case-insensitive).

    Args:
        products: List of product dictionaries.
        brand: The brand name to filter by.

    Returns:
        A new list containing products matching the specified brand.
    """
    if not brand:
        return list(products)

    target_brand = brand.strip().lower()
    return [
        product for product in products
        if isinstance(product.get("brand"), str) and product["brand"].strip().lower() == target_brand
    ]

def filter_by_subcategory(products: List[Dict[str, Any]], subcategory: str) -> List[Dict[str, Any]]:
    """
    Filters products by subcategory (case-insensitive).

    Args:
        products: List of product dictionaries.
        subcategory: The subcategory name to filter by.

    Returns:
        A new list containing products matching the specified subcategory.
    """
    if not subcategory:
        return list(products)

    target_sub = subcategory.strip().lower()
    return [
        product for product in products
        if isinstance(product.get("subcategory"), str) and product["subcategory"].strip().lower() == target_sub
    ]

def filter_by_rating(products: List[Dict[str, Any]], min_rating: float) -> List[Dict[str, Any]]:
    """
    Filters products by minimum rating (inclusive).

    Args:
        products: List of product dictionaries.
        min_rating: The minimum rating (0.0 to 5.0).

    Returns:
        A new list containing products with a rating greater than or equal to min_rating.
    """
    return [
        product for product in products
        if isinstance(product.get("rating"), (int, float)) and product["rating"] >= min_rating
    ]
