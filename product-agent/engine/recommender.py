from typing import List, Dict, Any
from engine import filters
from engine import similarity
from engine import scorer

def recommend_products(
    products: List[Dict[str, Any]],
    user_preferences: Dict[str, Any],
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Coordinates the recommendation pipeline:
    1. Fits the TF-IDF vectorizer on the entire products catalog.
    2. Applies filters if hard filter criteria are specified in user_preferences.
    3. Calculates similarity scores.
    4. Calculates final recommendation scores.
    5. Sorts the results by score descending and returns the top N.

    Args:
        products: The complete catalog of products.
        user_preferences: A dictionary representing user preferences. Expected keys:
            - preferred_tags (List[str])
            - preferred_brand (str)
            - preferred_category (str)
            - preferred_subcategory (str)
            - budget (float) - Optional budget limit
            - filter_category (str) - Optional hard filter
            - filter_brand (str) - Optional hard filter
            - filter_subcategory (str) - Optional hard filter
            - filter_min_rating (float) - Optional hard filter
            - filter_max_price (float) - Optional hard filter
        top_n: The number of recommendations to return. Defaults to 5.

    Returns:
        A sorted list of dictionaries representing the recommended products:
        [
            {
                "product": dict,
                "score": float,
                "similarity": float,
                "score_breakdown": dict
            }
        ]
    """
    if not products:
        return []

    # Initialize and fit TF-IDF vectorizer on the full catalog tags
    vectorizer = similarity.init_vectorizer(products)

    # Start with all products as candidates
    candidates = list(products)

    # Apply hard filters if present in user preferences
    if "filter_category" in user_preferences and user_preferences["filter_category"]:
        candidates = filters.filter_by_category(candidates, user_preferences["filter_category"])

    if "filter_brand" in user_preferences and user_preferences["filter_brand"]:
        candidates = filters.filter_by_brand(candidates, user_preferences["filter_brand"])

    if "filter_subcategory" in user_preferences and user_preferences["filter_subcategory"]:
        candidates = filters.filter_by_subcategory(candidates, user_preferences["filter_subcategory"])

    if "filter_min_rating" in user_preferences and user_preferences["filter_min_rating"] is not None:
        try:
            min_rating = float(user_preferences["filter_min_rating"])
            candidates = filters.filter_by_rating(candidates, min_rating)
        except (ValueError, TypeError):
            pass

    if "filter_max_price" in user_preferences and user_preferences["filter_max_price"] is not None:
        try:
            max_price = float(user_preferences["filter_max_price"])
            candidates = filters.filter_by_budget(candidates, max_price)
        except (ValueError, TypeError):
            pass

    # Score candidates
    scored_recommendations = []
    for product in candidates:
        # Calculate similarity
        sim_res = similarity.calculate_similarity_score(product, user_preferences, vectorizer)
        
        # Calculate final recommendation score
        score_res = scorer.calculate_final_score(product, user_preferences, sim_res)

        scored_recommendations.append({
            "product": product,
            "score": score_res["final_score"],
            "similarity": sim_res["overall_similarity"],
            "score_breakdown": score_res["breakdown"]
        })

    # Sort candidates by final score descending
    scored_recommendations.sort(key=lambda x: x["score"], reverse=True)

    return scored_recommendations[:top_n]
