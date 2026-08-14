# Deploying SafeMoMo publicly (Render free tier)

The repo is deploy-ready: one Docker service serves the API and the built
frontend from a single public URL. Everything below is a one-time setup of
about 10 minutes.

## 1. Create a Brevo API key (for report acknowledgment emails)

Render's **free** tier blocks outbound SMTP ports (25, 465, 587), so Gmail
SMTP can never send from a free instance — the connection just times out.
Brevo's HTTP API runs over normal HTTPS (443), which is not blocked, and
its free tier allows 300 emails/day.

1. Sign up at https://www.brevo.com (free plan, no card).
2. Verify `safemomoapi@gmail.com` as a **sender**: Senders, Domains & IPs ->
   Senders -> Add a sender. Brevo emails that address a confirmation link;
   click it. (No domain purchase needed — a verified single sender is
   enough.)
3. Create the key: SMTP & API -> API Keys -> Generate a new API key.
   Copy it — this is `SAFEMOMO_BREVO_API_KEY`.

The sender address itself is set in `render.yaml` as `SAFEMOMO_FROM_EMAIL`
and needs no dashboard entry.

If no key is set, reports still work perfectly — the app simply doesn't
claim an email was sent.

## 2. Deploy on Render

1. Sign up / log in at https://render.com (easiest: "Sign in with GitHub").
2. Click **New +** -> **Blueprint** and connect the
   `kamanquaowusu/MINI-PROJECT` repository. Render reads `render.yaml`
   and proposes the `safemomo` web service (free plan, Docker).
3. When prompted for environment variables, set:
   - `SAFEMOMO_BREVO_API_KEY` = the API key from step 1
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
- **No SMTP:** free instances cannot reach SMTP ports at all, which is why
  email goes through Brevo's HTTP API. Gmail SMTP would only work on a
  paid instance. See:
  https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports
- Acknowledgment emails stay dormant (reports still work, users still see
  the on-screen confirmation) if `SAFEMOMO_BREVO_API_KEY` is unset.
