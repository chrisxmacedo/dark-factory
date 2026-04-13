/**
 * Auto-generated API client.
 *
 * Usage:
 *   import { createApiClient } from '@clausehub/{repo-name}-client';
 *   const client = createApiClient({ baseUrl: '...', token: '...' });
 *   const { data } = await client.GET('/health');
 */

import createClient from 'openapi-fetch';

// After first regeneration, uncomment:
// import type { paths } from './schema.js';
// export type { paths } from './schema.js';

export { default as createClient } from 'openapi-fetch';

/**
 * Create a typed API client with Bearer auth pre-configured.
 *
 * After first regeneration, update the generic parameter:
 *   createClient<paths>({ ... })
 */
export function createApiClient(options: {
  baseUrl: string;
  token: string;
}) {
  return createClient({
    baseUrl: options.baseUrl,
    headers: {
      Authorization: `Bearer ${options.token}`,
      'Content-Type': 'application/vnd.api+json',
    },
  });
}
