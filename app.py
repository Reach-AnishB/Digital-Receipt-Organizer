from flask import Flask, request, jsonify
import pytesseract
import cv2
import os
import json
import re
import logging
from pdf2image import convert_from_path
from PIL import Image
import openai

# Configure logging
logging.basicConfig(filename="server.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# OpenAI API Key
openai.api_key = "your_openai_api_key"

# JSON file for storing receipts
DATA_FILE = "receipts.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# Function to extract text using OCR
def extract_text_from_image(image_path):
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config="--psm 6")
        return text
    except Exception as e:
        logging.error(f"OCR error: {str(e)}")
        return ""

# Extract receipt details using regex and AI
def parse_receipt_text(text):
    store = "Unknown Store"
    date = "Unknown Date"
    amount = 0.0
    category = "Food"

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    if lines:
        store = lines[0]  # First non-empty line as store name

    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
    if date_match:
        date = date_match.group(0)

    amount_match = re.search(r'(\$\d+(\.\d{2})?)|(\d+\.\d{2})', text)
    if amount_match:
        amount = float(amount_match.group(0).replace("$", ""))

    category_keywords = {
        "Food": ["hotel", "restaurant", "cafe", "dining"],
        "Shopping": ["supermarket", "clothes", "mall", "store"],
        "Fees": ["fee", "registration", "tuition", "charges"],
        "Bills": ["electricity", "water bill", "gas", "internet"],
        "Groceries": ["grocery", "vegetables", "fruits", "market"]
    }

    text_lower = text.lower()

    for cat, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            category = cat
            break

    return store, date, amount, category

# Save receipt data to JSON
def save_receipt_data(store, date, amount, category):
    with open(DATA_FILE, "r") as f:
        receipts = json.load(f)

    receipts.append({"store": store, "date": date, "amount": amount, "category": category})

    with open(DATA_FILE, "w") as f:
        json.dump(receipts, f, indent=4)

# Receipt Upload API
@app.route('/upload', methods=['POST'])
def upload_receipt():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = file.filename
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", filename)
    file.save(file_path)

    try:
        if filename.lower().endswith(".pdf"):
            images = convert_from_path(file_path)
            image_path = file_path.replace(".pdf", ".png")
            images[0].save(image_path, "PNG")
        else:
            image_path = file_path

        extracted_text = extract_text_from_image(image_path)
        store, date, amount, category = parse_receipt_text(extracted_text)

        save_receipt_data(store, date, amount, category)

        return jsonify({"message": "Receipt uploaded successfully", "store": store, "date": date, "amount": amount, "category": category})
    
    except Exception as e:
        logging.error(f"Error processing receipt: {str(e)}")
        return jsonify({"error": "Error processing receipt, check logs"}), 500

# Get Receipts API
@app.route('/receipts', methods=['GET'])
def get_receipts():
    with open(DATA_FILE, "r") as f:
        receipts = json.load(f)
    return jsonify(receipts)

# Delete Receipt API
@app.route('/delete_receipt', methods=['POST'])
def delete_receipt():
    data = request.json
    with open(DATA_FILE, "r") as f:
        receipts = json.load(f)

    updated_receipts = [r for r in receipts if not (r["store"] == data["store"] and r["date"] == data["date"] and r["amount"] == data["amount"])]

    with open(DATA_FILE, "w") as f:
        json.dump(updated_receipts, f, indent=4)

    return jsonify({"message": "Receipt deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
