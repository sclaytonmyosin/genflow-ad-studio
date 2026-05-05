import type { SSEEvent } from '../types';
import { apiUrl } from '../lib/url';

export function createSSEConnection(
  jobId: string,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Event) => void
): EventSource {
  const es = new EventSource(apiUrl(`/jobs/${jobId}/stream`));

  es.onmessage = (e: MessageEvent) => {
    try {
      const event: SSEEvent = JSON.parse(e.data);
      onEvent(event);
    } catch {
      console.error('Failed to parse SSE event:', e.data);
    }
  };

  es.onerror = (e: Event) => {
    if (onError) {
      onError(e);
    }
  };

  return es;
}
