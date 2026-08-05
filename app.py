import os
import sys
import json
import streamlit as st

# Add current directory to path to ensure modules are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import loader, recommender

# Dynamic import of GeminiReasoner
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
    layout="centered"  # Centered layout as requested
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

/* Gradient Title */
.title-gradient {
    background: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
    letter-spacing: -0.025em;
    text-align: center;
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    text-align: center;
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

.divider {
    text-align: center;
    margin: 2.5rem 0;
    font-weight: bold;
    color: #4b5563;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# Main Title Headers
st.markdown('<div class="title-gradient">Product Recommendation Agent</div>', unsafe_allow_html=True)


# Resolve local paths
base_dir = os.path.dirname(os.path.abspath(__file__))
catalog_path = os.path.join(base_dir, "catalog.json")
sample_users_path = os.path.join(base_dir, "sample_users.json")

# 1. Load Catalog & Sample Users
try:
    products = loader.load_catalog(catalog_path)
except Exception as e:
    st.error(f"Failed to load catalog data from {catalog_path}: {e}")
    st.stop()

sample_users = []
if os.path.exists(sample_users_path):
    try:
        with open(sample_users_path, "r", encoding="utf-8") as f:
            sample_users = json.load(f)
    except Exception as e:
        st.warning(f"Failed to load sample users: {e}")

# Pre-populate categories, brands, and tags list
categories = loader.get_categories(products)
brands = loader.get_brands(products)
all_tags = sorted(list(set(tag for p in products for tag in p.get("tags", []))))
max_price = max(p["price"] for p in products)

# Initialize Session State values for widgets if not already present
if "pref_category" not in st.session_state:
    st.session_state.pref_category = categories[0]
if "pref_subcategory" not in st.session_state:
    st.session_state.pref_subcategory = "All Subcategories"
if "pref_brand" not in st.session_state:
    st.session_state.pref_brand = "All Brands"
if "pref_budget" not in st.session_state:
    st.session_state.pref_budget = int(max_price / 2)
if "pref_tags" not in st.session_state:
    st.session_state.pref_tags = []
if "nlp_prompt" not in st.session_state:
    st.session_state.nlp_prompt = ""

# Show API status warn
if reasoner is None or (reasoner.client is None and reasoner.groq_client is None):
    st.warning("⚠️ Gemini/Groq API is not configured. Please add GOOGLE_API_KEY or GROQ_API_KEY to your `.env` file in the root directory to enable AI preferences extraction and explanations.")

# ======================================================
# FEATURE 1 — Natural Language Shopping Assistant
# ======================================================
st.markdown("### Describe what you're looking for")
nlp_input = st.text_area(
    "Type your requirements in plain English:",
    value=st.session_state.nlp_prompt,
    placeholder="I'm looking for a lightweight laptop under ₹80,000 for coding and college.",
    height=100,
    key="nlp_textarea_key"
)

if st.button("✨ AI Understand My Needs"):
    if nlp_input.strip():
        if reasoner is not None and (reasoner.client is not None or reasoner.groq_client is not None):
            with st.spinner("🤖 Extracting preferences..."):
                extracted = reasoner.extract_preferences(nlp_input)
                
                # Apply extracted category if valid
                if extracted.get("category") in categories:
                    st.session_state.pref_category = extracted["category"]
                    
                    # Apply subcategory if valid for that category
                    valid_subs = loader.get_subcategories(products, extracted["category"])
                    if extracted.get("subcategory") in valid_subs:
                        st.session_state.pref_subcategory = extracted["subcategory"]
                    else:
                        st.session_state.pref_subcategory = "All Subcategories"
                
                # Apply brand if valid
                if extracted.get("preferred_brand") in brands:
                    st.session_state.pref_brand = extracted["preferred_brand"]
                else:
                    st.session_state.pref_brand = "All Brands"
                
                # Apply budget
                if extracted.get("budget") is not None:
                    st.session_state.pref_budget = int(extracted["budget"])
                
                # Apply tags
                if extracted.get("preferred_tags"):
                    st.session_state.pref_tags = [t for t in extracted["preferred_tags"] if t in all_tags]
                
                st.session_state.nlp_prompt = nlp_input
                st.success("AI successfully extracted your preferences and filled out the form below!")
                st.rerun()
        else:
            st.error("Gemini Reasoner is unavailable. Check API keys.")
    else:
        st.warning("Please describe what you are looking for first.")



# ======================================================
# FEATURES 2 & 3 — Sample Users (Demo Mode)
# ======================================================
st.markdown("### Try a Sample User")
selected_sample = st.selectbox(
    "Select Sample User Profile:",
    options=["Custom Search"] + [f"{u['name']} ({u['description']})" for u in sample_users]
)

# Load selected sample user into state
if "last_selected_sample" not in st.session_state:
    st.session_state.last_selected_sample = "Custom Search"

if selected_sample != st.session_state.last_selected_sample:
    st.session_state.last_selected_sample = selected_sample
    if selected_sample != "Custom Search":
        user_name = selected_sample.split(" (")[0]
        user = next(u for u in sample_users if u["name"] == user_name)
        prefs = user["preferences"]
        
        if prefs.get("category") in categories:
            st.session_state.pref_category = prefs["category"]
        if prefs.get("subcategory"):
            st.session_state.pref_subcategory = prefs["subcategory"]
        else:
            st.session_state.pref_subcategory = "All Subcategories"
        if prefs.get("preferred_brand") in brands:
            st.session_state.pref_brand = prefs["preferred_brand"]
        else:
            st.session_state.pref_brand = "All Brands"
        if prefs.get("budget") is not None:
            st.session_state.pref_budget = int(prefs["budget"])
        if prefs.get("preferred_tags"):
            st.session_state.pref_tags = [t for t in prefs["preferred_tags"] if t in all_tags]
        st.rerun()

st.markdown("<br/>", unsafe_allow_html=True)

# ======================================================
# FEATURES 4 & 5 — Recommendation Form & Cards
# ======================================================
st.markdown("### Customize Your Search Details")
with st.form("recommendation_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Category Selector
        cat_index = categories.index(st.session_state.pref_category) if st.session_state.pref_category in categories else 0
        form_category = st.selectbox("Category", options=categories, index=cat_index)
        
        # Subcategory Selector (Dynamic list for selected Category)
        valid_subs = loader.get_subcategories(products, form_category)
        subcategory_options = ["All Subcategories"] + valid_subs
        sub_index = subcategory_options.index(st.session_state.pref_subcategory) if st.session_state.pref_subcategory in subcategory_options else 0
        form_subcategory = st.selectbox("Subcategory (Optional)", options=subcategory_options, index=sub_index)
        
        # Brand Selector
        brand_options = ["All Brands"] + brands
        brand_index = brand_options.index(st.session_state.pref_brand) if st.session_state.pref_brand in brand_options else 0
        form_brand = st.selectbox("Brand (Optional)", options=brand_options, index=brand_index)
        
    with col2:
        # Budget Input
        form_budget = st.number_input(
            "Max Budget (INR)",
            min_value=0,
            value=st.session_state.pref_budget,
            step=500
        )
        
        # Tags Multiselect
        form_tags = st.multiselect("Preferred Tags", options=all_tags, default=st.session_state.pref_tags)
        
    submit_btn = st.form_submit_button("Recommend Products")

if submit_btn:
    st.session_state.pref_category = form_category
    st.session_state.pref_subcategory = form_subcategory
    st.session_state.pref_brand = form_brand
    st.session_state.pref_budget = form_budget
    st.session_state.pref_tags = form_tags

# Fetch recommendations based on current state values
user_prefs = {
    "preferred_tags": st.session_state.pref_tags,
    "preferred_brand": st.session_state.pref_brand if st.session_state.pref_brand != "All Brands" else "",
    "preferred_category": st.session_state.pref_category,
    "preferred_subcategory": st.session_state.pref_subcategory if st.session_state.pref_subcategory != "All Subcategories" else "",
    "budget": float(st.session_state.pref_budget),
    # Map filters strictly
    "filter_category": st.session_state.pref_category,
    "filter_max_price": float(st.session_state.pref_budget)
}

if st.session_state.pref_brand != "All Brands":
    user_prefs["filter_brand"] = st.session_state.pref_brand

if st.session_state.pref_subcategory != "All Subcategories":
    user_prefs["filter_subcategory"] = st.session_state.pref_subcategory

# Execute recommendation logic from engine
recs = recommender.recommend_products(products, user_prefs, top_n=5)

# Display recommendations
st.markdown("### Recommendations Results")
if not recs:
    st.info("No products match the selected filters. Try adjusting your parameters above.")
else:
    for idx, rec in enumerate(recs):
        prod = rec["product"]
        score = rec["score"]
        breakdown = rec["score_breakdown"]

        # Product card representation
        st.markdown(f"""
        <div class="product-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0px;">
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
        </div>
        """, unsafe_allow_html=True)

        # AI Suitability Explanation Button
        if st.button("✨ Generate AI Suitability Explanation", key=f"ai_btn_{prod['id']}"):
            if reasoner is not None and (reasoner.client is not None or reasoner.groq_client is not None):
                with st.spinner("🤖 Consulting Gemini for suitability reasoning..."):
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
                st.info("ℹ️ AI explanation is currently unavailable. Please check GOOGLE_API_KEY or GROQ_API_KEY environment variable.")
