// ─────────────────────────────────────────
// Brief → ScriptRequest handoff (Briefing Engine bridge)
// Mirrors lib/genflow-bridge.ts in the boost-briefing-engine.
// Decodes `?brief=…` query param into a typed handoff payload and
// surfaces it to the ProductForm for one-click pre-population.
// ─────────────────────────────────────────

import type { ScriptRequest } from '../types';

export interface BriefArchetype {
  primary: 'rebel';
  secondary: 'everyman';
  blend: 'hybrid';
}

export interface BriefVisuals {
  style: 'handheld' | 'raw' | 'documentary';
  format: 'ugc' | 'selfie-cam';
  feel: string;
}

export interface BriefAudio {
  type: 'local-licensed-music';
  voiceover: false;
  description?: string;
}

export interface BriefValueProp {
  price: '$25/mo';
  offering: 'Unlimited 5G';
  emphasis?: string;
}

export interface BriefConcept {
  title: string;
  description: string;
  targetAudience?: string;
  keyMessage: string;
}

export interface BriefSchema {
  archetype: BriefArchetype;
  visuals: BriefVisuals;
  audio: BriefAudio;
  valueProp: BriefValueProp;
  concept: BriefConcept;
}

export interface BriefHandoffPayload {
  brief: BriefSchema;
  request: ScriptRequest;
  source: 'boost-briefing-engine';
  brief_id: string;
  /** Optional: pre-written AI product-image prompt from the Briefing Engine */
  suggested_product_image_prompt?: string;
}

/** base64url → utf8 string (browser-safe) */
function b64urlDecode(token: string): string {
  const b64 = token.replace(/-/g, '+').replace(/_/g, '/');
  const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4);
  return atob(padded);
}

export function decodeBriefHandoff(token: string): BriefHandoffPayload | null {
  try {
    const json = b64urlDecode(token);
    const decoded = JSON.parse(json) as BriefHandoffPayload;
    if (!decoded?.brief?.concept?.title || !decoded?.request?.product_name) {
      return null;
    }
    return decoded;
  } catch {
    return null;
  }
}

/**
 * Read `?brief=…` from the current URL (if any) and return the decoded
 * payload. Strips the param from the address bar so a refresh won't
 * re-trigger pre-population.
 */
export function consumeBriefFromUrl(): BriefHandoffPayload | null {
  if (typeof window === 'undefined') return null;
  const params = new URLSearchParams(window.location.search);
  const token = params.get('brief');
  if (!token) return null;

  const payload = decodeBriefHandoff(token);

  // Clean the URL so a refresh doesn't re-fire the brief pre-fill.
  params.delete('brief');
  const search = params.toString();
  const newUrl =
    window.location.pathname + (search ? `?${search}` : '') + window.location.hash;
  window.history.replaceState({}, '', newUrl);

  return payload;
}
