
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
