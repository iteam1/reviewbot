## Roles

**Guest**
- Very limited access (often read-only to issues/discussions, depending on visibility/settings).

**Reporter**
- Can read code and project info.
- Can usually create issues and view CI results, but can’t push code.

**Developer**
- Can contribute code (push to non-protected branches), open MRs, run pipelines.

**Maintainer**
- Can manage settings, members, protections, and generally administer the project.

**Owner** (mainly for Groups, and for personal namespaces)
- Full control, including group-level settings, billing (on paid plans), and high-level admin capabilities.

## Curl

Full:

```bash
source .env

PROJECT_ID=26984
MR_IID=2342

SRC_BRANCH=$(
  curl --silent --show-error \
    --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_API_URL/projects/$PROJECT_ID/merge_requests/$MR_IID" \
  | jq -r '.source_branch'
)

curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/$PROJECT_ID/merge_requests/$MR_IID/changes" \
| jq -r '.changes[].new_path' \
| while IFS= read -r p; do
    [ -z "$p" ] && continue
    enc=$(printf "%s" "$p" | jq -sRr @uri)
    ref=$(printf "%s" "$SRC_BRANCH" | jq -sRr @uri)
    echo "===== FILE: $p ====="
    curl --silent --show-error \
      --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
      "$GITLAB_API_URL/projects/$PROJECT_ID/repository/files/$enc/raw?ref=$ref"
    echo
  done
```

### User

- See whoami

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/user"
```

### Project

Attributes:
- `id`
- `name_with_namespace`
- `default_branch`
- `web_url`

- List projects

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects?membership=true&per_page=10"
```

- Search project by name:

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects?search=<your_project_name>&per_page=10"
```

Example:

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects?search=OPNEXT.DOCUMENT&per_page=10"
```

- List branches

```bash
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/repository/branches?per_page=10"
```

- Pull branch

```bash
git clone --branch "<branch_name>" --single-branch \
  "https://oauth2:${GITLAB_TOKEN}@${GITLAB_HOST}/<namespace>%2F<project>.git" \
  "<path/to/your/folder>"
```

### MR

Attributes

**Identity / references**
- `id`: Global MR id (unique in GitLab instance)
- `iid`: MR number within the project (the `!2327` part)
- `project_id`
- `reference`: like `!2327`
- `references.short`: `!2327`
- `references.relative`: `!2327`
- `references.full`: `GROUP/OPNEXT88/p1/document!2327`
- `web_url`: MR URL in browser

**Content**
- `title`
- `description`
- `labels`: array of strings
- `draft` / `work_in_progress`: WIP state

**State / lifecycle**
- `state`: `opened` / `merged` / `closed`
- `created_at`
- `updated_at`
- `merged_at`: if merged
- `closed_at`: if closed
- `merged_by`, `merge_user`, `closed_by`: user objects (may be `null`)

**Branches / commits**
- `source_branch`
- `target_branch`
- `source_project_id`
- `target_project_id`
- `sha`: HEAD commit SHA of the MR
- `merge_commit_sha`: created when merged (may be `null`)
- `squash_commit_sha`: if squashed (may be `null`)
- `should_remove_source_branch`
- `force_remove_source_branch`

**People**
- `author`: user object
- `assignee`: single user (or `null`)
- `assignees`: array
- `reviewers`: array

**Mergeability / checks**
- `merge_status`: older field (e.g. `can_be_merged`)
- `detailed_merge_status`: more specific mergeability status
- `has_conflicts`
- `blocking_discussions_resolved`
- `merge_when_pipeline_succeeds`
- `merge_after`: often `null`

**Misc**
- `user_notes_count`: number of comments/notes
- `upvotes`, `downvotes`
- `milestone`: object (or `null`)
- `time_stats`: estimate/spent
- `task_completion_status`: checklist progress
- `prepared_at`
- `discussion_locked`
- `imported`, `imported_from`
- `squash`, `squash_on_merge`

- List all Merge Requests of a specific project

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/merge_requests?state=all&per_page=10"
```

Example:
```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/26984/merge_requests?state=all&per_page=10"
```

Useful filters:
- state=opened|merged|closed|all
- source_branch=...
- target_branch=main
- author_username=...

- View a specific Merge Request

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/merge_requests/<mr_iid>"
```

- View MR changes (diff info)
```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/merge_requests/<mr_iid>/changes"
```

- View MR discussions / notes (comments)

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/merge_requests/<mr_iid>/notes?per_page=10"
```

- Get file content:

```bash
curl --silent --show-error \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/repository/files/<urlencoded_file_path>/raw?ref=<ref>"
```

- Post comment:

```bash
curl --silent --show-error \
  --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"body":"<your_comment>"}' \
  "$GITLAB_API_URL/projects/<project_id>/merge_requests/<mr_iid>/notes"
```

Example:

```bash
curl --silent --show-error \
  --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"body":"☃️ Merry Christmas 🎄"}' \
  "$GITLAB_API_URL/projects/26984/merge_requests/2334/notes"
```

### Other

- List pipelines

```bash
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/pipelines?per_page=10"
```

- List jobs for a pipeline:

```bash
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/<project_id>/pipelines/<pipeline_id>/jobs"
```

## What we need to automate/review

- `GITLAB_HOST`

- `GITLAB_BASE_URL="https://${GITLAB_HOST}"`

- `GITLAB_TOKEN`

- `GITLAB_API_URL="${GITLAB_BASE_URL}/api/v4"`

- `project_id` (or alternatively `project_path`)

- `mr_iid` (the MR number inside that project)

- Scopes: `api, read_api, read_repository`

### endpoints

Must have: `.../merge_requests/:iid/changes`

Recommended:

- `.../merge_requests/:iid` (metadata)
- `.../repository/files/...` for any files you comment on (context)
- `.../merge_requests/:iid/notes` (don't duplicate)

For example:

```bash
curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/26984/merge_requests/2327"

curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/26984/merge_requests/2327/changes"

curl --silent --show-error --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_API_URL/projects/26984/merge_requests/2327/notes?per_page=100"
```