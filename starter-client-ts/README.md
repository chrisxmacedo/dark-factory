# {repo-name}-client-ts

Auto-generated TypeScript client for the [{repo-name}](https://github.com/ClauseHub/{repo-name}) API.

> **Do not edit this code manually.** It is regenerated from the API's OpenAPI
> spec on every merge to main.

## Installation

```bash
npm install @clausehub/{repo-name}-client
```

## Usage

```typescript
import { createApiClient } from '@clausehub/{repo-name}-client';

const client = createApiClient({
  baseUrl: 'https://{repo-name}.ondigitalocean.app',
  token: 'your-jwt',
});

// Fully typed — autocomplete on all endpoints
const { data, error } = await client.GET('/suppliers');
```

## How regeneration works

1. A merge to main on the API repo triggers `publish-clients.yml`
2. That workflow exports `openapi.json` and triggers `regenerate.yml` here
3. `openapi-typescript` regenerates typed schemas from the spec
4. A PR is opened with the changes for review

## Post-clone setup

After cloning from `starter-client-ts`, the `/create-project` command will:
1. Update the package name in `package.json`
2. Set the `CLIENTS_PAT` secret on the API repo
3. Trigger the first regeneration
