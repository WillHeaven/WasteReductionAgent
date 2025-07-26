# WasteReductionAgent
Agent, My first Agentic Agent

This project is an Agentic AI system designed to reduce product spoilage and optimize inventory management in retail environments, particularly for perishable goods. It consists of five intelligent agents, each operating independently but orchestrated through a unified API gateway for seamless decision-making.

## 🧠 Intelligent Agents

1. **Spoilage Prediction Agent**  
   Uses logistic regression to assess spoilage risk based on expiry dates, sales velocity, weather, and product category.

2. **Pricing Agent**  
   Recommends markdowns for high-risk products to reduce waste while preserving profit margins.

3. **Logistics Agent**  
   Suggests inter-store transfers for excess stock nearing expiry using a trained random forest model.

4. **Store Operations Agent**  
   Uses an LLM to recommend in-store actions like shelf placement or staff alerts tailored to product condition.

5. **Customer Engagement Agent**  
   Generates persuasive app notifications to encourage purchases of discounted or expiring items.

## 🛠️ Tech Stack

- **Machine Learning**: scikit-learn (Logistic Regression, Random Forest)
- **LLM Integration**: Amazon Bedrock with Claude 3 Sonnet
- **Microservices**: Flask / FastAPI for each agent
- **Communication**: REST APIs
- **Notifications**: AWS SNS (optional)
- **Validation**: Pydantic models for schema consistency

## 🎯 Objective

To proactively identify at-risk products, optimize pricing and logistics, and guide store operations to minimize waste, improve efficiency, and enhance customer engagement.
