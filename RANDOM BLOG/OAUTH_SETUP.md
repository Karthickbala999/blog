## Google OAuth (Direct API Flow)

1. Create a **Web** OAuth client at <https://console.cloud.google.com/apis/credentials>.
   - Authorized redirect URI: `http://localhost:8000/oauth/google/callback/` (adjust for prod).
   - Copy the client ID and client secret.

2. Provide the credentials to Django before starting the server:

```powershell
$env:GOOGLE_CLIENT_ID="your-client-id"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
# Optional: override redirect URI if not using localhost
$env:GOOGLE_REDIRECT_URI="https://your-domain.com/oauth/google/callback/"
```

For Bash/Zsh:

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="https://your-domain.com/oauth/google/callback/"
```

3. Start the server (`python manage.py runserver`) and navigate to `/login/` or `/signup/`.
   - Clicking **Continue with Google** launches the Google consent screen.
   - After the callback, the backend exchanges the code for tokens using Google’s OAuth API, fetches profile data, provisions the user (if needed), and logs them in.

4. To test manually:
   - `GET /oauth/google/` should redirect to Google with a `state` parameter stored in the session.
   - After approving access, Google calls `/oauth/google/callback/?code=...&state=...`.
   - Any state mismatch or missing code returns HTTP 400 with an error message.

