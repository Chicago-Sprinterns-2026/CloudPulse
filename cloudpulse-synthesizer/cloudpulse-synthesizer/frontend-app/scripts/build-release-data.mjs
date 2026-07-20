// Preprocesses every release_notes*.json file in ./data-raw into small,
// purpose-built files the app actually fetches at runtime:
//
//   public/release-data/recent.json          — last RECENT_MONTHS, all products (small, fast)
//   public/release-data/manifest.json        — { product, slug, count } for every product
//   public/release-data/by-product/<slug>.json  — one file per product, FULL history
//
// Why: the raw files total ~21MB across ~10 files. Doing the
// normalize/merge/dedupe in the BROWSER on every visit — even streamed —
// means every user's browser re-downloads and re-processes all 21MB before
// the app is usable. Doing it once here, at build time, means the browser
// only ever fetches the small slice it actually needs: recent.json for the
// default ledger, and a single per-product file only when someone clicks
// "show full history" for that specific product.
//
// Run with: npm run build:data
// Re-run this any time a file is added to/changed in ./data-raw.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RAW_DIR = path.join(__dirname, '..', 'data-raw');
const OUT_DIR = path.join(__dirname, '..', 'public', 'release-data');
const RECENT_MONTHS = 12; // must match RECENT_MONTHS in src/synthesizer.jsx

function normalizeRecord(raw) {
  if ('product' in raw && 'date' in raw && 'update' in raw) {
    return {
      product: raw.product,
      date: raw.date,
      update: raw.update,
      type: raw.release_note_type || raw.type || null,
      version: raw.version || raw.product_version || null,
    };
  }
  return {
    product: raw.product_name,
    date: raw.publish_date,
    update: raw.description,
    type: raw.release_note_type || null,
    version: raw.product_version || null,
  };
}

function extractRecords(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.releases)) return data.releases;
  return [];
}

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function isWithinMonths(dateStr, months, now = new Date()) {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return false;
  const cutoff = new Date(now);
  cutoff.setMonth(cutoff.getMonth() - months);
  return date >= cutoff;
}

function main() {
  const files = fs.readdirSync(RAW_DIR).filter((f) => f.endsWith('.json'));
  if (files.length === 0) {
    console.error(`No .json files found in ${RAW_DIR}`);
    process.exit(1);
  }

  const seen = new Set();
  const merged = [];

  files.forEach((file) => {
    const filePath = path.join(RAW_DIR, file);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const rawRecords = extractRecords(data);
    let validCount = 0;

    rawRecords.forEach((raw) => {
      const record = normalizeRecord(raw);
      if (!record.product || !record.date || !record.update) return;
      validCount += 1;

      const key = `${record.product}|${record.date}|${record.update}`;
      if (seen.has(key)) return;
      seen.add(key);
      merged.push(record);
    });

    if (rawRecords.length > 0 && validCount === 0) {
      console.warn(
        `⚠ ${file}: ${rawRecords.length} records but none matched a known schema — ` +
        `check normalizeRecord() in this script against this file's field names.`
      );
    }

    console.log(`  ${file}: ${rawRecords.length} raw records`);
  });

  merged.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));

  fs.mkdirSync(path.join(OUT_DIR, 'by-product'), { recursive: true });

  // recent.json — everything within the buffer window, all products
  const recent = merged.filter((r) => isWithinMonths(r.date, RECENT_MONTHS));
  fs.writeFileSync(path.join(OUT_DIR, 'recent.json'), JSON.stringify(recent));

  // by-product/<slug>.json — full history per product, plus a manifest
  const byProduct = new Map();
  merged.forEach((r) => {
    if (!byProduct.has(r.product)) byProduct.set(r.product, []);
    byProduct.get(r.product).push(r);
  });

  const manifest = [];
  const usedSlugs = new Map(); // guard against two products slugifying to the same string

  byProduct.forEach((records, product) => {
    let slug = slugify(product);
    if (usedSlugs.has(slug) && usedSlugs.get(slug) !== product) {
      slug = `${slug}-${usedSlugs.size}`;
    }
    usedSlugs.set(slug, product);

    fs.writeFileSync(path.join(OUT_DIR, 'by-product', `${slug}.json`), JSON.stringify(records));
    manifest.push({ product, slug, count: records.length });
  });

  manifest.sort((a, b) => b.count - a.count);
  fs.writeFileSync(path.join(OUT_DIR, 'manifest.json'), JSON.stringify(manifest));

  console.log();
  console.log(`Merged: ${merged.length} unique records across ${byProduct.size} products`);
  console.log(`recent.json (last ${RECENT_MONTHS} months): ${recent.length} records, ${fmtSize(path.join(OUT_DIR, 'recent.json'))}`);
  console.log(`manifest.json: ${manifest.length} products, ${fmtSize(path.join(OUT_DIR, 'manifest.json'))}`);
  console.log(`by-product/: ${byProduct.size} files`);
  console.log();
  console.log(`✓ Wrote output to ${path.relative(process.cwd(), OUT_DIR)}`);
}

function fmtSize(filePath) {
  const bytes = fs.statSync(filePath).size;
  return bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(2)}MB` : `${(bytes / 1024).toFixed(1)}KB`;
}

main();
