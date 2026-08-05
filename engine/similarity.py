from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def init_vectorizer(products: List[Dict[str, Any]]) -> TfidfVectorizer:
    """
    Fits and returns a TfidfVectorizer on the tags corpus of all products in the catalog.

    Args:
        products: A list of product dictionaries.

    Returns:
        A fitted TfidfVectorizer instance.
    """
    corpus = []
    for product in products:
        tags = product.get("tags", [])
        if isinstance(tags, list):
            # Join tags to form a space-separated text document
            corpus.append(" ".join(tags))
        else:
            corpus.append("")
            
    # Set up vectorizer with lowercase conversion and word boundaries
    vectorizer = TfidfVectorizer(lowercase=True, token_pattern=r'(?u)\b\w+\b')
    vectorizer.fit(corpus)
    return vectorizer

def calculate_tag_similarity(
    product_tags: List[str], 
    preferred_tags: List[str], 
    vectorizer: TfidfVectorizer
) -> float:
    """
    Calculates TF-IDF cosine similarity between product tags and user preferred tags.

    Args:
        product_tags: List of strings representing the product's tags.
        preferred_tags: List of strings representing the user's preferred tags.
        vectorizer: A pre-fitted TfidfVectorizer instance.

    Returns:
        A float value between 0.0 and 1.0 representing the cosine similarity.
    """
    if not product_tags or not preferred_tags:
        return 0.0

    prod_text = " ".join(product_tags)
    pref_text = " ".join(preferred_tags)

    try:
        # Transform text into TF-IDF vectors
        vectors = vectorizer.transform([prod_text, pref_text])
        
        # Compute cosine similarity
        sim_matrix = cosine_similarity(vectors[0:1], vectors[1:2])
        score = float(sim_matrix[0][0])
        return max(0.0, min(1.0, score))  # Ensure bound within [0.0, 1.0]
    except Exception:
        return 0.0

def calculate_categorical_similarity(product: Dict[str, Any], user_prefs: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculates categorical match scores (brand, category, subcategory).
    Each matches case-insensitively, returning 1.0 for a match and 0.0 otherwise.

    Args:
        product: Product dictionary.
        user_prefs: User preferences dictionary.

    Returns:
        A dictionary with brand_match, category_match, and subcategory_match scores.
    """
    # 1. Brand match
    prod_brand = str(product.get("brand", "")).strip().lower()
    pref_brand = str(user_prefs.get("preferred_brand", "")).strip().lower()
    brand_match = 1.0 if prod_brand and pref_brand and prod_brand == pref_brand else 0.0

    # 2. Category match
    prod_cat = str(product.get("category", "")).strip().lower()
    pref_cat = str(user_prefs.get("preferred_category", "")).strip().lower()
    category_match = 1.0 if prod_cat and pref_cat and prod_cat == pref_cat else 0.0

    # 3. Subcategory match
    prod_sub = str(product.get("subcategory", "")).strip().lower()
    pref_sub = str(user_prefs.get("preferred_subcategory", "")).strip().lower()
    subcategory_match = 1.0 if prod_sub and pref_sub and prod_sub == pref_sub else 0.0

    return {
        "brand_match": brand_match,
        "category_match": category_match,
        "subcategory_match": subcategory_match
    }

def calculate_similarity_score(
    product: Dict[str, Any], 
    user_prefs: Dict[str, Any], 
    vectorizer: TfidfVectorizer
) -> Dict[str, Any]:
    """
    Computes a combined similarity score between a product and user preferences.

    Weighted breakdown:
    - Tag similarity (TF-IDF): 40% (0.4)
    - Category match: 20% (0.2)
    - Subcategory match: 20% (0.2)
    - Brand match: 20% (0.2)

    Args:
        product: The product dictionary containing tags, brand, category, subcategory.
        user_prefs: The user preferences dictionary containing preferred_tags, etc.
        vectorizer: Pre-fitted TfidfVectorizer.

    Returns:
        A dictionary containing:
        - overall_similarity: Combined weighted score (0.0 to 1.0)
        - tag_similarity: Pure TF-IDF tag similarity (0.0 to 1.0)
        - category_match: 1.0 or 0.0
        - subcategory_match: 1.0 or 0.0
        - brand_match: 1.0 or 0.0
    """
    # Tag similarity
    prod_tags = product.get("tags", [])
    pref_tags = user_prefs.get("preferred_tags", [])
    tag_sim = calculate_tag_similarity(prod_tags, pref_tags, vectorizer)

    # Categorical matches
    cat_sims = calculate_categorical_similarity(product, user_prefs)

    # Weighted calculation
    overall_sim = (
        (tag_sim * 0.4) +
        (cat_sims["category_match"] * 0.2) +
        (cat_sims["subcategory_match"] * 0.2) +
        (cat_sims["brand_match"] * 0.2)
    )

    return {
        "overall_similarity": float(overall_sim),
        "tag_similarity": float(tag_sim),
        "category_match": cat_sims["category_match"],
        "subcategory_match": cat_sims["subcategory_match"],
        "brand_match": cat_sims["brand_match"]
    }
