FROM python:3.13.1-slim

# install UV
COPY --from=ghcr.io/astral-sh/uv:0.5.23 /uv /bin/uv

# copy files
COPY . /app/

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

CMD ["uv", "run", "main.py"]
