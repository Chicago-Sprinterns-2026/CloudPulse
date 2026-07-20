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
