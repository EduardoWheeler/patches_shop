const TOKEN_KEY = "admin_token";
const STATUSES = ["pending", "paid", "shipped", "cancelled"];
const state = { categories: [], products: [], orders: [], editingId: null, currentImage: null };
const $ = (id) => document.getElementById(id);

function h(tag, props, ...children) {
  const el = Object.assign(document.createElement(tag), props || {});
  el.append(...children);
  return el;
}

function money(value) {
  return "$" + Number(value).toFixed(2);
}

function notify(text, kind) {
  $("admin-msg").textContent = text;
  $("admin-msg").className = kind || "";
}

function errorText(body) {
  if (Array.isArray(body.detail)) {
    return body.detail.map((d) => d.loc.slice(1).join(".") + ": " + d.msg).join("; ");
  }
  return typeof body.detail === "string" ? body.detail : "Error en la solicitud";
}

async function request(path, options = {}) {
  const headers = { Authorization: "Bearer " + sessionStorage.getItem(TOKEN_KEY) };
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const response = await fetch("/api" + path, { ...options, headers });
  if (response.status === 401) {
    logout();
    throw new Error("La sesión ha expirado");
  }
  if (!response.ok) throw new Error(errorText(await response.json().catch(() => ({}))));
  return response.status === 204 ? null : response.json();
}

function showApp(visible) {
  $("login-view").classList.toggle("hidden", visible);
  $("app-view").classList.toggle("hidden", !visible);
  $("logout").classList.toggle("hidden", !visible);
}

function logout() {
  sessionStorage.removeItem(TOKEN_KEY);
  showApp(false);
}

function slugify(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

// ---------- Render ----------
function renderCategories() {
  const select = $("product-form").elements["category_id"];
  select.replaceChildren(...state.categories.map((c) => h("option", { value: c.id, textContent: c.name })));
  $("categories-list").replaceChildren(
    ...state.categories.map((c) => h("li", { textContent: c.name + " (" + c.slug + ")" }))
  );
}

function renderProducts() {
  const names = Object.fromEntries(state.categories.map((c) => [c.id, c.name]));
  const header = h("tr", {}, ...["", "Nombre", "Categoría", "Precio", "Stock", ""].map((t) => h("th", { textContent: t })));
  const rows = state.products.map((p) => {
    const thumb = p.image_url ? h("img", { src: p.image_url, alt: p.name, className: "thumb" }) : "";
    const edit = h("button", { className: "btn", textContent: "Editar" });
    edit.addEventListener("click", () => editProduct(p));
    const del = h("button", { className: "btn", textContent: "Eliminar" });
    del.addEventListener("click", () => deleteProduct(p));
    return h("tr", {},
      h("td", {}, thumb), h("td", { textContent: p.name }), h("td", { textContent: names[p.category_id] || "" }),
      h("td", { textContent: money(p.price) }), h("td", { textContent: p.stock }), h("td", {}, edit, del));
  });
  $("products-table").replaceChildren(header, ...rows);
}

function renderOrders() {
  const productNames = Object.fromEntries(state.products.map((p) => [p.id, p.name]));
  const header = h("tr", {}, ...["#", "Cliente", "Artículos", "Total", "Fecha", "Estado"].map((t) => h("th", { textContent: t })));
  const rows = state.orders.map((o) => {
    const select = h("select", { disabled: o.status === "cancelled" });
    STATUSES.forEach((s) => select.append(h("option", { value: s, textContent: s, selected: s === o.status })));
    select.addEventListener("change", () => changeStatus(o, select.value));
    const items = o.items.map((i) =>
      i.quantity + " × " + (productNames[i.product_id] || "#" + i.product_id) + (i.custom_text ? ' ("' + i.custom_text + '")' : "")
    ).join(", ");
    return h("tr", {},
      h("td", { textContent: o.id }), h("td", { textContent: o.customer_name + " · " + o.customer_email + " · " + o.shipping_address }),
      h("td", { textContent: items }), h("td", { textContent: money(o.total) }),
      h("td", { textContent: new Date(o.created_at).toLocaleString() }), h("td", {}, select));
  });
  $("orders-table").replaceChildren(header, ...rows);
}

// ---------- Data ----------
async function loadAll() {
  try {
    [state.categories, state.products, state.orders] = await Promise.all([
      request("/categories"), request("/products"), request("/orders"),
    ]);
    renderCategories();
    renderProducts();
    renderOrders();
  } catch (err) {
    notify(err.message, "error");
  }
}

function resetProductForm() {
  const form = $("product-form");
  form.reset();
  state.editingId = null;
  state.currentImage = null;
  $("image-preview").classList.add("hidden");
  $("product-form-title").textContent = "Nuevo producto";
}

function editProduct(p) {
  const f = $("product-form").elements;
  state.editingId = p.id;
  state.currentImage = p.image_url;
  f["name"].value = p.name;
  f["category_id"].value = p.category_id;
  f["price"].value = p.price;
  f["stock"].value = p.stock;
  f["size"].value = p.size || "";
  f["description"].value = p.description || "";
  $("image-preview").classList.toggle("hidden", !p.image_url);
  if (p.image_url) $("image-preview").src = p.image_url;
  $("product-form-title").textContent = "Editar producto #" + p.id;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function deleteProduct(p) {
  if (!confirm("¿Eliminar '" + p.name + "' del catálogo?")) return;
  try {
    await request("/products/" + p.id, { method: "DELETE" });
    notify("Producto eliminado", "ok");
    await loadAll();
  } catch (err) {
    notify(err.message, "error");
  }
}

async function changeStatus(order, status) {
  if (status === "cancelled" && !confirm("Al cancelar el pedido #" + order.id + " se repondrá el stock. ¿Continuar?")) {
    renderOrders();
    return;
  }
  try {
    await request("/orders/" + order.id + "/status", { method: "PATCH", body: JSON.stringify({ status }) });
    notify("Pedido #" + order.id + " actualizado", "ok");
  } catch (err) {
    notify(err.message, "error");
  }
  await loadAll();
}

// ---------- Eventos ----------
$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = new FormData(form);
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: data.get("email"), password: data.get("password") }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(errorText(body));
    sessionStorage.setItem(TOKEN_KEY, body.access_token);
    const me = await request("/auth/me");
    if (me.role !== "admin") {
      logout();
      throw new Error("Esta cuenta no es de administrador");
    }
    form.reset();
    $("login-msg").textContent = "";
    showApp(true);
    await loadAll();
  } catch (err) {
    $("login-msg").textContent = err.message;
  }
});

$("logout").addEventListener("click", logout);

document.querySelectorAll("[data-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("active", b === button));
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("hidden", t.id !== "tab-" + button.dataset.tab));
  });
});

$("product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const f = event.target.elements;
  try {
    const file = f["image"].files[0];
    if (file) {
      const body = new FormData();
      body.append("file", file);
      state.currentImage = (await request("/uploads", { method: "POST", body })).url;
    }
    const payload = {
      category_id: Number(f["category_id"].value),
      name: f["name"].value.trim(),
      description: f["description"].value.trim() || null,
      price: f["price"].value,
      stock: Number(f["stock"].value),
      size: f["size"].value.trim() || null,
      image_url: state.currentImage,
      is_active: true,
    };
    const editing = state.editingId !== null;
    await request(editing ? "/products/" + state.editingId : "/products", {
      method: editing ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    notify(editing ? "Producto actualizado" : "Producto creado", "ok");
    resetProductForm();
    await loadAll();
  } catch (err) {
    notify(err.message, "error");
  }
});

$("product-cancel").addEventListener("click", resetProductForm);

$("category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const f = event.target.elements;
  const name = f["name"].value.trim();
  const slug = f["slug"].value.trim() || slugify(name);
  try {
    await request("/categories", { method: "POST", body: JSON.stringify({ name, slug }) });
    event.target.reset();
    notify("Categoría creada", "ok");
    await loadAll();
  } catch (err) {
    notify(err.message, "error");
  }
});

if (sessionStorage.getItem(TOKEN_KEY)) {
  request("/auth/me")
    .then((me) => {
      if (me.role !== "admin") return logout();
      showApp(true);
      return loadAll();
    })
    .catch(() => logout());
}
