FROM python:3.12-slim

# install UV
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /bin/uv

# copy files
COPY . /app/

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["uv", "run", "main.py"]
