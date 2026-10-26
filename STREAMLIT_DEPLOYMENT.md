# Streamlit deployment: public demo vs. private research

This repository intentionally supports **two deployment configurations** from the same `main` branch and `app.py` entrypoint. The default configuration is fail-closed: anonymous visitors see the synthetic interactive demo only. Real research can contact external financial data sources and paid model APIs and **must not be offered to anonymous visitors**.

## 1. Public, no-login interactive demo

Deployment coordinates:

| Setting | Value |
| --- | --- |
| GitHub repository | `Away928/ai-research-agent` |
| Branch | `main` |
| Entrypoint | `app.py` |
| App URL (existing) | `https://ai-research-agent928.streamlit.app/` |
| Community Cloud Sharing | **This app is public and searchable** |
| Live research secrets | **None** |

The application runs in *synthetic demo-only* mode when `AGENT_LIVE_RESEARCH_ENABLED` is not exactly `1` or `AGENT_LIVE_ACCESS_SHA256` is missing/invalid.

- Do **not** set `AGENT_LIVE_RESEARCH_ENABLED` or any private-owner passcode on the public app.
- Remove any saved financial-provider/API tokens from the public app's Secrets if they are not needed. No API keys, external financial provider calls, or uploads are needed for the demo.
- Open the app URL in a private/incognito browser window without logging in. Verify the one-click demo and absence of the `真实研究` option and provider inputs.
- If the URL redirects to `/-/login`, the **Streamlit Community Cloud sharing permission** still blocks anonymous access. Publishing a public GitHub repository does **not** override that setting.

On Streamlit Community Cloud, open [your app workspace](https://share.streamlit.io/), choose the existing app **Settings → Sharing → Who can view this app**, and select **This app is public and searchable**. Alternatively, use **Share → Make this app public**. The owner must perform this change in the authenticated Cloud UI.

## 2. Separate, owner-only real research app

If real financial-provider queries and LLM calls are required through a browser, create **another Streamlit Community Cloud app** from the same repository, branch and `app.py` entrypoint. Give it a different subdomain and set **Sharing → Only specific people can view this app**. Streamlit Community Cloud has limits on private apps per account/workspace; check current platform eligibility.

To enable its private UI, provide **both** of these *server-side* values in the private app's **Settings → Secrets** as root-level TOML keys:

```toml
AGENT_LIVE_RESEARCH_ENABLED = "1"
AGENT_LIVE_ACCESS_SHA256 = "<64-character SHA-256 hex of a long random owner passphrase>"
```

Generate a **new random access passphrase** locally (not here, not in Git, not in an Issue):

```bash
python3 - <<'PY'
import hashlib, secrets
passphrase = secrets.token_urlsafe(32)
print("Save this passphrase in a password manager:", passphrase)
print("Set AGENT_LIVE_ACCESS_SHA256 to:", hashlib.sha256(passphrase.encode()).hexdigest())
PY
```

Save the raw passphrase **only** in your password manager. Paste **only its hash** into the private app Secrets. A short common password is unsafe: the hash is not salted, so the access token must have high entropy. Always restrict this second app to your own Cloud account as an additional access control.

For optional model calls, configure a backend credential **only in the private app's Secrets** (never in the public app or the Git repository), such as:

```toml
# Add to the private app ONLY, if using an OpenAI-compatible backend:
OPENAI_API_KEY = "<private-provider-credential>"
OPENAI_BASE_URL = "https://api.example.com/v1"
OPENAI_MODEL = "example-model"
```

These values are placeholders, not a functional provider configuration. Choose your actual provider settings privately. In the private UI, enter the access passphrase in the sidebar, click **解锁私人研究**, then choose **真实研究**. Lock the UI again after use. The app does not put environment-sourced API keys into browser input values, but third-party model services may receive uploaded text by design.

### Local owner-only run

You can start the same owner mode on a private computer by setting the two environment variables above **locally** and launching:

```bash
python -m streamlit run app.py
```

Do not expose the local server to a public network. Avoid sharing its address or browser session. Without both variables, the UI always runs in synthetic-only mode.

## 3. Security boundary and tests

- The real-research option and the agent execution branch are both guarded server-side. A forged UI selection or client-side API key cannot enable it.
- `ui/live_access.py` verifies a SHA-256 digest with a constant-time comparison, and the password input is masked. No raw access passphrase belongs in this repository.
- Live research remains a **single-user experimental workflow**: local result/history files may persist during a process lifetime. It is not an authenticated multi-tenant service, and no cloud deployment security audit is claimed.
- Avoid entering real client files or unlicensed data. Provider/LLM requests can incur charges and return errors; outputs still need original-source verification.
- Test the default public mode with `python scripts/verify_demo.py`; test the private authorization path with `python scripts/verify_real_entry.py` (uses only synthetic mock credentials and disables real network operations).
- See [Streamlit Community Cloud sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app) and [Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) for current platform controls.

**Do not treat a GitHub CI success as proof that Streamlit Cloud's Sharing setting is public.** Verify the deployed URL independently in an unauthenticated browser.
