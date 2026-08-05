import os
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv, dotenv_values

# Load environment variables from the .env file
# Try loading from local directories as well for execution flexibility
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, ".."))
workspace_root = os.path.abspath(os.path.join(project_root, ".."))

# Resolve keys by inspecting all possible .env files and ignoring placeholders starting with 'YOUR_'
GOOGLE_API_KEY = None
GEMINI_API_KEY = None

env_paths = [
    os.path.join(project_root, ".env"),
    os.path.join(workspace_root, ".env"),
    os.path.join(os.getcwd(), ".env")
]

for path in env_paths:
    if os.path.exists(path):
        config = dotenv_values(path)
        g_key = config.get("GOOGLE_API_KEY")
        gem_key = config.get("GEMINI_API_KEY")
        
        if g_key and not g_key.startswith("YOUR_"):
            GOOGLE_API_KEY = g_key
        if gem_key and not gem_key.startswith("YOUR_"):
            GEMINI_API_KEY = gem_key

# Fallback to system environment if still not found
if not GOOGLE_API_KEY:
    g_key = os.environ.get("GOOGLE_API_KEY")
    if g_key and not g_key.startswith("YOUR_"):
        GOOGLE_API_KEY = g_key

if not GEMINI_API_KEY:
    gem_key = os.environ.get("GEMINI_API_KEY")
    if gem_key and not gem_key.startswith("YOUR_"):
        GEMINI_API_KEY = gem_key

# Also call load_dotenv to make sure other environment settings are available
load_dotenv()

class GeminiReasoner:
    """
    A reasoner class responsible for generating human-readable, tailored 
    suitability explanations for product recommendations using the Google GenAI SDK.
    """
    def __init__(self):
        # Read API key prioritizing GOOGLE_API_KEY, falling back to GEMINI_API_KEY
        self.api_key = GOOGLE_API_KEY or GEMINI_API_KEY

        # Initialize the GenAI Client with 10 seconds timeout and maximum 2 retries (total 3 attempts)
        if self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=10_000,  # 10,000 milliseconds = 10 seconds
                        retry_options=types.HttpRetryOptions(attempts=3)
                    )
                )
            except Exception:
                self.client = None
        else:
            self.client = None

    def generate_explanation(
        self,
        user_preferences: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> str:
        """
        Generates a concise suitability explanation for a single product recommendation.

        Args:
            recommendation: Dictionary representing the product recommendation containing:
                - product: Dictionary with name, category, brand, price, rating, tags.
                - score: Float representing the recommendation score.
                - score_breakdown: Dictionary showing individual scoring component matches.
            user_preferences: Dictionary containing the user's search and brand preferences.

        Returns:
            A string containing the explanation, or a fallback message if generation fails.
        """
        if not self.client:
            return "AI explanation is currently unavailable."

        try:
            product = recommendation.get("product", {})
            score = recommendation.get("score", 0.0)
            breakdown = recommendation.get("score_breakdown", {})

            # Format details for prompt inclusion
            user_details = f"""
- Preferred Category: {user_preferences.get('preferred_category', 'N/A')}
- Preferred Subcategory: {user_preferences.get('preferred_subcategory', 'N/A')}
- Preferred Brand: {user_preferences.get('preferred_brand', 'N/A')}
- Preferred Tags: {', '.join(user_preferences.get('preferred_tags', [])) if user_preferences.get('preferred_tags') else 'None'}
- Budget Limit: {user_preferences.get('budget', 'N/A')}
"""

            product_details = f"""
- Product Name: {product.get('name', 'N/A')}
- Brand: {product.get('brand', 'N/A')}
- Category: {product.get('category', 'N/A')}
- Subcategory: {product.get('subcategory', 'N/A')}
- Price: {product.get('price', 'N/A')}
- Rating: {product.get('rating', 'N/A')}/5.0
- Tags: {', '.join(product.get('tags', [])) if product.get('tags') else 'None'}
"""

            # Formatting breakdown details
            b_tag = breakdown.get("tag_similarity", {}).get("raw", 0.0)
            b_budget = breakdown.get("budget_match", {}).get("raw", 0.0)
            b_brand = breakdown.get("brand_match", {}).get("raw", 0.0)
            b_rating = breakdown.get("product_rating", {}).get("raw", 0.0)
            b_catsub = breakdown.get("category_subcategory", {}).get("raw", 0.0)
            budget_expl = breakdown.get("budget_match", {}).get("explanation", "N/A")

            score_details = f"""
- Overall Score: {score * 100:.1f}%
- Breakdown:
  * Tag Similarity: {b_tag * 100:.1f}%
  * Budget Match: {b_budget * 100:.1f}% ({budget_expl})
  * Brand Match: {b_brand * 100:.1f}%
  * Product Rating: {b_rating:.1f}/5.0
  * Category/Subcategory Match: {b_catsub * 100:.1f}%
"""

            prompt = f"""
User Preferences:
{user_details}

Recommended Product Details:
{product_details}

Recommendation Scores:
{score_details}

Please explain why this product matches the user's preferences.
"""

            # Configure system instructions as requested
            system_instruction = """You are a shopping assistant.
DO NOT recommend different products.
DO NOT invent specifications.
ONLY explain why THIS product matches the user's preferences.
Limit the response to 3–5 bullet points.
Mention:
• Budget fit
• Category fit
• Tag match
• Brand preference (if applicable)
• Rating
Do not hallucinate."""

            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )

            if response.text:
                return response.text.strip()
            else:
                return "AI explanation is currently unavailable."

        except Exception:
            # Robust exception handling: never raise exceptions to Streamlit UI
            return "AI explanation is currently unavailable."

    def generate_batch_explanations(
        self,
        user_preferences: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Iterates over a list of product recommendations to generate a list of explanation mappings.

        Args:
            user_preferences: User preferences dictionary.
            recommendations: List of recommendation dictionaries.

        Returns:
            A list of dictionaries matching:
            [
                {
                    "product_name": "...",
                    "explanation": "..."
                }
            ]
        """
        results = []
        for rec in recommendations:
            prod = rec.get("product", {})
            name = prod.get("name", "Unknown Product")
            explanation = self.generate_explanation(user_preferences, rec)
            results.append({
                "product_name": name,
                "explanation": explanation
            })
        return results

if __name__ == "__main__":
    # Demo code showing one recommendation being explained
    print("Initializing GeminiReasoner...")
    reasoner = GeminiReasoner()

    # Mock user preferences
    demo_prefs = {
        "preferred_tags": ["Coding", "Premium", "Everyday"],
        "preferred_brand": "Apple",
        "preferred_category": "Electronics",
        "preferred_subcategory": "Smartphone",
        "budget": 80000.0
    }

    # Mock recommendation object
    demo_rec = {
        "product": {
            "id": 3,
            "name": "iPhone 15",
            "category": "Electronics",
            "subcategory": "Smartphone",
            "brand": "Apple",
            "price": 79000.0,
            "rating": 4.7,
            "tags": ["Photography", "Premium", "Everyday"]
        },
        "score": 0.746,
        "score_breakdown": {
            "tag_similarity": {"raw": 0.613, "weighted": 0.245},
            "budget_match": {"raw": 1.0, "weighted": 0.25, "explanation": "Within budget (full score)."},
            "brand_match": {"raw": 1.0, "weighted": 0.15},
            "product_rating": {"raw": 4.7, "normalized": 0.94, "weighted": 0.094},
            "category_subcategory": {"raw": 1.0, "weighted": 0.10}
        }
    }

    print("\nGenerating suitability explanation for product: iPhone 15...")
    explanation_text = reasoner.generate_explanation(demo_prefs, demo_rec)
    print("\nExplanation Output:\n")
    print(explanation_text)
