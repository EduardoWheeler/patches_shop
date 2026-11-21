const api = {
  async request(path, options = {}) {
    const response = await fetch("/api" + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail : "Error en la solicitud";
      throw new Error(detail);
    }
    return response.json();
  },
  getCategories() {
    return this.request("/categories");
  },
  getProducts(params = {}) {
    const query = new URLSearchParams();
    if (params.category_id) query.set("category_id", params.category_id);
    if (params.q) query.set("q", params.q);
    return this.request("/products?" + query.toString());
  },
  createOrder(payload) {
    return this.request("/orders", { method: "POST", body: JSON.stringify(payload) });
  },
};
