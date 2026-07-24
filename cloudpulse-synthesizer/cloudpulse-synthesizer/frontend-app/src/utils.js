
export function stripHtml(html) {
  return html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}

export function truncate(text, maxLength) {
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}


export function productsMatch(a, b) {
  if (a === b) return true;
  const x = a.toLowerCase();
  const y = b.toLowerCase();
  return x.includes(y) || y.includes(x);
}

// Finds which known products are mentioned in free-form text (e.g. a chat
// message), for resolving one-pager targets without an extra LLM call.
// Drops a match that's wholly contained in a longer match also found (e.g.
// "AI" swallowed by "Vertex AI") so overlapping product names don't both show up.
export function extractProductsFromText(text, products) {
  const lower = text.toLowerCase();
  const found = products.filter((product) => lower.includes(product.toLowerCase()));
  return found.filter(
    (product) =>
      !found.some(
        (other) => other !== product && other.length > product.length && other.toLowerCase().includes(product.toLowerCase())
      )
  );
}
