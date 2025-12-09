# reviewbot

*A code review agent that can review MRs*

```
┌────────────────┐                ┌────────────────────────────┐           ┌──────────────┐
│   VSC          │                │  Your Backend              │           │ LLM provider │
│                ├---[webhook]--->│  (Flask/FastAPI)           ├--[API]--->│     API      │
│  MR/PR Created │                │                            │           │              │
└────────────────┘                │  /webhook                  │           └──────────────┘
                                  │  endpoint                  │
                                  │                            │
                                  │  1. Parse event            │
                                  │  2. Fetch diff             │
┌────────────────┐                │  3. Ref external knowledge │
│   VSC          │                │  4. Call LLM               │
│  MR/PR Comment │<--[comment]----┤  5. Format reply           │
└────────────────┘                │  6. Post comment           │
                                  └────────────────────────────┘
```

## Features
- Self-hosted
- Support many LLM providers: OpenAI, Claude, non-official providers, etc. (*Can be extended*)
- Support many mainstream VCS: GitHub, GitLab, DevOps, etc. (*Can be extended*)
- Can be integrate external knowledge base.

## Structure

```
reviewbot/                 # Project root  
├── src/
│   ├── core/              # Domain logic and shared components
│   ├── vcs/               # All VCS provider integrations isolated
│   ├── llm/               # All LLM provider integrations isolated
│   └── config/            # Configuration management
├── backend/
├── tests/
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── requirements.txt
├── README.md
└── .env.example
└── Makefile                # Development commands
```

## References

https://mypy-lang.org/

https://docs.python.org/3/library/abc.html

https://docs.python.org/3/library/typing.html

https://docs.pydantic.dev/latest/

https://github.com/openai/openai-python

https://github.com/anthropics/anthropic-sdk-python