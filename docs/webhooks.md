## Workflow

1. Parse webhook
2. Extract diff/code changes
3. Apply review criteria
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
- Mock
- ngrok
- VS Code Port Forwarding
- Cloudflare Tunnel
- VM

## API Reference

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
