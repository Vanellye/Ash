# ERIA dimensional API on Fly.io

## Runtime model
- Node.js 22 HTTP adapter invokes the existing Fetch-handler API.
- SQLite lives on the mounted Fly Volume at `/data/eria.sqlite`.
- One Machine stays running; HTTP auto-stop is disabled.
- Health checks call `/health`; rolling deploys keep the prior Machine available during replacement where capacity permits.

## One-time Fly setup
1. Create the Fly app named `eria-dimensional-api` in the desired organization.
2. Create a persistent volume named `eria_data` in `ord` (or change `primary_region` and create it in that region).
3. Set the mutation credential: `fly secrets set MUTATION_TOKEN='…' -a eria-dimensional-api`.
4. Deploy from the repository root: `fly deploy --config fly.toml`.
5. Confirm `https://eria-dimensional-api.fly.dev/health` returns HTTP 200.

## GitHub Actions
Create a GitHub environment named `flyio-staging` and add `FLY_API_TOKEN` as an environment secret. The workflow validates tests and builds the image before deployment.

## Important
- This uses SQLite on one Fly Volume and is intended for a single active writer Machine. Do not scale multiple writers against this SQLite file.
- A Fly Volume is local to one Machine and is not replicated backup. Configure and test backups before production data is stored.
- Keep `MUTATION_TOKEN` in Fly secrets; never commit it.
- The initial setup does not create the Fly app, volume, secret, GitHub environment, or deploy the service. Those require Fly account authorization.
