// The scraped release notes store `update` as raw HTML. Strip tags before
// showing it as card preview text — rendering raw HTML would just show
// literal <p>/<strong> tags to the user.
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

// Release-note product names don't always match the product catalog exactly
// (e.g. catalog has "Cloud SQL", release notes have "Cloud SQL for MySQL").
// Exact match first, fall back to a loose substring match either direction.
export function productsMatch(a, b) {
  if (a === b) return true;
  const x = a.toLowerCase();
  const y = b.toLowerCase();
  return x.includes(y) || y.includes(x);
}
