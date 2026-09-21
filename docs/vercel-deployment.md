# Vercel container deployment

This project uses Vercel's container-image Functions beta and WebSocket support. It retains the Streamlit UI and research engine. It does not use a static export or a replacement frontend.

## Deploy

From the repository root, with an authenticated Vercel CLI:

```powershell
npx vercel deploy --yes
```

Vercel detects `Dockerfile.vercel`, builds the image in its hosted build environment, and routes traffic to the container. Once preview checks pass, deploy to production:

```powershell
npx vercel deploy --prod --yes
```

The server listens on `PORT` or port 80. No provider API keys are required for the synthetic demo or public exchange endpoints. Source upload and Docker context exclusions keep existing local market snapshots, secrets and logs out of deployment. Runtime ingestion writes raw data under `/tmp`; it is not durable storage. The hosted upload size is limited to 4 MB.

## Required verification

- Health endpoint `/_stcore/health` and the initial dashboard return successfully.
- The Streamlit WebSocket connects and the demo metrics finish rendering.
- Language changes and analysis controls recompute successfully.
- CSV uploads and downloads work, including repeated requests; these can be affected by routing to multiple instances.
- Reconnects are tested. Vercel terminates connections at the function duration limit and may route reconnects to a new instance. Session state and in-memory caches can be lost.

Do not describe this deployment as durable hosting for uploaded research data. Use external object storage and an appropriate session design before relying on persistence or multi-instance upload/download behavior. Local Docker verification requires a running Docker daemon.

References: [Container images](https://vercel.com/docs/functions/container-images), [WebSocket lifecycle](https://vercel.com/docs/functions/websockets).
