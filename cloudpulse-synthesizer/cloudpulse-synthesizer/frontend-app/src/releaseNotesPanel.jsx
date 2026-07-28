import React from 'react';
import { useLiveReleaseNotes } from './useReleaseNotes';
import { truncate } from './utils';

const PREVIEW_COUNT = 10;

/**
 * A short, fast preview of a product's most recent release notes.
 *
 * Deliberately one request. The full Release History tab walks every page of a
 * product's history — 400+ notes across several sequential round trips — which
 * is right when someone has come specifically to browse history, and much too
 * slow for a panel that sits beside the docs. This asks for ten rows and stops.
 *
 * @param {string}   product        Product name to fetch notes for.
 * @param {function} onViewHistory  Called when the reader wants the full history.
 */
export default function ReleaseNotesPanel({ product, onViewHistory }) {
  const { items: rawItems, loading, error, isLive } = useLiveReleaseNotes({
    product,
    // Fetch extra so exact duplicates in the source data don't leave the panel
    // short of PREVIEW_COUNT rows.
    pageSize: PREVIEW_COUNT * 2,
    pollMs: 0, // a preview panel doesn't need to watch for new notes
  });

  // The table contains some byte-identical rows. Drop those, but keep notes
  // that share a date and wording yet differ by version — App Engine publishes
  // the same change per generation, and those are genuinely separate notes.
  const items = React.useMemo(() => {
    const seen = new Set();
    return rawItems
      .filter((item) => {
        const key = `${item.date}|${item.version || ''}|${item.update}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .slice(0, PREVIEW_COUNT);
  }, [rawItems]);

  return (
    <aside className="notes-panel">
      <div className="notes-panel-head">
        <h4>Recent release notes</h4>
        {!loading && !error && items.length > 0 && (
          <span className={`notes-panel-source${isLive ? '' : ' notes-panel-stale'}`}>
            {isLive ? 'Live from Google Cloud' : 'Offline snapshot'}
          </span>
        )}
      </div>

      {loading && <p className="note notes-panel-empty">Loading…</p>}

      {error && (
        <p className="note notes-panel-empty" style={{ color: 'var(--coral)' }}>
          Couldn't load release notes.
        </p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="note notes-panel-empty">No release notes found for {product}.</p>
      )}

      <div className="notes-panel-list">
        {items.map((item) => (
          <a
            key={item.id}
            className="notes-panel-item"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            title={`Open the ${item.product} release notes for ${item.date}`}
          >
            <div className="notes-panel-meta">
              <span className="notes-panel-date">{item.date}</span>
              {item.type && <span className="notes-panel-type">{item.type}</span>}
              {item.version && <span className="notes-panel-version">{item.version}</span>}
            </div>
            <p>{truncate(item.update, 85)}</p>
          </a>
        ))}
      </div>

      {onViewHistory && !loading && items.length > 0 && (
        <button
          type="button"
          className="btn btn-secondary full-width notes-panel-more"
          onClick={onViewHistory}
        >
          View full history
        </button>
      )}
    </aside>
  );
}