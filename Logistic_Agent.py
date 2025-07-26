import pandas as pd
import requests
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from flask import Flask, request, jsonify

app = Flask(__name__)


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


def get_product_transfer(product_details):
    import pandas as pd

    inventory_data = pd.read_csv(
        r"C:\Users\NIRMALSJ\OneDrive - Capgemini\Attachments\Desktop\Path For Future\Hackathon\Agents\Logistic Agent Dataset\Inventory data.csv"
    )
    inventory_json = inventory_data.to_dict(orient="records")
    logistic_Input = []

    for item in product_details:
        matched = False
        if item.get("transfer_label") == 1:
            for inv_item in inventory_json:
                if (
                    inv_item.get("Product Name", "").strip().lower() == item.get("Product Name", "").strip().lower()
                    and inv_item.get("Store ID") != item.get("Store ID")
                    and inv_item.get("risk") == 0
                ):
                    enriched = {
                        "Product ID": item["Product ID"],
                        "From Store": item["Store ID"],
                        "To Store": inv_item["Store ID"],
                        "Transfer Qty": item["Stock Qty"],
                        "Transfer Cost": item["New Price"] * item["Stock Qty"],
                        "Product Name": item["Product Name"],
                        "sales_velocity": item["sales_velocity"],
                        "day_to_expiry": item["day_to_expiry"],
                        "New Price": item["New Price"],
                        "Markdown": item["Markdown"],
                        "risk": item["risk"]
                    }
                    logistic_Input.append(enriched)
                    matched = True
                    break

            if not matched:
                print(f" No valid transfer target found for product {item['Product Name']} from store {item['Store ID']}")
                logistic_Input.append({
                    "Product ID": item["Product ID"],
                    "From Store": item["Store ID"],
                    "To Store": None,
                    "Transfer Qty": 0,
                    "Transfer Cost": 0,
                    "Product Name": item["Product Name"],
                    "sales_velocity": item["sales_velocity"],
                    "day_to_expiry": item["day_to_expiry"],
                    "New Price": item["New Price"],
                    "Markdown": item["Markdown"],
                    "risk": item["risk"],
                    "Message": f"No eligible store found for transfer of {item['Product Name']}"
                })


    return logistic_Input

        
def train_model():
    inventory_data = pd.read_csv(r"C:\Users\NIRMALSJ\OneDrive - Capgemini\Attachments\Desktop\Path For Future\Hackathon\Agents\Logistic Agent Dataset\Inventory data.csv")
    inventory_data['transfer_label'] = ((inventory_data['risk'] == 1) & (inventory_data['Stock Qty']>10)).astype(int)
    features = ['Stock Qty', 'sales_velocity', 'day_to_expiry', 'risk']
    target ="transfer_label"
    x=inventory_data[features]
    y=inventory_data[target]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)
    return model

model = train_model()

@app.route('/logistic', methods=['POST'])
def logistic():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    markdown_data = get_risk_PricingAgent_details(data)
    #print("Columns in markdown_data:", markdown_data)
    input_df = pd.DataFrame(markdown_data)
    #print("Columns in input_df:", input_df.columns.tolist())
    features = ['Stock Qty', 'sales_velocity', 'day_to_expiry', 'risk']
    #print("Features used for prediction:", features)
    input_df["transfer_label"] = model.predict(input_df[features])
    transfer_label_data = input_df.to_dict(orient="records")
    #print("Transfer label data:", transfer_label_data)
    product_transfer = get_product_transfer(transfer_label_data)
    #print("Product transfer data:", product_transfer)
    return jsonify(product_transfer)


if __name__=='__main__':
    app.run(port=5002, debug=True)
