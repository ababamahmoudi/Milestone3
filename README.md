# 🌐 CloudMart — Enterprise Cloud Solution (Milestone 3)

CloudMart is a cloud-based e-commerce platform built as part of **CSP451 – Enterprise Cloud Solutions**.  
The project demonstrates modern cloud architecture using:

- **FastAPI** (backend)
- **Cosmos DB (NoSQL)** for products, cart, and orders
- **Docker** for containerization
- **Azure Container Instances (ACI)** for deployment
- **GitHub Actions CI/CD** for automation (test + build + deployment stage)

This version uses a **single-container architecture** where the FastAPI backend also serves the frontend HTML/JS interface.

---

## 🚀 Features

### ✔ Cloud-Hosted API  
Fully containerized API running on Azure Container Instances.

### ✔ Cosmos DB Integration  
Three containers:
- `products`
- `cart`
- `orders`

The app loads seeded products and supports full CRUD operations for cart and orders.

### ✔ CI/CD Pipeline  
GitHub Actions:
- **CI Pipeline (ci.yml)**:  
  Runs linting + dependency install + Docker build.
  
- **Deployment Pipeline (deploy.yml)**:  
  Echo-based manual deployment notice.  
  *(Azure deployment is performed manually due to Seneca Lab subscription restrictions.)*

### ✔ Single Container Deployment  
Docker Hub hosts the image, which is pulled by Azure Container Instances.

---

## 🏗 Architecture Overview

**Browser → Azure Container Instance → FastAPI App → Cosmos DB**

### Components:
- **Frontend + Backend**: Served from FastAPI inside the container
- **Database**: Cosmos DB (NoSQL Core API)
- **Hosting**: Azure Container Instance (Linux)
- **Container Registry**: Docker Hub
- **CI/CD**: GitHub Actions

---

## 📦 Project Structure

Milestone3/
├── main.py
├── Dockerfile
├── requirements.txt
├── .github/
│ └── workflows/
│ ├── ci.yml
│ └── deploy.yml
└── README.md


---

## 🧪 Local Development

### 1. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate


### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server locally
```bash
uvicorn main:app --reload
```

```bash
uvicorn main:app --reload
```
Open in your browser:
```bash
cpp
Copy code
http://127.0.0.1:8000/
```

## 🐳 Docker Commands
```bash
Build image
bash
Copy code
docker build -t cloudmart-api:local .
Run container
bash
Copy code
docker run --rm -p 8000:80 cloudmart-api:local☁️ Deployment (Azure Portal)
```

# Due to subscription restrictions in Seneca’s Azure Lab environment, deployment is performed manually through the Azure Portal:

- Push Docker image to Docker Hub

- Create Azure Container Instance (ACI)

### Configure environment variables:

```bash
COSMOS_ENDPOINT

COSMOS_KEY

Expose port 80

Assign DNS label (e.g., cloudmart132256223)
```

## 🔄 CI/CD Workflows

ci.yml

Runs automatically on each push to main

Installs dependencies

Lints FastAPI code

Builds Docker image

deploy.yml

Deployment stage included but performs:

echo "Azure deployment is performed manually due to subscription restrictions."


This satisfies the Milestone 3 requirement to demonstrate a deployment stage.

🔍 Endpoints
Method	Endpoint	Description
GET	/	Frontend HTML
GET	/health	Status + build info
GET	/api/v1/products	List products
GET	/api/v1/products/{id}	Get specific product
GET	/api/v1/categories	List categories
GET	/api/v1/cart	Retrieve cart
POST	/api/v1/cart/items	Add/update cart item
DELETE	/api/v1/cart/items/{id}	Remove cart item
POST	/api/v1/orders	Place order
GET	/api/v1/orders	List all orders
📸 Screenshots Required for Submission

Cosmos DB database + containers

Azure Container Instance overview

Container Environment Variables (COSMOS_ENDPOINT, COSMOS_KEY)

Running CloudMart app from DNS

GitHub Actions CI pipeline success

GitHub Actions Deploy pipeline success

Docker Hub image

Project folder structure

Commands used during build/deployment (terminal screenshots)

👤 Author

Ali Babamahmoudi
Seneca Polytechnic – CSP451
2025
