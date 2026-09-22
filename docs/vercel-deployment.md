# Vercel container deployment

This project uses Vercel's container-image Functions beta and WebSocket support. It retains the Streamlit UI and research engine. It does not use a static export or a replacement frontend.

## Deploy

From the repository root, with an authenticated Vercel CLI:

```powershell
npx vercel deploy --yes
```

`vercel.json` explicitly selects `Dockerfile.vercel` as the dashboard container service and routes traffic to it. This avoids the existing project's Python framework preset producing an empty static build. Vercel builds the image in its hosted environment. Once preview checks pass, deploy to production:

```powershell
npx vercel deploy --prod --yes
```

The server listens on `PORT` or port 80. No provider API keys are required for public exchange endpoints. The image includes `bootstrap/bybit.parquet` and its provenance JSON; Docker verifies the digest and data validity during the build. Source upload and Docker context exclusions keep private local snapshots, secrets and logs out of deployment. Runtime ingestion writes raw data under `/tmp`; it is not durable storage. The hosted upload size is limited to 4 MB.

If the dashboard reports no verified real snapshot, open Technical details. The latest loader reports each exchange failure and the absolute missing or rejected snapshot path. Deploy from this repository directory, not its parent, using `npx vercel deploy --prod --yes`. A browser refresh alone does not update an older deployed image. Confirm the build log includes `Verified bundled real market data: bybit 730` before checking the production URL. If that build fails, fix the reported missing file or checksum rather than disabling verification.

## Required verification

- Health endpoint `/_stcore/health` and the initial dashboard return successfully.
- The Streamlit WebSocket connects and real snapshot metrics finish rendering even when exchange APIs are unavailable. The historical date and stale-data warning remain visible.
- Language changes and analysis controls recompute successfully.
- CSV uploads and downloads work, including repeated requests; these can be affected by routing to multiple instances.
- Reconnects are tested. Vercel terminates connections at the function duration limit and may route reconnects to a new instance. Session state and in-memory caches can be lost.

Do not describe this deployment as durable hosting for uploaded research data. Use external object storage and an appropriate session design before relying on persistence or multi-instance upload/download behavior. Local Docker verification requires a running Docker daemon.

References: [Container images](https://vercel.com/docs/functions/container-images), [WebSocket lifecycle](https://vercel.com/docs/functions/websockets).
