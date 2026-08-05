import os
import sys

# Add the parent directory of the script to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import loader, filters, similarity, scorer, recommender

def run_integration_test():
    print("==================================================")
    print("Running Integration Test for Product Rec Agent...")
    print("==================================================")

    # Resolve local path for catalog.json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(base_dir, "catalog.json")

    # 1. Load Catalog
    print(f"\n[Step 1] Loading catalog from: {catalog_path}")
    try:
        products = loader.load_catalog(catalog_path)
        print(f"-> Success: Loaded {len(products)} products.")
    except Exception as e:
        print(f"-> ERROR: Failed to load catalog: {e}")
        sys.exit(1)

    # 2 & 3 & 4 & 5. Perform Recommendation Flow
    user_prefs = {
        "preferred_tags": ["Coding", "Premium", "Everyday"],
        "preferred_brand": "Apple",
        "preferred_category": "Electronics",
        "preferred_subcategory": "Smartphone",
        "budget": 80000.0,
        "filter_category": "Electronics",  # Hard filter
        "filter_max_price": 100000.0        # Hard filter
    }

    print("\n[Step 2-5] Generating top 5 recommendations with preferences:")
    print(f"   Preferences: {user_prefs}")
    recs = recommender.recommend_products(products, user_prefs, top_n=5)
    print(f"-> Success: Generated {len(recs)} recommendations.")

    # 6. Validations
    print("\n[Step 6] Validating Results...")
    
    # Validation 6.1: Results count
    assert len(recs) > 0, "Recommendations list is empty!"
    
    # Validation 6.2: Sorting order (descending by score)
    scores = [rec["score"] for rec in recs]
    print(f"   Calculated scores: {scores}")
    assert scores == sorted(scores, reverse=True), f"Results are not sorted descending: {scores}"
    print("   ✓ Validation Passed: Results are sorted descending.")

    # Validation 6.3: Scores are between 0 and 1
    for rec in recs:
        score = rec["score"]
        assert 0.0 <= score <= 1.0, f"Score {score} is out of bounds [0, 1] for product {rec['product']['name']}!"
    print("   ✓ Validation Passed: Scores are clamped between 0 and 1.")

    # Validation 6.4: Category filter works
    for rec in recs:
        category = rec["product"]["category"]
        assert category == "Electronics", f"Product {rec['product']['name']} has category {category}, expected 'Electronics'!"
    print("   ✓ Validation Passed: Category filter worked correctly.")

    # Validation 6.5: Budget filter works
    for rec in recs:
        price = rec["product"]["price"]
        assert price <= 100000.0, f"Product {rec['product']['name']} price {price} exceeds filter limit of 100000.0!"
    print("   ✓ Validation Passed: Budget filter worked correctly.")

    # Validation 6.6: No duplicate products
    product_ids = [rec["product"]["id"] for rec in recs]
    unique_ids = set(product_ids)
    assert len(product_ids) == len(unique_ids), f"Duplicate products detected! Product IDs: {product_ids}"
    print("   ✓ Validation Passed: No duplicate products in recommendations.")

    print("\n==================================================")
    print("Integration Test Passed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_integration_test()
