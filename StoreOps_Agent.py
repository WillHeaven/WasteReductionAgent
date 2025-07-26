from flask import Flask, request, jsonify
import requests
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

def store_ops_decision_llm(item):
    prompt = (
        f"You are a store operations assistant. Based on the following product data, "
        f"decide the most appropriate store action to reduce spoilage or improve sales.\n\n"
        f"Product Details:\n"
        f"- Product Name: {item['Product Name']}\n"
        f"- Stock Quantity: {item['Stock Qty']}\n"
        f"- Days to Expiry: {item['day_to_expiry']}\n"
        f"- Sales Velocity: {item['sales_velocity']}\n"
        f"- Markdown: {item['Markdown']}\n"
        f"- Risk: {item['risk']}\n\n"
        f"Generate:\n"
        f"1. Action to be taken as Move to end-cap, Alert staff for sampling, Reorder shelf placement, Alert for manual markdown\n"
        f"2. Reason for the action\n"
        f"3. According to the action set it as for Worker or Manager. if it is align with internal work set it for Manager. if it is align for external work set is for Worker\n"
        f"Respond in JSON format with keys: action, reason, assigned."
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
            "max_tokens": 300,
            "temperature": 0.5,
            "top_p": 0.8
        })
    )

    result = json.loads(response['body'].read())

    content = result.get("content", "")
    if isinstance(content, list):
        content_text = ''.join([msg.get("text", "") for msg in content])
    elif isinstance(content, str):
        content_text = content
    else:
        content_text = str(content)

    try:
        return json.loads(content_text)
    except json.JSONDecodeError:
        print("Failed to parse LLM response:", content_text)
        return {
            "action": None,
            "reason": "LLM response could not be parsed",
            "assigned": "Manager"
        }


def get_risk_PricingAgent_details(product_details):
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
    logistic_Input=[]
    for i, item in enumerate(pricingAgent_op):
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
            logistic_Input.append(enriched)
    return logistic_Input
    
def generate_store_ops_actions(data):
    actions = []

    for item in data:
        decision = store_ops_decision_llm(item)
        if decision["action"]:
            actions.append({
                "Store ID": item["Store ID"],
                "Product ID": item["Product ID"],
                "Product Name": item["Product Name"],
                "Action": decision["action"],
                "Reason": decision["reason"],
                "Assigned To": decision["assigned"],
                "Due Time": "End of Day",
                "Status": "Pending"
            })

    return actions

@app.route('/storeOpsAgent', methods=['POST'])
def store_ops_agent():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    PricingAgent_data = get_risk_PricingAgent_details(data)
    actions = generate_store_ops_actions(PricingAgent_data)
    return jsonify(actions)

if __name__ == '__main__':
    app.run(port=5003, debug=True)
