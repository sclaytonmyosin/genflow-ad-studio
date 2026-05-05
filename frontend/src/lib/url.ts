// ─────────────────────────────────────────
// Subpath-aware URL helpers.
//
// Vite injects `import.meta.env.BASE_URL` from the `base` config, so we read
// it once here and prefix any absolute path that hits the backend (API,
// /output assets, /asset diagrams). Works transparently:
//   - dev / local: BASE_URL = "/"             → "/api/v1/..."
//   - prod behind nginx at /genflow: BASE_URL = "/genflow/" → "/genflow/api/v1/..."
// ─────────────────────────────────────────

const RAW_BASE = import.meta.env.BASE_URL || '/';
// Normalize: ensure exactly one trailing slash, no doubles.
const BASE = RAW_BASE.endsWith('/') ? RAW_BASE : `${RAW_BASE}/`;
const BASE_ROOT = BASE.replace(/\/$/, '');

/** Prefix an absolute path (e.g. "/api/v1/jobs") with the deployed base URL. */
export function prefix(path: string): string {
  const normalized = path.startsWith('/') ? path.slice(1) : path;
  return `${BASE}${normalized}`;
}

/** Convenience: prefix an /api/v1 path. */
export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return prefix(`/api/v1${normalized}`);
}

/** Convenience: prefix an /asset (diagrams etc) path. */
export function assetUrl(name: string): string {
  return prefix(`/asset/${name}`);
}

/**
 * Browser URL for static files under ``/output/`` (sample product images,
 * generated/uploaded assets). Prefixes Vite ``base`` in production.
 * Pass-through for ``http(s):``, ``blob:``, ``data:``, and paths that already
 * include the deploy base (e.g. ``/genflow/output/...`` from the API).
 */
export function outputUrl(path: string): string {
  if (!path) return path;
  if (
    path.startsWith('http') ||
    path.startsWith('blob:') ||
    path.startsWith('data:')
  ) {
    return path;
  }
  if (BASE_ROOT && (path === BASE_ROOT || path.startsWith(`${BASE_ROOT}/`))) {
    return path;
  }
  const trimmed = path.startsWith('/') ? path.slice(1) : path;
  return prefix(trimmed);
}
