# Predefined demo query cache to bypass LLM calls during presentations
# Maps exact user queries to structured preference dictionaries matching catalog taxonomy.

DEMO_CACHE = {
    "I'm looking for headphones under ₹20,000 for travelling. Noise cancellation is important, and I'd prefer Sony or JBL.": {
        "category": "Electronics",
        "subcategory": "Headphones",
        "budget": 20000,
        "preferred_brand": "Sony",
        "preferred_tags": [
            "Travel",
            "Noise Cancelling"
        ]
    },
    "I'm a computer science student looking for a lightweight laptop under ₹75,000 for programming and machine learning. Good battery life is important.": {
        "category": "Electronics",
        "subcategory": "Laptop",
        "budget": 75000,
        "preferred_brand": None,
        "preferred_tags": [
            "Coding",
            "Students",
            "Lightweight",
            "Battery"
        ]
    },
    "I need comfortable running shoes under ₹5,000 for daily jogging with good grip and cushioning.": {
        "category": "Fashion",
        "subcategory": "Running Shoes",
        "budget": 5000,
        "preferred_brand": None,
        "preferred_tags": [
            "Running",
            "Comfort",
            "Sports"
        ]
    }
}
