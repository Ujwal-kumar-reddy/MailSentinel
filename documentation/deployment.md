# Deploy MailSentinel

1. Push the project to a Git repository you control. Include `ml/artifacts/release.joblib`, `ml/artifacts/metrics.json`, the frontend lockfile and both deployment configurations. The raw email archives are excluded.
2. In Render, choose **New → Blueprint** and connect the repository. Render reads the root `render.yaml`. For the first deployment use `http://localhost:5173` as the initial `CORS_ORIGINS` value. Keep the repository root as the working directory. The build installs the locked Python package versions. Startup loads the checked-in model.
3. Copy the actual HTTPS Render service address. Visit `/health` and confirm the selected model and ready status. Visit `/metrics` to verify the release.
4. In Vercel, import the same repository. Set **Root Directory** to `frontend`, framework to **Vite**, and production environment variable `VITE_API_URL` to the full HTTPS Render service origin. Deploy. Vite embeds this address at build time.
5. Copy the resulting production Vercel origin into Render’s `CORS_ORIGINS` and redeploy the API. Use comma-separated exact origins if you also need a custom domain. Exclude paths and trailing slashes. Preview deployments need their own allowed origins.
6. Open the public frontend. Run both example emails, upload the CSV template, export the results and compare the dashboard against the API report. Refresh a page with its hash in the address bar. Cold starts can delay the first request.

If the app shows **API unavailable**, open the API health endpoint directly. A working health endpoint plus a failed browser request usually points to the API build-time URL or the Render origin allow-list. If startup fails during deserialization, deploy the artifact and matching Python requirements together.

Provider references: [Render FastAPI guide](https://render.com/docs/deploy-fastapi) and [Vercel Vite guide](https://vercel.com/docs/frameworks/frontend/vite).
