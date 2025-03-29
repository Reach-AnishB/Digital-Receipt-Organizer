import requests

API_URL = "http://127.0.0.1:5000"

def chatbot_response(user_query):
    user_query = user_query.lower()  # Convert query to lowercase for case insensitivity

    # Fetch receipt data from backend
    response = requests.get(f"{API_URL}/receipts")

    if response.status_code != 200:
        return "❌ Could not retrieve receipt data."

    receipts = response.json()

    # Initialize spending amounts
    category_spending = {
        "food": 0,
        "shopping": 0,
        "fees": 0
    }

    # Calculate total spending per category
    for receipt in receipts:
        category = receipt["category"].lower()
        amount = float(receipt["amount"])

        if category in category_spending:
            category_spending[category] += amount
        else:
            category_spending["food"] += amount  # Default unknown to Food

    # Handle different user questions
    if "food expense" in user_query:
        return f"🍽️ Your total food expense is **${category_spending['food']:.2f}**."
    elif "shopping expense" in user_query:
        return f"🛍️ Your total shopping expense is **${category_spending['shopping']:.2f}**."
    elif "fees expense" in user_query or "registration" in user_query:
        return f"🏫 Your total fees expense is **${category_spending['fees']:.2f}**."
    elif "total expense" in user_query:
        total = sum(category_spending.values())
        return f"💰 Your total expense across all categories is **${total:.2f}**."
    else:
        return "🤖 I couldn't understand that. Try asking about food, shopping, fees, or total expenses."
