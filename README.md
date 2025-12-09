# reviewbot

*A code review agent that can review MRs*

```
┌─────────────┐                ┌──────────────────┐         ┌──────────────┐
│   VSC       │                │  Your Backend    │  API    │ LLM provider │
│             ├---[webhook]--->│  (Flask/FastAPI) ├-------->│     API      │
│  MR Created │                │                  │         │              │
└─────────────┘                │  /webhook        │         └──────────────┘
                               │  endpoint        │
                               │                  │
                               │  1. Parse event  │
                               │  2. Fetch diff   │
┌─────────────┐                │  3. Add criteria │
│   VSV       │                │  4. Call LLM     │
│  MR Comment │<--[comment]----┤  5. Format reply │
└─────────────┘                │  6. Post comment │
                               └──────────────────┘
```

## Features
- Self-hosted
- Support many LLM providers: OpenAI, Claude, non-official providers, etc. (*Can be extended*)
- Support many mainstream VCS: GitHub, GitLab, DevOps, etc. (*Can be extended*)
- Can be integrate external knowledge base.

## Structure

## References