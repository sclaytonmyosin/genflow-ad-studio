import type { ScriptModelOption } from '../types';

// ─── Ad Tones ───────────────────────────────────────────────
export const AD_TONES = ['energetic', 'sophisticated', 'playful', 'authoritative', 'warm'];

// ─── Script Models (multi-provider) ─────────────────────────
export const SCRIPT_MODELS: ScriptModelOption[] = [
  // ── Google (Vertex AI) ──
  { id: 'gemini-2.5-flash',  label: 'Gemini 2.5 Flash',  provider: 'Google',    description: 'Fast iteration' },
  { id: 'gemini-2.5-pro',    label: 'Gemini 2.5 Pro',    provider: 'Google',    description: 'Highest quality (default)' },
  // ── Anthropic (via OpenRouter) ──
  { id: 'anthropic/claude-opus-4-5',    label: 'Claude Opus 4',    provider: 'Anthropic', description: 'Best reasoning & creativity' },
  { id: 'anthropic/claude-sonnet-4-5',  label: 'Claude Sonnet 4',  provider: 'Anthropic', description: 'Balanced speed & quality' },
  { id: 'anthropic/claude-haiku-3-5',   label: 'Claude Haiku 3.5', provider: 'Anthropic', description: 'Fastest Claude' },
  // ── OpenAI ──
  { id: 'openai/gpt-4.5-preview', label: 'GPT-4.5',   provider: 'OpenAI', description: 'Creative writing' },
  { id: 'openai/gpt-4o',          label: 'GPT-4o',    provider: 'OpenAI', description: 'Multimodal flagship' },
  // ── xAI ──
  { id: 'x-ai/grok-3',       label: 'Grok 3',       provider: 'xAI',      description: 'Latest Grok' },
  { id: 'x-ai/grok-3-mini',  label: 'Grok 3 Mini',  provider: 'xAI',      description: 'Fast Grok' },
  // ── Mistral ──
  { id: 'mistralai/mistral-large-latest', label: 'Mistral Large', provider: 'Mistral', description: 'Top Mistral model' },
  // ── Kimi / ByteDance ──
  { id: 'moonshot/moonshot-v1-128k', label: 'Kimi (Moonshot)', provider: 'Kimi', description: 'ByteDance / 128k context' },
];

// Legacy alias so existing code referencing GEMINI_MODELS still works
export const GEMINI_MODELS = SCRIPT_MODELS;

/** Default favors quality for final creative output; switch to Flash in-product for speed. */
export const DEFAULT_SCRIPT_MODEL = 'gemini-2.5-pro';

// Provider badge colors
export const PROVIDER_COLORS: Record<string, string> = {
  Google:    '#4285F4',
  Anthropic: '#D97706',
  OpenAI:    '#10A37F',
  xAI:       '#1DA1F2',
  Mistral:   '#7C3AED',
  Kimi:      '#EF4444',
};

// ─── Ethnicities ────────────────────────────────────────────
export const ETHNICITIES = [
  '', 'South Asian', 'East Asian', 'Southeast Asian', 'Black', 'White',
  'Latino', 'Middle Eastern', 'Mixed',
];

// ─── Age Ranges ─────────────────────────────────────────────
export const AGE_RANGES = ['18-25', '25-35', '35-45', '45-55', '55+'];

// ─── Veo Models (Video Generation) ──────────────────────────
export const VEO_MODELS = [
  { id: 'veo-3.1-generate-preview',      label: 'Veo 3.1 Preview',      description: 'Standard — Best quality' },
  { id: 'veo-3.1-fast-generate-preview', label: 'Veo 3.1 Fast Preview', description: 'Faster generation' },
];

// ─── Image Resolutions ──────────────────────────────────────
export const IMAGE_RESOLUTIONS = ['1K', '2K', '4K'] as const;

// ─── Defaults ───────────────────────────────────────────────
export const DEFAULT_IMAGE_RESOLUTION = '2K';
export const DEFAULT_STORYBOARD_QC_THRESHOLD = 60;
export const DEFAULT_MAX_REGEN_ATTEMPTS = 3;
export const DEFAULT_VIDEO_QC_THRESHOLD = 3;
export const DEFAULT_MAX_VIDEO_QC_REGEN = 2;
export const DEFAULT_NUM_VIDEO_VARIANTS = 1;
export const DEFAULT_NUM_AVATAR_VARIANTS = 2;
