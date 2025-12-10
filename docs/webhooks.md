## Workflow

1. Parse webhook
2. Extract diff/code changes
3. Apply external knowledge
4. Send to LLM
5. Format response
6. Post comment back

### Step 1: Parse webhook

After parsing the webhook, we need to **fetch the diff** using the VCS APIs:

**GitHub - Get PR Diff:**

```python
# From the parsed webhook, we have:
pr_number = base_webhook.pull_request.number
repo_name = base_webhook.pull_request.repository_name

# Make API call to GitHub
GET https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files
```
**Returns:**

```json
[
  {
    "filename": "src/auth.py",
    "status": "modified",
    "additions": 5,
    "deletions": 2,
    "patch": "@@ -10,7 +10,10 @@ def authenticate(user):\n-    if user.password == 'admin':\n+    if check_password_hash(user.password_hash, password):\n         return True"
  }
]
```

**GitLab - Get MR Diff:**

```python
# Make API call to GitLab
GET https://gitlab.com/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes
```

### Step 2: Extract diff/code changes

### Step 3, 4: Ref external knowledge and send to LLM for review

```python
prompt = f"""
Review this code change:

File: {file.name}

Changes:
{file.diff}

Follow these criteria:
{criteria}
"""
```

### Step 5, 6: Format response and post back

## Testing Options

### Mock request

### VS Code Port Forwarding (Easiest)
1. Server is running on port 8000
2. In VS Code: Ctrl+Shift+P → "Ports: Forward a Port" → Enter 8000
3. VS Code gives you a public URL like https://xxx.devtunnels.ms
4. Use that URL in GitHub webhook settings

### ngrok (More Reliable)

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Run ngrok
ngrok http 8000
```

### Cloudflare Tunnel (Free & Stable)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Run tunnel
./cloudflared tunnel --url http://localhost:8000
```

## VCS API

### GitHub API

#### Get PR Files/Diff:
- **Endpoint**: `GET /repos/{owner}/{repo}/pulls/{pull_number}/files`
- **Auth**: Bearer token in header: `Authorization: Bearer <token>`
- **Parameters**: `owner`, `repo`, `pull_number`, optional `page`, `per_page`
- **Response**: Array of file objects with `filename`, `status`, `additions`, `deletions`, `patch`

#### Post Comment:
- **Endpoint**: `POST /repos/{owner}/{repo}/issues/{issue_number}/comments` (PRs are issues)
- **Auth**: Bearer token
- **Body**: `{"body": "comment text"}`

### GitLab API

#### Get MR Diff:
- **Endpoint**: `GET /projects/{id}/merge_requests/{merge_request_iid}/diffs` (newer)
- **Alt Endpoint**: `GET /projects/{id}/merge_requests/{merge_request_iid}/changes` (deprecated)
- **Auth**: Private token in header: `PRIVATE-TOKEN: <token>`
- **Parameters**: `id` (project), `merge_request_iid`, optional `page`, `per_page`
- **Response**: Array with `old_path`, `new_path`, `diff`, `new_file`, `deleted_file`, etc.

#### Post Comment:
- **Endpoint**: `POST /projects/{id}/merge_requests/{merge_request_iid}/notes`
- **Auth**: Private token
- **Body**: `{"body": "comment text"}`

### Key Differences

- **Authentication**: GitHub uses Bearer tokens, GitLab uses Private tokens
- **Parameters**: GitHub uses `owner/repo + pr_number`, GitLab uses `project_id + mr_iid`
- **Response Format**: Different field names but similar structure

## VCS Webhooks

### [GitHub Webhook](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks)

1. Configure GitHub webhook on your repo:
- Go to repo → Settings → Webhooks → Add webhook
- **Payload URL**: Your forwarded URL + `/webhooks/github/` (For example: `https://t1rp9w5h-8000.asse.devtunnels.ms/webhooks/github/`)
- **Content type**: Select `application/json`
- **Secret**: (optional, match `GITHUB_WEBHOOK_SECRET`)
- **Events**: Select "Let me select individual events" → check "Pull requests"
- **Add webhook**

2. Create a test PR
- Receive the `pull_request` event with action `opened`
- Fetch the diff via GitHub API
- Run the LangChain review agent
- Post a comment back on the PR

### [GitLab Webhook](https://docs.gitlab.com/user/project/integrations/webhooks/)

1. Configure GitLab webhook on your project:
- Go to project → Settings → Webhooks → Add new webhook
- **URL**: Your forwarded URL + `/webhooks/gitlab/`
- **Secret token**: (optional, match `GITLAB_WEBHOOK_TOKEN`, sent as `X-Gitlab-Token` header)
- **Trigger**: Check "Merge request events"

2. Create a test MR
- Receive the `Merge Request Hook` event with action `open`
- Fetch the diff via GitLab API
- Run the LangChain review agent
- Post a comment back on the MR

## Authentication

### GitHub Personal Access Token

1. **Navigate to**: GitHub.com → Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Click**: "Generate new token (classic)"
3. **Configure**:
   - **Note**: `reviewbot-token` (descriptive name)
   - **Expiration**: 30-90 days (recommended)
   - **Scopes**: ✅ `repo` (full repository access)
4. **Copy token**: Starts with `ghp_...` (save securely!)

### GitLab Personal Access Token

1. **Navigate to**: GitLab.com → Avatar → Edit profile → Personal access tokens
2. **Click**: "Add new token"
3. **Configure**:
   - **Token name**: `reviewbot-token`
   - **Expiration date**: Max 365 days (400 days in GitLab 17.6+)
   - **Scopes**: ✅ `api` (full API access)
4. **Copy token**: Starts with `glpat-...` (save securely!)

### Security Best Practices

- **Never commit tokens** to version control
- **Use environment variables**: `GITHUB_TOKEN=ghp_...`, `GITLAB_TOKEN=glpat_...`
- **Store in `.env` file** for local development
- **Set appropriate expiration dates** and rotate regularly

## Payload

- GitLab payload example:

```json
{
    "object_kind": "merge_request",
    "event_type": "merge_request",
    "user": {
        "id": 1,
        "name": "Administrator",
        "username": "root",
        "avatar_url": "http://www.gravatar.com/avatar/avatar.png",
        "email": "admin@example.com"
    },
    "project": {
        "id": 1,
        "name": "Gitlab Test",
        "description": "Awesome project description",
        "web_url": "http://example.com/gitlabhq/gitlab-test",
        "git_ssh_url": "git@example.com:gitlabhq/gitlab-test.git",
        "git_http_url": "http://example.com/gitlabhq/gitlab-test.git",
        "namespace": "GitlabHQ",
        "path_with_namespace": "gitlabhq/gitlab-test",
        "default_branch": "master"
    },
    "object_attributes": {
        "id": 99,
        "iid": 1,
        "title": "MS-Viewport",
        "description": "Fix viewport issues on mobile",
        "state": "opened",
        "target_branch": "master",
        "source_branch": "ms-viewport",
        "author_id": 51,
        "created_at": "2013-12-03T17:23:34Z",
        "updated_at": "2013-12-03T17:23:34Z",
        "url": "http://example.com/diaspora/merge_requests/1",
        "action": "open"
    }
}
```

- Github payload example:

```json
{
    "action": "opened",
    "number": 123,
    "pull_request": {
        "id": 456789,
        "number": 123,
        "title": "Fix critical bug",
        "body": "This fixes the authentication issue",
        "user": {
            "id": 12345,
            "login": "developer123",
            "avatar_url": "https://github.com/avatar.png",
            "type": "User"
        },
        "state": "open",
        "head": {
            "label": "developer123:fix-auth",
            "ref": "fix-auth",
            "sha": "abc123def456",
            "repo": {
                "id": 987654,
                "name": "awesome-app",
                "full_name": "company/awesome-app",
                "owner": {
                    "id": 12345,
                    "login": "developer123",
                    "avatar_url": "https://github.com/avatar.png",
                    "type": "User"
                },
                "private": False,
                "html_url": "https://github.com/company/awesome-app",
                "clone_url": "https://github.com/company/awesome-app.git",
                "ssh_url": "git@github.com:company/awesome-app.git",
                "default_branch": "main"
            }
        },
        "base": {
            "label": "company:main",
            "ref": "main",
            "sha": "def456abc789",
            "repo": {
                "id": 987654,
                "name": "awesome-app",
                "full_name": "company/awesome-app",
                "owner": {
                    "id": 12345,
                    "login": "developer123",
                    "avatar_url": "https://github.com/avatar.png",
                    "type": "User"
                },
                "private": False,
                "html_url": "https://github.com/company/awesome-app",
                "clone_url": "https://github.com/company/awesome-app.git",
                "ssh_url": "git@github.com:company/awesome-app.git",
                "default_branch": "main"
            }
        },
        "created_at": "2023-12-09T10:00:00Z",
        "updated_at": "2023-12-09T10:00:00Z",
        "html_url": "https://github.com/company/awesome-app/pull/123",
        "merged": None
    },
    "repository": {
        "id": 987654,
        "name": "awesome-app",
        "full_name": "company/awesome-app",
        "owner": {
            "id": 12345,
            "login": "developer123",
            "avatar_url": "https://github.com/avatar.png",
            "type": "User"
        },
        "private": False,
        "html_url": "https://github.com/company/awesome-app",
        "clone_url": "https://github.com/company/awesome-app.git",
        "ssh_url": "git@github.com:company/awesome-app.git",
        "default_branch": "main"
    },
    "sender": {
        "id": 12345,
        "login": "developer123",
        "avatar_url": "https://github.com/avatar.png",
        "type": "User"
    }
}
```

## References

https://docs.github.com/en/webhooks/webhook-events-and-payloads

https://docs.gitlab.com/user/project/integrations/webhook_events/

https://github.com/pingdotgg/sample_hooks

https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps

https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28

https://docs.gitlab.com/user/profile/personal_access_tokens/

https://docs.gitlab.com/api/merge_requests/

https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks

https://docs.gitlab.com/user/project/integrations/webhooks/