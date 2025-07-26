import streamlit as st
import pandas as pd
import json
import requests
import numpy as np
import matplotlib.pyplot as plt



def run_customer_agent(data):
    try:
        response = requests.post(
            "http://localhost:6000/tools/CustomerEngagementAgent", json={"products": data})
        response.raise_for_status()
        customer_agent = response.json()
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh} - {response.text}")
        return []
    except requests.exceptions.RequestException as err:
        print(f"Request Error: {err}")
        return []
    return customer_agent

st.title("Customer product")

uploaded_file = st.file_uploader("Upload a your inventory file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.dropna(how='all', inplace=True)
    df = df.replace({np.nan: None})

#Convert date fields to ISO format
    date_columns = ['Expiry Date', 'Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')

#Remove null fields from each record
    records = df.to_dict(orient="records")
    cleaned_records = [{k: v for k, v in record.items() if v is not None} for record in records]

#Keep only records with all required fields
    required_fields = ["Product ID", "Product Name", "Category", "Store ID", "Expiry Date", 
                       "Stock Qty", "Daily Sales", "Date", "Weather", "Price"]
    final_records = [
        record for record in cleaned_records
        if all(field in record and record[field] is not None for field in required_fields)
    ]

    products_json = final_records

    st.write("Data Uploaded Successfully!")
    st.dataframe(df)
    #st.subheader("Converted JSON Structure")
    #st.json({"products": products_json})


    st.header("Inventory Metrics")
    total_stock = df["Stock Qty"].sum()
    avg_days_to_expiry = (pd.to_datetime(df["Expiry Date"]) - pd.to_datetime(df["Date"])).dt.days.mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stock", int(total_stock))
    col2.metric("Avg Days to Expiry", f"{avg_days_to_expiry:.1f}")


if uploaded_file:
    output = run_customer_agent(products_json)
    st.success("Agent Recommendations Generated")
    #st.json(output)

    tab1, tab2, tab3, tab4 = st.tabs(["Forecasting", "Logistics Suggestions", "Store Operation", "Trade-Off Metrics"])

    with tab1:
        st.subheader("Spoilage Prediction and Pricing Recommendations")
        for item in output:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Product Name", item['Product Name'])
            col2.metric("Days to Expiry", item['day_to_expiry'])
            col3.metric("Markdown Percentage", item['Markdown'])
            col4.metric("New Price", f"{item['New Price']}")
            st.markdown("---")

    with tab2:
        st.subheader("Logistics Suggestions")
        for item in output:
            if "Logistics Suggestion" in item:
                suggestion = item["Logistics Suggestion"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Product Name", suggestion['Product Name'])
                col2.metric("Transfer To", suggestion['To Store'])
                col3.metric("Transfer Quantity", suggestion['Transfer Qty'])
                col4.metric("Transfer Cost", suggestion['Transfer Cost'])
                st.markdown("---")

    with tab3:
        st.subheader("Store Operation Action")
        for item in output:
            if "Store Ops Action" in item:
                operation = item["Store Ops Action"]

                status = operation.get("Status", "Unknown")
                status_color = {
                    "Pending": "orange",
                    "Completed": "green",
                    "In Progress": "blue",
                    "Failed": "red"
                }.get(status, "gray")

                col1, col2, col3 = st.columns(3)
                col1.metric("Product Name", operation.get("Product Name", "N/A"))
                col2.metric("Product ID", operation.get("Product ID", "N/A"))
                col3.markdown(f"**Status:** <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)

                st.markdown(f"**Action:** {operation.get('Action', 'N/A')}")
                st.markdown(f"**Assigned To:** {operation.get('Assigned To', 'N/A')}")
                st.markdown(f"**Due Time:** {operation.get('Due Time', 'N/A')}")
                st.markdown(f"**Reason:** {operation.get('Reason', 'N/A')}")
                st.markdown("---")

    with tab4:
        st.subheader("Trade-Off Metrics Visualization")

        if output:
            df = pd.DataFrame(output)

            df["Waste Reduced (units)"] = df["Logistics Suggestion"].apply(lambda x: x["Transfer Qty"] if isinstance(x, dict) else 0)
            df["Margin Impact"] = df["Logistics Suggestion"].apply(lambda x: round(x["Transfer Qty"] * x["New Price"], 2) if isinstance(x, dict) else 0)
            df["Inventory Velocity"] = df["sales_velocity"]

            total_waste = df["Waste Reduced (units)"].sum()
            total_margin = df["Margin Impact"].sum()
            avg_velocity = df["Inventory Velocity"].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Waste Reduced", f"{total_waste} units")
            col2.metric("Total Margin Impact", f"{total_margin:.2f}")
            col3.metric("Avg Inventory Velocity", f"{avg_velocity:.2f}")

            st.markdown("---")

        # Waste Reduction
            fig1, ax1 = plt.subplots()
            ax1.bar(df["Product Name"], df["Waste Reduced (units)"], color="skyblue")
            ax1.set_title("Waste Reduction by Product")
            ax1.set_ylabel("Units")
            st.pyplot(fig1)

        # Margin Impact
            fig2, ax2 = plt.subplots()
            ax2.bar(df["Product Name"], df["Margin Impact"], color="salmon")
            ax2.set_title("Margin Impact by Product")
            ax2.set_ylabel("Rate")
            st.pyplot(fig2)

        # Inventory Velocity
            fig3, ax3 = plt.subplots()
            ax3.bar(df["Product Name"], df["Inventory Velocity"], color="lightgreen")
            ax3.set_title("Inventory Velocity by Product")
            ax3.set_ylabel("Velocity")
            st.pyplot(fig3)
        else:
            st.warning("Please run the Customer Engagement Agent to generate output.")


