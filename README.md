# Product Recommendation Agent

A Gemini-powered recommendation system that matches products from a catalog with users based on their preferences, demographics, and transaction history.

## Project Structure

- `app.py`: Main entry point (Streamlit application).
- `products.json`: Product catalog data.
- `users.json`: User profile and transaction data.
- `recommender.py`: Recommender core logic.
- `gemini.py`: Integration with Gemini APIs.
- `utils.py`: Utility functions for data handling.
- `requirements.txt`: Python package requirements.

## Setup & Running

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
