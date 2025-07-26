from flask import Flask, request, jsonify
import requests
import boto3
import json

app = Flask(__name__)
print("Flask app is starting...")


bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",  
    aws_access_key_id="Your Access key id",
    aws_secret_access_key="Your Secret Key",
    aws_session_token="Your Session Token"
)

sns_runtime = boto3.client(
    "sns",
    region_name="us-east-1",  
    aws_access_key_id="Your Access key id",
    aws_secret_access_key="Your Secret Key",
    aws_session_token="Your Session Token"
)


def sendNotification(message, topic_arn):
    try:
        response = sns_runtime.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject="Product Expiry Notification"
        )
        print(f"Notification sent successfully: {response}")
        return response
    except Exception as e:
        print(f"Error sending notification: {e}")
        return None


def customer_message(product_name, days_to_expiry, markdown):
    prompt = (
        f"The product '{product_name}' is expiring in {days_to_expiry} days and has a {markdown} discount. "
        f"Generate:\n"
        f"1. A short app notification (max 20 words) to encourage purchase.\n"
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


def PricingAgent_details(product_details):
    try:
        response = requests.post(
            "http://localhost:6000/tools/pricingAgent", json={"products": product_details}
        )
        pricingAgent_op = response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh} - {response.text}")
        return []
    except requests.exceptions.RequestException as err:
        print(f"Request Error: {err}")
        return []

    PricingAgent_Op = []
    for item in pricingAgent_op:
        if item["risk"] == 1:
            enriched = {
                "Product ID": item["Product ID"],
                "Store ID": item["Store ID"],
                "Product Name": item["Product Name"],
                "Stock Qty": item["Stock Qty"],
                "sales_velocity": item["sales_velocity"],
                "day_to_expiry": item["day_to_expiry"],
                "New Price": item["New Price"],
                "Markdown": item["Markdown"],
                "risk": item["risk"],
            }
            PricingAgent_Op.append(enriched)
    return PricingAgent_Op


def tradeOff_score(risk, stock_qty, markdown, labour_cost):
    markdown_percentage = int(markdown.replace('%', '')) / 100 if markdown else 0
    score = (risk * 0.5) + (stock_qty * 0.2) + (markdown_percentage * 0.2) + (labour_cost * 0.1)
    return round(score, 2)


def call_logistics_agent(data):
    try:
        response = requests.post("http://localhost:6000/tools/logistic", json={"products": data})
        return response.json()
    except Exception as e:
        print("Logistics Agent Error:", e)
        return []


def call_store_ops_agent(data):
    try:
        response = requests.post("http://localhost:6000/tools/storeOpsAgent", json={"products": data})
        return response.json()
    except Exception as e:
        print("Store Ops Agent Error:", e)
        return []


def extract_notification_text(notification_list):
    if isinstance(notification_list, list) and len(notification_list) > 0:
        return notification_list[0].get("text", "")
    return ""


@app.route('/CustomerEngagementAgent', methods=['POST'])
def CustomerEngagementAgent():
    data = request.get_json()
    #print("Received request data:", data)
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    PricingAgent_data = PricingAgent_details(data)
    logistics_data = call_logistics_agent(data)
    store_ops_data = call_store_ops_agent(data)

    enriched_output = []
    for item in PricingAgent_data:
        labour_cost = 1 if item["risk"] == 1 else 0
        product_name = item["Product Name"]
        days_to_expiry = item["day_to_expiry"]
        markdown = item["Markdown"]

        score = tradeOff_score(item["risk"], item["Stock Qty"], markdown, labour_cost)
        notification = customer_message(product_name, days_to_expiry, markdown)
        notification_text = extract_notification_text(notification)
        sendNotification(notification_text, "arn:aws:sns:us-east-1:486539985600:AgenticAiTopic")
        product_id = item["Product ID"]
        store_id = item["Store ID"]

        logistics_info = next(
            (l for l in logistics_data if l["Product ID"] == product_id and l.get("From Store", store_id) == store_id),
            {}
        )
        store_ops_info = next(
            (s for s in store_ops_data if s["Product ID"] == product_id and s["Store ID"] == store_id),
            {}
        )

        enriched_item = {
            "Product ID": product_id,
            "Store ID": store_id,
            "Product Name": product_name,
            "sales_velocity": item["sales_velocity"],
            "day_to_expiry": days_to_expiry,
            "New Price": item["New Price"],
            "Markdown": markdown,
            "risk": item["risk"],
            "Notification": notification,
            "Trade-Off Score": score,
            "Logistics Suggestion": logistics_info if isinstance(logistics_info, dict) else {},
            "Store Ops Action": store_ops_info if isinstance(store_ops_info, dict) else {}
        }

        enriched_output.append(enriched_item)

    return jsonify(enriched_output)


if __name__ == '__main__':
    app.run(port=5005, debug=True)
