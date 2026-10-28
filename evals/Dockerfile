# Supply reviewed exact CLI versions; no latest-version defaults or embedded credentials.
ARG BASE_IMAGE=public.ecr.aws/docker/library/node:22-bookworm-slim
ARG GRADER_BASE_IMAGE=public.ecr.aws/docker/library/python:3.13-slim-bookworm
FROM ${BASE_IMAGE} AS agent
ARG CODEX_VERSION
ARG CLAUDE_VERSION
RUN for version in "$CODEX_VERSION" "$CLAUDE_VERSION"; do \
      printf '%s\n' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$' || exit 1; \
    done \
    && apt-get update && apt-get install -y --no-install-recommends python3 python3-venv git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/eval-python \
    && /opt/eval-python/bin/pip install --no-cache-dir fastapi==0.162.0 httpx==0.28.1 \
    && npm install --global "@openai/codex@${CODEX_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
    && npm cache clean --force
ENV PATH="/opt/eval-python/bin:${PATH}" \
    DISABLE_UPDATES=1 \
    DISABLE_AUTOUPDATER=1
# The runner sets a non-root UID, fresh HOME and resource limits, and overrides ENTRYPOINT.
USER 1000:1000

# Default grading needs no agent CLI, authentication, Node or Git.
FROM ${GRADER_BASE_IMAGE} AS grader
RUN pip install --no-cache-dir fastapi==0.162.0 httpx==0.28.1
USER 1000:1000
