from fastapi import FastAPI
from pydantic import BaseModel, Field
import requests
from typing import List

app = FastAPI()

class productDetail(BaseModel):
    ProductID: str = Field(..., alias="Product ID")
    StoreID: str = Field(..., alias="Store ID")
    ProductName: str = Field(..., alias="Product Name")
    StockQty: int = Field(..., alias="Stock Qty")
    Price: int
    Date: str
    ExpiryDate: str = Field(..., alias="Expiry Date")
    Category: str
    Weather: str
    DailySales: int = Field(..., alias="Daily Sales")

    class Config:
        allow_population_by_field_name = True


class productRequest(BaseModel):
    products: List[productDetail]

@app.post("/tools/predictSpoilage")
def predictSpoilage(request: productRequest):
    try:
        response = requests.post("http://localhost:5000/predictSpoilage", json=request.dict(by_alias=True)["products"])
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/tools/pricingAgent")
def predictSpoilage(request: productRequest):
    try:
        response = requests.post(" http://localhost:5001/pricingAgent", json=request.dict(by_alias=True)["products"])
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/tools/logistic")
def predictSpoilage(request: productRequest):
    try:
        response = requests.post("http://localhost:5002/logistic", json=request.dict(by_alias=True)["products"])
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/tools/storeOpsAgent")
def predictSpoilage(request: productRequest):
    try:
        response = requests.post(" http://localhost:5003/storeOpsAgent", json=request.dict(by_alias=True)["products"])
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/tools/CustomerEngagementAgent")
def predictSpoilage(request: productRequest):
    try:
        response = requests.post("http://localhost:5005/CustomerEngagementAgent", json=request.dict(by_alias=True)["products"])
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/tools")
def list_tools():
    return {
        "predict_spoilage": {
            "description": "Predicts spoilage risk based on expiry, sales, and weather data.",
            "input_schema": ProductRequest.schema()
        },
        "pricing_agent": {
            "description": "Calculates pricing adjustments based on spoilage risk and sales velocity.",
            "input_schema": ProductRequest.schema()
        },
        "logistic": {
            "description": "Handles logistics operations such as product transfers between stores.",
            "input_schema": ProductRequest.schema()
        },
        "storeOpsAgent": {
            "description": "Manages store operations including markdowns and shelf placements.",
            "input_schema": ProductRequest.schema()
        },
        "CustomerEngagementAgent": {
            "description": "Engages customers with notifications and recommendations based on product data.",
            "input_schema": ProductRequest.schema()
        }
    }

