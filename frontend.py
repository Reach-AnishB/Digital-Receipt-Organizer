import streamlit as st
import requests
import pandas as pd
from ai_chatbox import chatbot_response  # Import AI Chatbot

# Flask API Endpoint
API_URL = "http://127.0.0.1:5000"

# Set Streamlit Page Layout
st.set_page_config(page_title="Digital Receipt Organizer", layout="wide")

# 🔹 **LEFT SIDEBAR - AI Chatbox**
with st.sidebar:
    st.title("🤖 Chat with Assistant")
    user_query = st.text_input("Ask me anything...")

    if user_query:
        response_text = chatbot_response(user_query)  # Call AI chatbot
        st.write("🤖:", response_text)

# 🔹 **RIGHT MAIN SECTION - Upload & Receipt History**
st.title("📑 Digital Receipt Organizer")

# Receipt Upload Section
st.subheader("Upload a Receipt 📤")
uploaded_file = st.file_uploader("Upload an image or PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    response = requests.post(f"{API_URL}/upload", files=files)

    if response.status_code == 200:
        st.success("✅ Receipt uploaded successfully!")
        receipt_data = response.json()
        st.json(receipt_data)
    else:
        st.error("❌ Error processing receipt.")

# Display Receipt History
st.subheader("📋 Receipt History")
response = requests.get(f"{API_URL}/receipts")

if response.status_code == 200:
    receipts = response.json()
    if receipts:
        df = pd.DataFrame(receipts)

        # Show receipt table with delete buttons
        for i, row in df.iterrows():
            cols = st.columns([5, 2, 2, 2, 2, 1])  # Layout for columns
            cols[0].write(row["store"])
            cols[1].write(row["date"])
            cols[2].write(f"${row['amount']:.2f}")
            cols[3].write(row["category"])

            # Delete Button
            if cols[4].button("🗑 Delete", key=i):
                delete_data = {"store": row["store"], "date": row["date"], "amount": row["amount"]}
                delete_response = requests.post(f"{API_URL}/delete_receipt", json=delete_data)

                if delete_response.status_code == 200:
                    st.success("✅ Receipt deleted successfully!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Failed to delete receipt.")
else:
    st.error("❌ Could not retrieve receipts.")
