from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

app = Flask(__name__)

def train_model():
	inventory = pd.read_csv(r"C:\Users\NIRMALSJ\OneDrive - Capgemini\Attachments\Desktop\Path For Future\Hackathon\Agents\simulated_inventory.csv", parse_dates=["Date","Expiry Date"], dayfirst=True)

	# print(inventory.info())
	# print(inventory.isnull().sum())
	# print(inventory.head())

	inventory['day_to_expiry'] = (inventory['Expiry Date']-inventory['Date']).dt.days
	inventory['sales_velocity'] = inventory['Daily Sales'] / inventory['Stock Qty'].replace(0,np.nan)

	#print(inventory[["Product ID", "Product Name", "Store ID", "Date", "Expiry Date", "day_to_expiry", "Daily Sales", "Stock Qty", "sales_velocity"]].head())

	inventory['risk'] = np.where((inventory['day_to_expiry']<=3) & (inventory['sales_velocity']<0.3),1,0)

	#print("\nFeature new Data:")
	#print(inventory[["Product ID", "Product Name", "Store ID", "Date", "Expiry Date","Category", "Weather", "day_to_expiry", "Daily Sales", "Stock Qty", "sales_velocity","risk"]].head())

	#Feature and target
	Feature = ["day_to_expiry","sales_velocity","Category","Weather"]
	Target ="risk"
	x=inventory[Feature]
	y=inventory[Target]

	#Preprocessing for categorical features
	categorical_features = ["Category","Weather"]
	numerical_features = ["day_to_expiry","sales_velocity"]

	preprocessor = ColumnTransformer(transformers = [("cat", OneHotEncoder(handle_unknown='ignore'), categorical_features)],
	remainder = "passthrough")

	#pipeline with regression
	pipeline= Pipeline( steps =[("preprocessor", preprocessor),("classifier", LogisticRegression(max_iter=1000))])

	#Splitting the data
	x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2, stratify=y, random_state=42)

	#training the model
	pipeline.fit(x_train, y_train)
	return  pipeline

model= train_model()

@app.route('/predictSpoilage', methods=['POST'])
def predictSpoilage():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    # Convert input data to DataFrame
    input_df = pd.DataFrame(data)
    input_df['day_to_expiry'] = (pd.to_datetime(input_df['Expiry Date']) - pd.to_datetime(input_df['Date'])).dt.days
    input_df['sales_velocity'] = input_df['Daily Sales'] / input_df['Stock Qty'].replace(0,np.nan)
    
    
    features = ["day_to_expiry", "sales_velocity", "Category", "Weather"]
    input_df["predicted_risk"] = model.predict(input_df[features])
    return jsonify(input_df[["Product ID", "Store ID","Stock Qty","Price", "day_to_expiry", "sales_velocity", "predicted_risk"]].to_dict(orient="records"))


if __name__=='__main__':
    app.run(debug=True)

#Evaluate the model
#y_pred = pipeline.predict(x_test)
#print("Model Accuracy:", accuracy_score(y_test, y_pred))
#print("\nClassification Report:\n", classification_report(y_test, y_pred))

#To simulate CSV File
#inventory.to_csv(r"C:\Users\NIRMALSJ\OneDrive - Capgemini\Attachments\Desktop\Path For Future\Hackathon\Agents\simulated_inventory_with_predictions.csv", index=False)
#print("\nPredictions saved to 'simulated_inventory_with_predictions.csv'.")