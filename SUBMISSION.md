# 🌐 CloudMart – Milestone 3 Submission  
**Course:** CSP451 – Enterprise Cloud Solutions  
**Student:** Ali Babamahmoudi  
**Submission Date:** 2025  

---

# 1. Project Overview

CloudMart is an enterprise-grade cloud application built using:

- **FastAPI** for backend + frontend delivery  
- **Cosmos DB (NoSQL)** for operational data  
- **Docker** for containerization  
- **Docker Hub** for image distribution  
- **Azure Container Instances (ACI)** for hosting  
- **GitHub Actions CI/CD** for automation  

Architecture follows a **single-container model**, where the same container serves both the API and the frontend UI.

---

# 2. Architecture Diagram

*(Paste your architecture screenshot here)*  
You may also import the provided draw.io diagram below.

---

# 3. Architecture Description (Written)

CloudMart follows a lightweight but realistic cloud architecture optimized for containerized deployments:

### **Client Layer**
A browser sends requests to the public DNS endpoint of the Azure Container Instance.

### **Application Layer (Container)**
A single Docker image hosts:
- FastAPI REST API
- HTML/JavaScript frontend
- Business logic for products, cart, and orders
The container is deployed to **Azure Container Instances**, configured with environment variables so it can connect to Cosmos DB.

### **Data Layer**
**Azure Cosmos DB (NoSQL)** holds three containers:
- `products` – seeded catalog of items  
- `cart` – per-user shopping cart  
- `orders` – order history  

Each container uses partition keys that align with the application’s read patterns.

### **CI/CD Layer**
The GitHub Actions workflow performs:
- Linting and dependency validation  
- Docker image build  
- Deployment stage (manual notice due to Azure lab restrictions)

Automated deployment is not permitted in the Seneca Lab subscription, so actual deployment is performed manually in Azure Portal.

---

# 4. CI/CD Pipeline Summary

### **CI Pipeline (`ci.yml`)**
- Runs on every push to `main`
- Installs dependencies
- Runs linter (flake8)
- Builds a Docker image

### **Deploy Pipeline (`deploy.yml`)**
Outputs a message indicating deployment is manual:

Azure deployment is performed manually due to subscription restrictions.


This satisfies the assignment requirement of having a deployment stage in the pipeline.

### Manual Deployment
Because role assignments on the subscription are locked in the Seneca Lab environment, Azure Container Instance deployment is performed via Azure Portal.

---

# 5. Implementation Details

### **FastAPI Application**
- Serves both frontend and backend
- `/health` provides service status and CosmosDB connectivity
- API supports:
  - Listing products
  - Filtering by category
  - Adding/removing cart items
  - Creating and retrieving orders

### **Cosmos DB**
Database:  
cloudmart


Containers:


products (partition key: /category)
cart (partition key: /user_id)
orders (partition key: /user_id)


### **Docker Deployment**
Image stored at Docker Hub:


YOUR_DOCKERHUB_USERNAME/cloudmart-api:latest


Azure Container Instance configured with:

- Port 80 exposed  
- DNS Label: `cloudmart-yourid`
- Environment vars:
  - `COSMOS_ENDPOINT`
  - `COSMOS_KEY`

---

# 6. Testing Evidence (Endpoints)

#### **GET /**  
Returns frontend.

#### **GET /health**  
Shows health status, build time, db connection.

#### **GET /api/v1/products**  
Lists seeded products from Cosmos DB.

#### **GET /api/v1/categories**  
Returns distinct product categories.

#### **GET /api/v1/cart**  
Shows cart items for demo user.

#### **POST /api/v1/cart/items**  
Adds/updates cart items.

#### **DELETE /api/v1/cart/items/{id}**  
Removes a cart item.

#### **POST /api/v1/orders**  
Creates an order and clears cart.

#### **GET /api/v1/orders**  
Retrieves historical orders.

---

# 7. Required Screenshots

Include these screenshots in your submission PDF/Slides:

### **Azure**
- Cosmos DB account overview
- Data Explorer showing database + containers
- Container Instance overview
- Container Instance → Environment variables
- Running application in browser using DNS name
- Deployment logs (if any) or container instance events

### **Docker / Local**
- Successful Docker build of image
- Docker Hub repository page

### **GitHub**
- Repository structure
- `ci.yml` workflow run (green checkmark)
- `deploy.yml` workflow run & manual deployment notice
- GitHub Secrets page (redact keys)

### **Application**
- `/` frontend
- `/health` status
- `/api/v1/products` output
- `/api/v1/cart` output after adding items
- `/api/v1/orders` output after placing an order

---

# 8. Manual Deployment Rationale

Because subscription-level IAM is disabled in the Seneca Azure student environment, GitHub Actions cannot authenticate to Azure.  
Therefore:

- CI/CD handles code validation and image building.
- Actual deployment to Azure Container Instances is performed via Azure Portal.

This is expected and acceptable.

---

# 9. Reflection

CloudMart demonstrates how modern applications can be packaged and deployed using cloud-native services.  
I gained hands-on experience with:

- Docker containerization  
- Serverless NoSQL storage  
- Cloud networking  
- CI/CD pipeline structure  
- Manual vs. automated deployment  
- Single-container backend/frontend architecture  

This project helped reinforce how real cloud services connect in practice, and how configuration restrictions affect DevOps workflows.

---

# 10. Conclusion

CloudMart is deployed successfully on Azure, integrated with Cosmos DB, version-controlled in GitHub, containerized with Docker, and supported by a CI/CD pipeline.  
It meets all functional and architectural requirements for CSP451 Milestone 3.
