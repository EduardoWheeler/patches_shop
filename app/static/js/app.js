const state = { cart: [] };

const els = {
  grid: document.getElementById("product-grid"),
  search: document.getElementById("search"),
  category: document.getElementById("category-filter"),
  cartPanel: document.getElementById("cart-panel"),
  cartToggle: document.getElementById("cart-toggle"),
  cartItems: document.getElementById("cart-items"),
  cartCount: document.getElementById("cart-count"),
  cartTotal: document.getElementById("cart-total"),
  form: document.getElementById("checkout-form"),
  message: document.getElementById("message"),
};

function money(value) {
  return "$" + Number(value).toFixed(2);
}

function setMessage(text, kind) {
  els.message.textContent = text;
  els.message.className = kind || "";
}

function renderProducts(products) {
  els.grid.replaceChildren();
  if (!products.length) {
    els.grid.textContent = "No se encontraron productos.";
    return;
  }
  products.forEach((p) => {
    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h3");
    title.textContent = p.name;
    const desc = document.createElement("p");
    desc.className = "meta";
    desc.textContent = (p.description || "") + (p.size ? " · " + p.size : "");
    const price = document.createElement("div");
    price.className = "price";
    price.textContent = money(p.price);
    const stock = document.createElement("div");
    stock.className = "meta";
    stock.textContent = p.stock > 0 ? "Stock: " + p.stock : "Agotado";

    const text = document.createElement("input");
    text.placeholder = "Texto personalizado (opcional)";
    text.maxLength = 100;
    const qty = document.createElement("input");
    qty.type = "number";
    qty.min = 1;
    qty.max = Math.max(p.stock, 1);
    qty.value = 1;

    const add = document.createElement("button");
    add.className = "btn primary";
    add.textContent = "Añadir al carrito";
    add.disabled = p.stock < 1;
    add.addEventListener("click", () => {
      const quantity = Math.min(Math.max(parseInt(qty.value, 10) || 1, 1), p.stock);
      addToCart(p, quantity, text.value.trim());
    });

    if (p.image_url) {
      const img = document.createElement("img");
      img.src = p.image_url;
      img.alt = p.name;
      img.className = "thumb";
      card.appendChild(img);
    }
    card.append(title, desc, price, stock, text, qty, add);
    els.grid.appendChild(card);
  });
}

function addToCart(product, quantity, customText) {
  const existing = state.cart.find(
    (i) => i.product_id === product.id && i.custom_text === customText
  );
  if (existing) {
    existing.quantity += quantity;
  } else {
    state.cart.push({
      product_id: product.id,
      name: product.name,
      price: Number(product.price),
      quantity,
      custom_text: customText,
    });
  }
  els.cartPanel.classList.remove("hidden");
  renderCart();
}

function renderCart() {
  els.cartItems.replaceChildren();
  let total = 0;
  let count = 0;
  state.cart.forEach((item, index) => {
    total += item.price * item.quantity;
    count += item.quantity;
    const li = document.createElement("li");
    const label = document.createElement("span");
    label.textContent =
      item.quantity + " × " + item.name + (item.custom_text ? ' ("' + item.custom_text + '")' : "");
    const right = document.createElement("span");
    right.textContent = money(item.price * item.quantity) + " ";
    const remove = document.createElement("button");
    remove.className = "btn";
    remove.textContent = "✕";
    remove.addEventListener("click", () => {
      state.cart.splice(index, 1);
      renderCart();
    });
    right.appendChild(remove);
    li.append(label, right);
    els.cartItems.appendChild(li);
  });
  els.cartTotal.textContent = money(total);
  els.cartCount.textContent = count;
}

async function loadProducts() {
  try {
    const products = await api.getProducts({
      category_id: els.category.value,
      q: els.search.value.trim(),
    });
    renderProducts(products);
  } catch (err) {
    els.grid.textContent = err.message;
  }
}

async function loadCategories() {
  try {
    const categories = await api.getCategories();
    categories.forEach((c) => {
      const option = document.createElement("option");
      option.value = c.id;
      option.textContent = c.name;
      els.category.appendChild(option);
    });
  } catch (err) {
    setMessage(err.message, "error");
  }
}

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.cart.length) {
    setMessage("El carrito está vacío.", "error");
    return;
  }
  const data = new FormData(els.form);
  const payload = {
    customer_name: data.get("customer_name"),
    customer_email: data.get("customer_email"),
    shipping_address: data.get("shipping_address"),
    items: state.cart.map((i) => ({
      product_id: i.product_id,
      quantity: i.quantity,
      custom_text: i.custom_text || null,
    })),
  };
  try {
    const order = await api.createOrder(payload);
    state.cart = [];
    renderCart();
    els.form.reset();
    setMessage("¡Pedido #" + order.id + " creado! Total: " + money(order.total), "ok");
    loadProducts();
  } catch (err) {
    setMessage(err.message, "error");
  }
});

let searchTimer;
els.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadProducts, 300);
});
els.category.addEventListener("change", loadProducts);
els.cartToggle.addEventListener("click", () => els.cartPanel.classList.toggle("hidden"));

loadCategories();
loadProducts();
renderCart();
