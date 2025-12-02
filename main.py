from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from azure.cosmos import CosmosClient, exceptions
from jose import jwt, JWTError
import os
import uuid
from datetime import datetime, timedelta

app = FastAPI(title="CloudMart API", version="1.2.0")

BUILD_TIME = datetime.utcnow().isoformat()

# -------------------- CORS -------------------- #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Cosmos DB -------------------- #

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
DATABASE_NAME = "cloudmart"

client = None
database = None
products_container = None
cart_container = None
orders_container = None


def init_cosmos():
    """
    Initialize Cosmos DB client and containers.
    If env vars are not set, the app still runs, but DB-dependent endpoints return empty data.
    """
    global client, database, products_container, cart_container, orders_container

    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        # running without DB (local/dev mode)
        return

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    products_container = database.get_container_client("products")
    cart_container = database.get_container_client("cart")
    orders_container = database.get_container_client("orders")

    # Seed data if necessary
    try:
        items = list(
            products_container.query_items(
                "SELECT * FROM c", enable_cross_partition_query=True
            )
        )
        if len(items) == 0:
            seed_products()
    except Exception:
        # if Cosmos is misconfigured, just skip seeding
        pass


def seed_products():
    """Seed demo products into the Cosmos DB 'products' container."""
    products = [
        {
            "id": "1",
            "name": "Wireless Headphones Pro",
            "description": "Premium noise-cancelling wireless headphones with 30hr battery",
            "category": "Electronics",
            "price": 199.99,
            "stock": 50,
            "image": "🎧",
        },
        {
            "id": "2",
            "name": "Smart Watch Elite",
            "description": "Advanced fitness tracking smartwatch with GPS",
            "category": "Electronics",
            "price": 299.99,
            "stock": 30,
            "image": "⌚",
        },
        {
            "id": "3",
            "name": "Running Shoes X1",
            "description": "Lightweight breathable running shoes",
            "category": "Sports",
            "price": 89.99,
            "stock": 100,
            "image": "👟",
        },
        {
            "id": "4",
            "name": "Laptop Backpack Pro",
            "description": "Water-resistant 15.6 inch laptop backpack",
            "category": "Accessories",
            "price": 49.99,
            "stock": 75,
            "image": "🎒",
        },
        {
            "id": "5",
            "name": "Coffee Maker Deluxe",
            "description": "12-cup programmable coffee maker",
            "category": "Home",
            "price": 79.99,
            "stock": 40,
            "image": "☕",
        },
        {
            "id": "6",
            "name": "Yoga Mat Premium",
            "description": "Extra thick eco-friendly yoga mat",
            "category": "Sports",
            "price": 35.99,
            "stock": 60,
            "image": "🧘",
        },
        {
            "id": "7",
            "name": "Bluetooth Speaker",
            "description": "Portable waterproof bluetooth speaker",
            "category": "Electronics",
            "price": 59.99,
            "stock": 45,
            "image": "🔊",
        },
        {
            "id": "8",
            "name": "Desk Lamp LED",
            "description": "Adjustable LED desk lamp with USB port",
            "category": "Home",
            "price": 29.99,
            "stock": 80,
            "image": "💡",
        },
    ]
    for p in products:
        try:
            products_container.create_item(p)
        except exceptions.CosmosResourceExistsError:
            pass


@app.on_event("startup")
async def startup_event():
    init_cosmos()

# -------------------- JWT AUTH -------------------- #

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "cloudmart-dev-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1


DEFAULT_USER = "demo_user"

# -------------------- HTML FRONTEND -------------------- #

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CloudMart - E-Commerce Platform</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing:border-box; margin:0; padding:0; }
body {
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
  min-height:100vh;
  color:#111827;
}
.header {
  background:rgba(15,23,42,0.85);
  color:#e5e7eb;
  padding:16px 24px;
  position:sticky;
  top:0;
  z-index:10;
}
.header-content {
  max-width:1100px;
  margin:0 auto;
  display:flex;
  align-items:center;
  justify-content:space-between;
}
.logo {
  font-size:24px;
  font-weight:800;
  letter-spacing:0.04em;
}
.logo span {
  color:#a5b4fc;
}
.db-badge {
  margin-left:8px;
  font-size:12px;
  padding:3px 8px;
  border-radius:999px;
  background:rgba(55,65,81,0.7);
  border:1px solid rgba(129,140,248,0.5);
}
.cart-btn {
  background:#4f46e5;
  border:none;
  color:white;
  padding:8px 14px;
  border-radius:999px;
  font-size:14px;
  display:flex;
  align-items:center;
  gap:8px;
  cursor:pointer;
}
.cart-count {
  background:white;
  color:#4f46e5;
  border-radius:999px;
  padding:2px 8px;
  font-size:12px;
  font-weight:700;
}
.main {
  max-width:1100px;
  margin:24px auto 40px;
  background:rgba(15,23,42,0.9);
  border-radius:16px;
  padding:20px;
  box-shadow:0 25px 50px -12px rgba(0,0,0,0.7);
  color:#e5e7eb;
}
.subtitle {
  color:#9ca3af;
  font-size:14px;
  margin-top:4px;
}
.chip-row {
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:16px;
}
.chip {
  padding:6px 12px;
  font-size:13px;
  border-radius:999px;
  border:1px solid rgba(156,163,175,0.5);
  background:rgba(31,41,55,0.8);
  color:#e5e7eb;
  cursor:pointer;
}
.chip.active {
  background:#f9fafb;
  color:#111827;
  border-color:transparent;
}
.product-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:16px;
  margin-top:20px;
}
.card {
  background:linear-gradient(145deg,rgba(17,24,39,0.98),rgba(15,23,42,0.98));
  border-radius:14px;
  padding:14px 14px 16px;
  border:1px solid rgba(55,65,81,0.9);
  box-shadow:0 10px 30px rgba(0,0,0,0.6);
}
.card-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
}
.emoji {
  font-size:32px;
}
.badge {
  font-size:11px;
  padding:3px 8px;
  border-radius:999px;
  background:rgba(55,65,81,0.8);
  color:#e5e7eb;
}
.card-title {
  margin-top:8px;
  font-weight:600;
  color:#f9fafb;
}
.card-desc {
  margin-top:6px;
  font-size:13px;
  color:#9ca3af;
}
.card-footer {
  margin-top:10px;
  display:flex;
  align-items:center;
  justify-content:space-between;
}
.price {
  font-weight:700;
  color:#a5b4fc;
}
.stock {
  font-size:11px;
  color:#6b7280;
}
.btn {
  padding:6px 10px;
  border-radius:999px;
  border:none;
  font-size:13px;
  cursor:pointer;
  font-weight:500;
}
.btn-primary {
  background:#4f46e5;
  color:white;
}
.btn-primary:hover {
  background:#4338ca;
}
.btn-outline {
  padding:6px 10px;
  border-radius:999px;
  border:1px solid rgba(156,163,175,0.7);
  font-size:13px;
  cursor:pointer;
  font-weight:500;
  background:transparent;
  color:#e5e7eb;
}
.cart-modal-backdrop {
  position:fixed;
  inset:0;
  background:rgba(15,23,42,0.8);
  display:none;
  align-items:flex-start;
  justify-content:center;
  padding-top:80px;
  z-index:50;
}
.cart-modal {
  background:#020617;
  border-radius:16px;
  padding:18px;
  width:100%;
  max-width:420px;
  border:1px solid rgba(75,85,99,0.8);
}
.cart-header-row {
  display:flex;
  justify-content:space-between;
  align-items:center;
}
.cart-items {
  margin-top:12px;
  max-height:300px;
  overflow-y:auto;
}
.cart-item {
  display:grid;
  grid-template-columns:1fr auto auto auto;
  align-items:center;
  gap:12px;
  padding:10px 0;
  border-bottom:1px solid rgba(31,41,55,0.9);
}
.cart-product {
  display:flex;
  flex-direction:column;
}
.cart-item-price {
  min-width:70px;
  text-align:right;
  color:#e5e7eb;
}
.cart-item-qty {
  min-width:20px;
  text-align:center;
  display:inline-block;
}
.cart-qty-controls {
  display:flex;
  align-items:center;
  gap:6px;
}
.qty-btn {
  width:22px;
  height:22px;
  border-radius:999px;
  border:none;
  background:#1f2937;
  color:#e5e7eb;
  cursor:pointer;
}
.cart-total-row {
  margin-top:10px;
  display:flex;
  justify-content:space-between;
  font-weight:600;
}
.toast {
  position:fixed;
  bottom:18px;
  right:18px;
  padding:10px 14px;
  border-radius:10px;
  background:#22c55e;
  color:#052e16;
  font-size:13px;
  display:none;
  z-index:60;
}
.toast.error {
  background:#f97373;
  color:#450a0a;
}
small.build {
  display:block;
  margin-top:10px;
  font-size:11px;
  color:#6b7280;
}
.cart-header-row h3 {
  color:#e5e7eb;
  font-weight:600;
}
.cart-modal > div span {
  color:#e5e7eb;
  font-weight:500;
}
#cartTotal {
  color:#a5b4fc;
  font-weight:700;
}
.search-input {
  width:100%;
  padding:8px 10px;
  border-radius:8px;
  border:1px solid rgba(75,85,99,0.9);
  background:#020617;
  color:#e5e7eb;
  font-size:13px;
  margin-top:12px;
}
</style>
</head>
<body>
<header class="header">
  <div class="header-content">
    <div>
      <div class="logo">Cloud<span>Mart</span><span class="db-badge">🗄️ Cosmos DB</span></div>
      <div class="subtitle">CI/CD: GitHub Actions → Docker Hub → Azure Container Instances</div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
      <button class="btn-outline" id="loginBtn" onclick="openLogin()">Login</button>
      <button class="cart-btn" onclick="openCart()">🛒 Cart <span id="cartCount" class="cart-count">0</span></button>
    </div>
  </div>
</header>

<main class="main">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:10px;">
    <div>
      <h2 style="font-size:18px;font-weight:600;">Products</h2>
      <p style="font-size:13px;color:#9ca3af;margin-top:4px;">
        Browse products from Cosmos DB, add to cart, and place orders.
      </p>
    </div>
    <div style="font-size:11px;color:#6b7280;text-align:right;">
      <div id="healthStatus">Checking health…</div>
      <small class="build">Build: <span id="buildTime"></span></small>
    </div>
  </div>

  <div class="chip-row" id="categoryChips">
  </div>

  <div>
    <input id="searchBox" class="search-input" type="text"
      placeholder="Search products by name or category..."
      oninput="searchProducts()" />
  </div>

  <div class="product-grid" id="productGrid">
  </div>
</main>

<!-- CART MODAL -->
<div class="cart-modal-backdrop" id="cartModal">
  <div class="cart-modal">
    <div class="cart-header-row">
      <h3>Shopping Cart</h3>
      <button class="qty-btn" onclick="closeCart()">✕</button>
    </div>

    <div style="
      display:grid;
      grid-template-columns:1fr auto auto auto;
      font-size:12px;
      color:#9ca3af;
      margin-top:12px;
      padding-bottom:6px;
      border-bottom:1px solid rgba(31,41,55,0.6);
    ">
      <span>Product</span>
      <span>Qty</span>
      <span>Total</span>
      <span></span>
    </div>

    <div class="cart-items" id="cartItems"></div>

    <div class="cart-total-row">
      <span>Total</span>
      <span id="cartTotal">$0.00</span>
    </div>

    <div style="margin-top:12px;display:flex;justify-content:flex-end;gap:8px;">
      <button class="btn" onclick="closeCart()">Close</button>
      <button class="btn btn-primary" onclick="placeOrder()">Place Order</button>
    </div>
  </div>
</div>

<!-- LOGIN MODAL -->
<div class="cart-modal-backdrop" id="loginModal">
  <div class="cart-modal">
    <div class="cart-header-row">
      <h3>Login</h3>
      <button class="qty-btn" onclick="closeLogin()">✕</button>
    </div>
    <form onsubmit="performLogin(event)" style="margin-top:12px;display:flex;flex-direction:column;gap:8px;">
      <div>
        <label style="font-size:12px;color:#9ca3af;">Username</label>
        <input id="loginUsername" type="text" value="demo"
          style="width:100%;margin-top:4px;padding:6px 8px;border-radius:8px;
                 border:1px solid rgba(75,85,99,0.9);background:#020617;
                 color:#e5e7eb;font-size:13px;">
      </div>
      <div>
        <label style="font-size:12px;color:#9ca3af;">Password</label>
        <input id="loginPassword" type="password" value="demo123"
          style="width:100%;margin-top:4px;padding:6px 8px;border-radius:8px;
                 border:1px solid rgba(75,85,99,0.9);background:#020617;
                 color:#e5e7eb;font-size:13px;">
      </div>
      <div style="margin-top:10px;display:flex;justify-content:flex-end;gap:8px;">
        <button type="button" class="btn" onclick="closeLogin()">Cancel</button>
        <button type="submit" class="btn btn-primary">Login</button>
      </div>
    </form>
    <p style="margin-top:8px;font-size:11px;color:#6b7280;">
      Demo credentials: demo / demo123
    </p>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let products = [];
let categories = [];
let cart = [];
let authToken = null;

async function fetchJSON(url, options) {
  const opts = options || {};
  opts.headers = opts.headers || {};

  if (authToken) {
    opts.headers["Authorization"] = "Bearer " + authToken;
  }

  const res = await fetch(url, opts);
  if (!res.ok) {
    throw new Error("HTTP " + res.status);
  }
  return res.json();
}

async function loadHealth() {
  try {
    const data = await fetchJSON("/health");
    document.getElementById("healthStatus").textContent =
      data.status === "healthy"
        ? "Status: healthy (" + data.db_status + ")"
        : "Status: " + data.status;
    document.getElementById("buildTime").textContent = data.build_time || "";
  } catch (e) {
    document.getElementById("healthStatus").textContent = "Status: unreachable";
  }
}

function updateAuthUI() {
  const btn = document.getElementById("loginBtn");
  if (!btn) return;
  if (authToken) {
    btn.textContent = "Logout";
  } else {
    btn.textContent = "Login";
  }
}

async function init() {
  authToken = localStorage.getItem("cloudmart_token") || null;
  updateAuthUI();

  await loadHealth();
  try {
    products = await fetchJSON("/api/v1/products");
    categories = await fetchJSON("/api/v1/categories");
    if (authToken) {
      try {
        cart = await fetchJSON("/api/v1/cart");
      } catch (e) {
        cart = [];
      }
    } else {
      cart = [];
    }
  } catch (e) {
    showToast("Failed to load data from API", true);
  }
  renderCategories();
  renderProducts();
  updateCartCount();
}

function renderCategories() {
  const container = document.getElementById("categoryChips");
  container.innerHTML = "";
  const allChip = document.createElement("button");
  allChip.className = "chip active";
  allChip.textContent = "All products";
  allChip.onclick = () => filterCategory(null);
  container.appendChild(allChip);

  categories.forEach(cat => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = cat;
    chip.onclick = () => filterCategory(cat);
    container.appendChild(chip);
  });
}

function renderProducts(filtered) {
  const grid = document.getElementById("productGrid");
  grid.innerHTML = "";
  const list = filtered || products;

  list.forEach(p => {
    const card = document.createElement("article");
    card.className = "card";

    card.innerHTML = `
      <div class="card-header">
        <div class="emoji">${p.image || "🛒"}</div>
        <span class="badge">${p.category}</span>
      </div>
      <div class="card-title">${p.name}</div>
      <div class="card-desc">${p.description}</div>
      <div class="card-footer">
        <div>
          <div class="price">$${Number(p.price).toFixed(2)}</div>
          <div class="stock">${p.stock} in stock</div>
        </div>
        <button class="btn btn-primary" data-id="${p.id}">Add to cart</button>
      </div>
    `;

    const btn = card.querySelector("button");
    btn.onclick = () => addToCart(p.id, 1);

    grid.appendChild(card);
  });
}

function filterCategory(category) {
  const chips = document.querySelectorAll(".chip");
  chips.forEach(c => c.classList.remove("active"));
  if (!category) {
    chips[0].classList.add("active");
    renderProducts();
    return;
  }
  chips.forEach(c => {
    if (c.textContent === category) c.classList.add("active");
  });
  renderProducts(products.filter(p => p.category === category));
}

async function searchProducts() {
  const box = document.getElementById("searchBox");
  if (!box) return;
  const q = box.value.trim();

  if (q.length === 0) {
    // Restore based on active category
    const activeChip = document.querySelector(".chip.active");
    if (!activeChip || activeChip.textContent === "All products") {
      renderProducts();
    } else {
      const cat = activeChip.textContent;
      renderProducts(products.filter(p => p.category === cat));
    }
    return;
  }

  try {
    const results = await fetchJSON("/api/v1/search?q=" + encodeURIComponent(q));
    renderProducts(results);
  } catch (e) {
    showToast("Search failed", true);
  }
}

function updateCartCount() {
  document.getElementById("cartCount").textContent = cart.length;
}

function requireLogin() {
  showToast("Please log in to use cart and orders", true);
  openLogin();
}

function openCart() {
  if (!authToken) {
    requireLogin();
    return;
  }
  renderCart();
  document.getElementById("cartModal").style.display = "flex";
}

function closeCart() {
  document.getElementById("cartModal").style.display = "none";
}

function renderCart() {
  const container = document.getElementById("cartItems");
  container.innerHTML = "";

  if (!cart || cart.length === 0) {
    container.innerHTML = '<p style="color:#9ca3af;font-size:13px;">Your cart is empty.</p>';
    document.getElementById("cartTotal").innerText = "$0.00";
    return;
  }

  let total = 0;

  cart.forEach(item => {
    const price = Number(item.price) || 0;
    const qty = Number(item.quantity) || 0;
    const lineTotal = price * qty;
    total += lineTotal;

    const row = document.createElement("div");
    row.className = "cart-item";

    row.innerHTML = `
      <div class="cart-product">
        <div>${item.name}</div>
        <div style="font-size:12px;color:#6b7280;">$${price.toFixed(2)} each</div>
      </div>

      <div class="cart-qty-controls">
        <button class="qty-btn dec">-</button>
        <span class="cart-item-qty">${qty}</span>
        <button class="qty-btn inc">+</button>
      </div>

      <div class="cart-item-price">$${lineTotal.toFixed(2)}</div>

      <button class="qty-btn remove-btn">✕</button>
    `;

    row.querySelector(".dec").onclick = () => {
      if (qty <= 1) {
        removeFromCart(item.id);
      } else {
        updateCartQuantity(item.id, qty - 1);
      }
    };

    row.querySelector(".inc").onclick = () => {
      updateCartQuantity(item.id, qty + 1);
    };

    row.querySelector(".remove-btn").onclick = () => {
      removeFromCart(item.id);
    };

    container.appendChild(row);
  });

  document.getElementById("cartTotal").innerText = `$${total.toFixed(2)}`;
}

async function addToCart(productId, quantity) {
  if (!authToken) {
    requireLogin();
    return;
  }
  try {
    await fetchJSON("/api/v1/cart/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    cart = await fetchJSON("/api/v1/cart");
    updateCartCount();
    showToast("Saved to Cosmos DB!");
  } catch (e) {
    showToast("Failed to update cart", true);
  }
}

async function updateCartQuantity(productId, quantity) {
  if (!authToken) {
    requireLogin();
    return;
  }
  await addToCart(productId, quantity);
  renderCart();
}

async function removeFromCart(productId) {
  if (!authToken) {
    requireLogin();
    return;
  }
  try {
    await fetchJSON("/api/v1/cart/items/" + productId, {
      method: "DELETE",
    });
    cart = await fetchJSON("/api/v1/cart");
    updateCartCount();
    renderCart();
    showToast("Removed from cart");
  } catch (e) {
    showToast("Failed to remove item", true);
  }
}

async function placeOrder() {
  if (!authToken) {
    requireLogin();
    return;
  }
  if (cart.length === 0) {
    showToast("Cart is empty", true);
    return;
  }
  try {
    const order = await fetchJSON("/api/v1/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    cart = [];
    updateCartCount();
    closeCart();
    showToast("Order saved to Cosmos DB!");
    console.log("Order:", order);
  } catch (e) {
    showToast("Failed to place order", true);
  }
}

function openLogin() {
  // If already logged in, clicking acts as logout
  if (authToken) {
    authToken = null;
    localStorage.removeItem("cloudmart_token");
    cart = [];
    updateCartCount();
    updateAuthUI();
    showToast("Logged out");
    return;
  }
  document.getElementById("loginModal").style.display = "flex";
}

function closeLogin() {
  document.getElementById("loginModal").style.display = "none";
}

async function performLogin(event) {
  event.preventDefault();
  const u = document.getElementById("loginUsername").value.trim();
  const p = document.getElementById("loginPassword").value.trim();

  if (!u || !p) {
    showToast("Please enter username and password", true);
    return;
  }

  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p }),
    });

    if (!res.ok) {
      showToast("Invalid credentials", true);
      return;
    }

    const data = await res.json();
    authToken = data.access_token;
    localStorage.setItem("cloudmart_token", authToken);
    updateAuthUI();
    closeLogin();

    // Reload cart from API now that we're authenticated
    try {
      cart = await fetchJSON("/api/v1/cart");
      updateCartCount();
    } catch (e) {
      cart = [];
    }

    showToast("Logged in successfully");
  } catch (e) {
    showToast("Login failed", true);
  }
}

let toastTimeout;
function showToast(message, isError) {
  const t = document.getElementById("toast");
  t.textContent = message;
  t.classList.toggle("error", !!isError);
  t.style.display = "block";
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => (t.style.display = "none"), 3000);
}

init();
</script>
</body>
</html>
"""

# -------------------- ROUTES -------------------- #

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_TEMPLATE


@app.get("/health")
def health():
    db_status = "connected" if client else "disconnected"
    return {
        "status": "healthy",
        "service": "cloudmart-api",
        "version": "1.2.0",
        "build_time": BUILD_TIME,
        "database": "cosmos-db",
        "db_status": db_status,
        "deployed_via": "aci-container",
    }


@app.post("/auth/login")
def auth_login(body: LoginRequest):
    if body.username != DEMO_USERNAME or body.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": body.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/v1/products")
def list_products(category: str | None = None):
    if not products_container:
        # running without DB
        return []
    try:
        if category:
            query = "SELECT * FROM c WHERE c.category = @category"
            items = list(
                products_container.query_items(
                    query,
                    parameters=[{"name": "@category", "value": category}],
                    enable_cross_partition_query=True,
                )
            )
        else:
            items = list(
                products_container.query_items(
                    "SELECT * FROM c", enable_cross_partition_query=True
                )
            )
        return items
    except Exception:
        return []


@app.get("/api/v1/search")
def search_products(q: str):
    """
    Simple search endpoint: searches in product name and category.
    """
    if not products_container:
        return []
    try:
        query = (
            "SELECT * FROM c "
            "WHERE CONTAINS(c.name, @q) "
            "OR CONTAINS(c.category, @q)"
        )
        items = list(
            products_container.query_items(
                query,
                parameters=[{"name": "@q", "value": q}],
                enable_cross_partition_query=True,
            )
        )
        return items
    except Exception:
        return []


@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str):
    if not products_container:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        items = list(
            products_container.query_items(
                "SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": product_id}],
                enable_cross_partition_query=True,
            )
        )
        if items:
            return items[0]
        raise HTTPException(status_code=404, detail="Product not found")
    except exceptions.CosmosHttpResponseError:
        raise HTTPException(status_code=404, detail="Product not found")


@app.get("/api/v1/categories")
def get_categories():
    if not products_container:
        return []
    try:
        items = list(
            products_container.query_items(
                "SELECT DISTINCT c.category FROM c",
                enable_cross_partition_query=True,
            )
        )
        return [item["category"] for item in items]
    except Exception:
        return []


@app.get("/api/v1/cart")
def get_cart(current_user: str = Depends(get_current_user)):
    if not cart_container or not products_container:
        return []

    try:
        items = list(
            cart_container.query_items(
                "SELECT * FROM c WHERE c.user_id = @user_id",
                parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
                enable_cross_partition_query=True,
            )
        )

        enriched_cart = []
        for item in items:
            product_items = list(
                products_container.query_items(
                    "SELECT * FROM c WHERE c.id = @pid",
                    parameters=[{"name": "@pid", "value": item["product_id"]}],
                    enable_cross_partition_query=True,
                )
            )
            if not product_items:
                continue

            product = product_items[0]
            enriched_cart.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": item["quantity"],
                    "image": product.get("image", "🛒"),
                    "category": product.get("category", "General"),
                }
            )

        return enriched_cart

    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/cart/items")
def add_to_cart(item: CartItem, current_user: str = Depends(get_current_user)):
    if not cart_container:
        return {"error": "Database not available"}
    try:
        existing = list(
            cart_container.query_items(
                "SELECT * FROM c WHERE c.user_id = @user_id AND c.product_id = @product_id",
                parameters=[
                    {"name": "@user_id", "value": DEFAULT_USER},
                    {"name": "@product_id", "value": item.product_id},
                ],
                enable_cross_partition_query=True,
            )
        )
        if existing:
            cart_item = existing[0]
            cart_item["quantity"] = item.quantity
            cart_container.upsert_item(cart_item)
        else:
            cart_item = {
                "id": str(uuid.uuid4()),
                "user_id": DEFAULT_USER,
                "product_id": item.product_id,
                "quantity": item.quantity,
            }
            cart_container.create_item(cart_item)
        return {"message": "Saved to Cosmos DB"}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/v1/cart/items/{product_id}")
def remove_from_cart(product_id: str, current_user: str = Depends(get_current_user)):
    if not cart_container:
        return {"error": "Database not available"}
    try:
        items = list(
            cart_container.query_items(
                "SELECT * FROM c WHERE c.user_id = @user_id AND c.product_id = @product_id",
                parameters=[
                    {"name": "@user_id", "value": DEFAULT_USER},
                    {"name": "@product_id", "value": product_id},
                ],
                enable_cross_partition_query=True,
            )
        )
        for item in items:
            cart_container.delete_item(item["id"], partition_key=DEFAULT_USER)
        return {"message": "Removed from Cosmos DB"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/v1/orders")
def create_order(current_user: str = Depends(get_current_user)):
    if not orders_container or not cart_container:
        return {"error": "Database not available"}
    try:
        cart_items = list(
            cart_container.query_items(
                "SELECT * FROM c WHERE c.user_id = @user_id",
                parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
                enable_cross_partition_query=True,
            )
        )
        order = {
            "id": str(uuid.uuid4()),
            "user_id": DEFAULT_USER,
            "items": [
                {"product_id": i["product_id"], "quantity": i["quantity"]}
                for i in cart_items
            ],
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat(),
        }
        orders_container.create_item(order)
        for item in cart_items:
            cart_container.delete_item(item["id"], partition_key=DEFAULT_USER)
        return order
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/orders")
def get_orders(current_user: str = Depends(get_current_user)):
    if not orders_container:
        return []
    try:
        items = list(
            orders_container.query_items(
                "SELECT * FROM c WHERE c.user_id = @user_id",
                parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
                enable_cross_partition_query=True,
            )
        )
        return items
    except Exception:
        return []

