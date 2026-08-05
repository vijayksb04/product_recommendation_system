import os
import sys
import streamlit as st

# Add current directory to path to ensure modules are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import loader, recommender

# Dynamic import of GeminiReasoner from llm.gemini_reasoner
try:
    from llm.gemini_reasoner import GeminiReasoner
    reasoner = GeminiReasoner()
except ImportError:
    GeminiReasoner = None
    reasoner = None

# Set page config
st.set_page_config(
    page_title="Product Recommendation Agent",
    page_icon="🛍️",
    layout="wide"
)

# Inject CSS for premium UI styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

/* Global Font & Background overrides */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0d0f12;
    color: #e2e8f0;
}

[data-testid="stSidebar"] {
    background-color: #14171d;
    border-right: 1px solid #22252c;
}

/* Gradient Title */
.title-gradient {
    background: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
    letter-spacing: -0.025em;
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Glassmorphism Cards */
.product-card {
    background: rgba(30, 41, 59, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(8px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.product-card:hover {
    transform: translateY(-2px);
    border-color: rgba(99, 102, 241, 0.35);
    box-shadow: 0 12px 24px rgba(99, 102, 241, 0.1);
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}

.badge-brand {
    background-color: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

.badge-category {
    background-color: rgba(167, 139, 250, 0.15);
    color: #c084fc;
    border: 1px solid rgba(167, 139, 250, 0.2);
}

.badge-subcategory {
    background-color: rgba(236, 72, 153, 0.15);
    color: #f472b6;
    border: 1px solid rgba(236, 72, 153, 0.2);
}

.price-text {
    font-size: 1.4rem;
    font-weight: 700;
    color: #10b981;
}

.rating-text {
    font-size: 1rem;
    font-weight: 600;
    color: #fbbf24;
}

.score-text {
    font-weight: 700;
    color: #a855f7;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# Main Title Headers
st.markdown('<div class="title-gradient">Product Recommendation Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Hackathon Edition — Modular Recommendation Engine & Explainable Scorer</div>', unsafe_allow_html=True)

# Resolve local paths
base_dir = os.path.dirname(os.path.abspath(__file__))
catalog_path = os.path.join(base_dir, "catalog.json")

# 1. Load Catalog
try:
    products = loader.load_catalog(catalog_path)
except Exception as e:
    st.error(f"Failed to load catalog data from {catalog_path}: {e}")
    st.stop()

# 2. Build Sidebar Inputs
st.sidebar.markdown("### Search Preferences")

# Category Selection
categories = loader.get_categories(products)
selected_category = st.sidebar.selectbox("Category", options=categories)

# Subcategory Selection (Dynamic based on Category)
subcategories = ["All Subcategories"] + loader.get_subcategories(products, selected_category)
selected_subcategory = st.sidebar.selectbox("Subcategory (Optional)", options=subcategories)

# Brand Selection (Optional)
brands = ["All Brands"] + loader.get_brands(products)
selected_brand = st.sidebar.selectbox("Brand (Optional)", options=brands)

# Budget Constraint
max_price = max(p["price"] for p in products)
min_price = min(p["price"] for p in products)
budget = st.sidebar.number_input(
    "Max Budget (INR)",
    min_value=0,
    max_value=int(max_price * 2),
    value=int(max_price / 2),
    step=500
)

# Extract and build all unique tags for selection
all_tags = sorted(list(set(tag for p in products for tag in p.get("tags", []))))
selected_tags = st.sidebar.multiselect("Preferred Tags", options=all_tags)

# 3. Call recommend_products
user_prefs = {
    "preferred_tags": selected_tags,
    "preferred_brand": selected_brand if selected_brand != "All Brands" else "",
    "preferred_category": selected_category,
    "preferred_subcategory": selected_subcategory if selected_subcategory != "All Subcategories" else "",
    "budget": float(budget),
    # Map strict hard filters
    "filter_category": selected_category,
    "filter_max_price": float(budget)
}

if selected_brand != "All Brands":
    user_prefs["filter_brand"] = selected_brand

if selected_subcategory != "All Subcategories":
    user_prefs["filter_subcategory"] = selected_subcategory

recs = recommender.recommend_products(products, user_prefs, top_n=5)

# 4. Display Recommendations
st.markdown("### Top Recommendations")
if not recs:
    st.info("No products match the selected filters. Try broadening your category, brand, or budget.")
else:
    for idx, rec in enumerate(recs):
        prod = rec["product"]
        score = rec["score"]
        similarity = rec["similarity"]
        breakdown = rec["score_breakdown"]

        # Card container
        st.markdown(f"""
        <div class="product-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                <div>
                    <span class="badge badge-brand">{prod['brand']}</span>
                    <span class="badge badge-category">{prod['category']}</span>
                    <span class="badge badge-subcategory">{prod['subcategory']}</span>
                    <h3 style="margin: 5px 0 0 0; color: #f8fafc;">{idx + 1}. {prod['name']}</h3>
                </div>
                <div style="text-align: right;">
                    <div class="price-text">₹{prod['price']:,}</div>
                    <div class="rating-text">⭐ {prod['rating']}/5.0</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 15px;">
                <div style="flex-grow: 1;">
                    <span style="font-size: 0.85rem; color: #94a3b8;">Recommendation Score</span>
                    <div style="background-color: rgba(255,255,255,0.05); border-radius: 9999px; height: 10px; width: 100%;">
                        <div style="background: linear-gradient(90deg, #a855f7 0%, #3b82f6 100%); border-radius: 9999px; height: 10px; width: {score * 100}%;"></div>
                    </div>
                </div>
                <div class="score-text">{score * 100:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Expandable Score Breakdown
        with st.expander("🔍 Suitability Score Breakdown"):
            b_tag = breakdown["tag_similarity"]
            b_budget = breakdown["budget_match"]
            b_brand = breakdown["brand_match"]
            b_rating = breakdown["product_rating"]
            b_catsub = breakdown["category_subcategory"]

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Tag Match", f"{b_tag['raw'] * 100:.0f}%", f"+{(b_tag['weighted'] * 100):.1f}% Overall")
            col2.metric("Budget Match", f"{b_budget['raw'] * 100:.0f}%", f"+{(b_budget['weighted'] * 100):.1f}% Overall")
            col3.metric("Brand Match", f"{b_brand['raw'] * 100:.0f}%", f"+{(b_brand['weighted'] * 100):.1f}% Overall")
            col4.metric("Product Rating", f"{b_rating['raw']:.1f}/5.0", f"+{(b_rating['weighted'] * 100):.1f}% Overall")
            col5.metric("Category Match", f"{b_catsub['raw'] * 100:.0f}%", f"+{(b_catsub['weighted'] * 100):.1f}% Overall")
            st.caption(f"**Budget status**: {b_budget['explanation']}")

        # 5. AI Explanation Action Button
        # We must use unique keys since it's inside a loop
        if st.button("✨ Generate AI Suitability Explanation", key=f"ai_btn_{prod['id']}"):
            if reasoner is not None and reasoner.client is not None:
                with st.spinner("🤖 Consulting Gemini for personalized explanation..."):
                    try:
                        explanation = reasoner.generate_explanation(user_prefs, rec)
                        st.markdown(f"""
                        <div style="background-color: rgba(99, 102, 241, 0.1); border-left: 4px solid #6366f1; padding: 1rem; border-radius: 8px; margin-top: 10px;">
                            <strong>AI Suitability Explanation:</strong><br/><br/>
                            {explanation}
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as ex:
                        st.error(f"Error calling Gemini Reasoner: {ex}")
            else:
                st.info("ℹ️ AI explanation is currently unavailable. Please verify GOOGLE_API_KEY environment variable.")
