from typing import Dict, Any, Union, Tuple

def calculate_budget_score(price: float, budget: float) -> Tuple[float, str]:
    """
    Computes a score based on product price and user budget.
    - Within budget = 1.0
    - Slightly above budget (<= 20% over) = 0.5
    - Far above budget (> 20% over) = -0.5 (penalty)

    Args:
        price: The product price.
        budget: The user's maximum budget.

    Returns:
        A tuple of (score, explanation_string).
    """
    if price <= budget:
        return 1.0, "Within budget (full score)."
    elif price <= budget * 1.2:
        return 0.5, f"Slightly above budget by {((price / budget) - 1.0) * 100:.1f}% (partial score)."
    else:
        return -0.5, f"Far above budget by {((price / budget) - 1.0) * 100:.1f}% (penalty)."

def calculate_final_score(
    product: Dict[str, Any],
    user_prefs: Dict[str, Any],
    similarity_score: Union[float, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes a final recommendation score combining multiple factors:
    - 40% Tag Similarity
    - 25% Budget Match
    - 15% Brand Match
    - 10% Product Rating
    - 10% Category/Subcategory Match

    Args:
        product: The product dictionary containing price, rating, brand, category, subcategory.
        user_prefs: The user preferences containing budget/max_budget, preferred_brand, etc.
        similarity_score: Either a float representing tag similarity, or the dictionary
                          returned from similarity.calculate_similarity_score.

    Returns:
        A dictionary containing:
        - final_score: The final weighted numerical recommendation score (clamped to min 0.0).
        - raw_final_score: The raw mathematical score before clamping.
        - breakdown: A dictionary showing individual weighted and raw component scores.
    """
    # 1. Parse similarity metrics
    if isinstance(similarity_score, dict):
        tag_sim = float(similarity_score.get("tag_similarity", 0.0))
        brand_match = float(similarity_score.get("brand_match", 0.0))
        category_match = float(similarity_score.get("category_match", 0.0))
        subcategory_match = float(similarity_score.get("subcategory_match", 0.0))
    else:
        # If float, treat as tag similarity and calculate other matches dynamically
        tag_sim = float(similarity_score)
        
        prod_brand = str(product.get("brand", "")).strip().lower()
        pref_brand = str(user_prefs.get("preferred_brand", "")).strip().lower()
        brand_match = 1.0 if prod_brand and pref_brand and prod_brand == pref_brand else 0.0

        prod_cat = str(product.get("category", "")).strip().lower()
        pref_cat = str(user_prefs.get("preferred_category", "")).strip().lower()
        category_match = 1.0 if prod_cat and pref_cat and prod_cat == pref_cat else 0.0

        prod_sub = str(product.get("subcategory", "")).strip().lower()
        pref_sub = str(user_prefs.get("preferred_subcategory", "")).strip().lower()
        subcategory_match = 1.0 if prod_sub and pref_sub and prod_sub == pref_sub else 0.0

    # 2. Budget match calculation
    price = float(product.get("price", 0.0))
    budget_limit = user_prefs.get("budget") or user_prefs.get("max_budget") or user_prefs.get("preferred_budget")
    
    if budget_limit is None:
        budget_score = 1.0
        budget_expl = "No budget constraints specified (defaulting to full match)."
    else:
        try:
            budget_score, budget_expl = calculate_budget_score(price, float(budget_limit))
        except (ValueError, TypeError):
            budget_score = 1.0
            budget_expl = "Invalid budget specification (defaulting to full match)."

    # 3. Product Rating match (normalize 0-5 scale to 0-1)
    raw_rating = float(product.get("rating", 0.0))
    rating_score = max(0.0, min(1.0, raw_rating / 5.0))

    # 4. Category/Subcategory Match (10% weight)
    cat_sub_score = (category_match + subcategory_match) / 2.0

    # 5. Compute Weighted Score Components
    weighted_tag = tag_sim * 0.40
    weighted_budget = budget_score * 0.25
    weighted_brand = brand_match * 0.15
    weighted_rating = rating_score * 0.10
    weighted_cat_sub = cat_sub_score * 0.10

    raw_final = weighted_tag + weighted_budget + weighted_brand + weighted_rating + weighted_cat_sub
    final_score = max(0.0, raw_final) # Clamp to 0.0 if negative due to budget penalty

    return {
        "final_score": float(final_score),
        "raw_final_score": float(raw_final),
        "breakdown": {
            "tag_similarity": {
                "raw": tag_sim,
                "weighted": weighted_tag,
                "percentage_weight": 40
            },
            "budget_match": {
                "raw": budget_score,
                "weighted": weighted_budget,
                "percentage_weight": 25,
                "explanation": budget_expl
            },
            "brand_match": {
                "raw": brand_match,
                "weighted": weighted_brand,
                "percentage_weight": 15
            },
            "product_rating": {
                "raw": raw_rating,
                "normalized": rating_score,
                "weighted": weighted_rating,
                "percentage_weight": 10
            },
            "category_subcategory": {
                "raw": cat_sub_score,
                "category_match": category_match,
                "subcategory_match": subcategory_match,
                "weighted": weighted_cat_sub,
                "percentage_weight": 10
            }
        }
    }
