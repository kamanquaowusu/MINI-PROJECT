# Deploying SafeMoMo publicly (Render free tier)

The repo is deploy-ready: one Docker service serves the API and the built
frontend from a single public URL. Everything below is a one-time setup of
about 10 minutes.

## 1. Create the Gmail App Password (for report acknowledgment emails)

1. Make sure 2-Step Verification is ON for your Google account
   (myaccount.google.com -> Security).
2. Go to https://myaccount.google.com/apppasswords
3. Create a password named e.g. "SafeMoMo" and copy the 16-character code.
   This is what goes in `SAFEMOMO_SMTP_PASSWORD` — NOT your normal Gmail
   password.

## 2. Deploy on Render

1. Sign up / log in at https://render.com (easiest: "Sign in with GitHub").
2. Click **New +** -> **Blueprint** and connect the
   `kamanquaowusu/MINI-PROJECT` repository. Render reads `render.yaml`
   and proposes the `safemomo` web service (free plan, Docker).
3. When prompted for environment variables, set:
   - `SAFEMOMO_SMTP_USER` = your Gmail address
   - `SAFEMOMO_SMTP_PASSWORD` = the App Password from step 1
4. Click **Apply** / **Create**. First build takes ~5–10 minutes
   (npm build + pip install). The service URL will look like
   `https://safemomo.onrender.com`.

Every future `git push` to `main` redeploys automatically.

## 3. Verify after deploy

- Open `https://<your-url>/api/health` -> should show
  `"status":"ok","model_loaded":true`.
- Open the root URL, check a message, submit a scam report with your own
  email -> you should receive the acknowledgment email.

## Known free-tier limitations

- **Cold starts:** the free instance sleeps after ~15 min of inactivity;
  the first visit after that takes ~30–60 s to wake.
- **Ephemeral disk:** `data/shadow/` (checks / feedback / reports logs)
  is wiped on every redeploy or restart. Before retraining from shadow
  data, download the JSONL files from the service shell, or upgrade to a
  paid instance with a persistent disk.
- Acknowledgment emails stay dormant (reports still work, users still see
  the on-screen confirmation) if the SMTP env vars are unset.
