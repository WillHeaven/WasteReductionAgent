
from flask import Flask, request, jsonify
import requests
import pandas as pd
import boto3
import json

app = Flask(__name__)

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",  
    aws_access_key_id="Your Access key id",
    aws_secret_access_key="Your Secret Key",
    aws_session_token="Your Session Token"
)


def generate_rationale(product_name, days_to_expiry, sales_velocity, stock_qty, markdown):
    prompt = (
        f"The product '{product_name}' is nearing expiry in {days_to_expiry} days, "
        f"with a sales velocity of {sales_velocity:.2f} units/day and a stock of {stock_qty} units. "
        f"A {int(markdown * 100)}% markdown is being considered. "
        f"Write a short, business-style explanation of why this markdown is a good idea to reduce waste and preserve margin. "
        f"Do not include any calculations or steps."
    )

    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.5,
            "top_p": 0.8
        })
    )

    result = json.loads(response['body'].read())
    return result['content']


def get_spoilage_data(product_details):
    try:
        response = requests.post(
            "http://localhost:6000/tools/predictSpoilage", json={"products": product_details})
        response.raise_for_status()
        spoilage_result = response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh} - {response.text}")
        return []
    except requests.exceptions.RequestException as err:
        print(f"Request Error: {err}")
        return []

    pricing_input = []
    for i, item in enumerate(spoilage_result):
        enriched = {
            "Product ID": item["Product ID"],
            "Store ID": item["Store ID"],
            "day_to_expiry": item["day_to_expiry"],
            "predicted_risk": item["predicted_risk"],
            "sales_velocity": item["sales_velocity"],
            "Stock Qty": product_details[i].get("Stock Qty", 0),
            "Price": product_details[i].get("Price", 100),
            "Product Name": product_details[i].get("Product Name", "Unknown")
        }
        pricing_input.append(enriched)

    return pricing_input

def markdown(item):
    productId = item["Product ID"]
    productName = item["Product Name"]
    storeId = item["Store ID"]
    price = item["Price"]
    risk = item["predicted_risk"]
    days_to_expiry = item["day_to_expiry"]
    sales_velocity = item["sales_velocity"]

    if risk == 1:
        if days_to_expiry <= 1:
            markdown = 0.5
        elif days_to_expiry <= 2:
            markdown = 0.3
        elif sales_velocity < 0.2:
            markdown = 0.2
        else:
            markdown = 0.1
    else:
        markdown = 0.0

    recommended_price = price * (1 - markdown)
    #rationale = generate_rationale(productId, days_to_expiry, sales_velocity, item["Stock Qty"], markdown)

    return {
        "Product ID": productId,
        "Product Name": productName,
        "Store ID": storeId,
        "Markdown": f"{int(markdown * 100)}%",
        "Old Price": price,
        "New Price": round(recommended_price, 2),
        "risk": risk,
        "Stock Qty": item["Stock Qty"],
        "sales_velocity": sales_velocity,
        "day_to_expiry": days_to_expiry
        #"Rationale": rationale
    }

#recommendations_markdown = [markdown(item) for item in pricing_input]
#for record in recommendations_markdown:
   # print(record)

@app.route('/pricingAgent', methods=['POST'])
def pricing_agent():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    spoilage_data = get_spoilage_data(data)
    results = [markdown(item) for item in spoilage_data]
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
