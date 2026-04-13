# {repo-name}-client-py

Auto-generated Python client for the [{repo-name}](https://github.com/ClauseHub/{repo-name}) API.

> **Do not edit this code manually.** It is regenerated from the API's OpenAPI
> spec on every merge to main.

## Installation

```bash
pip install {repo-name}-client
# or
uv add {repo-name}-client
```

## Usage

```python
from client import Client

client = Client(base_url="https://{repo-name}.ondigitalocean.app", token="your-jwt")

# Async usage
from client import AuthenticatedClient

client = AuthenticatedClient(base_url="...", token="your-jwt")
```

## How regeneration works

1. A merge to main on the API repo triggers `publish-clients.yml`
2. That workflow exports `openapi.json` and triggers `regenerate.yml` here
3. `openapi-python-client` regenerates all models and API methods
4. A PR is opened with the changes for review

## Post-clone setup

After cloning from `starter-client-py`, the `/create-project` command will:
1. Rename the package in `pyproject.toml` and `openapi-config.yml`
2. Set the `CLIENTS_PAT` secret on the API repo
3. Trigger the first regeneration

The `openapi-config.yml` file controls the generated package name — update
`project_name_override` and `package_name_override` to match the API name
(e.g. `energy_api_client` for `energy-api`).
