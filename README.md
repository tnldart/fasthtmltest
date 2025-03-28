Test repo to test container and kubernetes pipelines

environment variables set for development or production, by default runs in development and stores preferences in a local file

```
# Set to "development" or "production"
APP_ENV=development

# Only needed for production mode
DB_HOST=localhost
DB_NAME=markdown_app
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

# Build the python app image

```
podman build -t markdown-app .
```

# Build the postgresql image

```
podman build -f Dockerfile-postgresql -t my-postgresql-image .
```

# Run in development mode (using JSON file)

```
podman run -d -p 8000:5001 \
  -v $(pwd)/content:/app/content \
  -v $(pwd)/data:/app/data \
  markdown-app
```

# Run in production mode (Not seriously meant for production)

## Run the database server first

### Run database server

```
podman run -d -p 5432:5432 --name postgres-container \
    -e POSTGRES_DB=markdown_app \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=your_password \
    -v pgdata:/var/lib/postgresql/data \
    -d my-postgresql-image
```

### Run app

```
podman run -d -p 8000:5001 --name markdown-app \
  -v $(pwd)/content:/app/content \
  -e APP_ENV=production \
  -e DB_HOST=host.docker.internal \
  -e DB_NAME=markdown_app \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your_password \
  markdown-app
```
