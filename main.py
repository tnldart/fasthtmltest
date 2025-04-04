from fasthtml.common import *
import pathlib
from fastcore.utils import *
import datetime
import json
import os

# Determine if we're in development or production mode
ENV = os.getenv("APP_ENV", "development").lower()
print(f"Running in {ENV} mode")

app, rt = fast_app(hdrs=(MarkdownJS(),))

# JSON file for development mode
FAVORITES_FILE = "favorites.json"

# Database connection pool for production mode
db_pool = None

# Helper functions for development mode (JSON file)
def load_favorites_json():
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_favorites_json(favorites):
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f)

# Initialize for production mode (PostgreSQL)
async def init_db():
    global db_pool
    if ENV != "production":
        print("Development mode: using JSON file for storage")
        return
    
    # Import asyncpg only in production mode
    try:
        import asyncpg
    except ImportError:
        print("Warning: asyncpg module not found. Install with 'pip install asyncpg'")
        print("Falling back to JSON storage")
        return
    
    # Database connection settings
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "markdown_app"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "")
    }
    
    try:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
        # Create tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        print(f"Successfully connected to PostgreSQL database")
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Falling back to JSON storage")

# Unified API for both storage methods
async def save_favorite(filename):
    if ENV == "production" and db_pool is not None:
        # Production mode: PostgreSQL
        async with db_pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO favorites (filename)
                    VALUES ($1)
                    ON CONFLICT (filename)
                    DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                ''', filename)
                return True
            except Exception as e:
                print(f"Error saving favorite: {e}")
                return False
    else:
        # Development mode: JSON file
        favorites = load_favorites_json()
        favorites[filename] = {
            "filename": filename,
            "updated_at": str(datetime.datetime.now())
        }
        save_favorites_json(favorites)
        return True

async def get_favorites():
    if ENV == "production" and db_pool is not None:
        # Production mode: PostgreSQL
        try:
            async with db_pool.acquire() as conn:
                rows = await conn.fetch('SELECT * FROM favorites ORDER BY updated_at DESC')
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return []
    else:
        # Development mode: JSON file
        favorites = load_favorites_json()
        return [
            {
                "filename": key,
                "updated_at": value.get("updated_at", "")
            }
            for key, value in favorites.items()
        ]

async def delete_favorite(filename):
    if ENV == "production" and db_pool is not None:
        # Production mode: PostgreSQL
        try:
            async with db_pool.acquire() as conn:
                await conn.execute('DELETE FROM favorites WHERE filename = $1', filename)
        except Exception as e:
            print(f"Error deleting favorite: {e}")
    else:
        # Development mode: JSON file
        favorites = load_favorites_json()
        if filename in favorites:
            del favorites[filename]
            save_favorites_json(favorites)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    await init_db()

# Shutdown event to close database connections
@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if ENV == "production" and db_pool is not None:
        await db_pool.close()
        print("Database connection pool closed")

@rt("/")
def get():
    fnames = pathlib.Path("content").rglob("*.md")
    items = [Li(A(str(fname), href=f"/{fname}")) for fname in fnames]
    # Add a link to favorites page
    items.append(Li(A("View My Favorites", href="/favorites")))
    # Add indicator of current mode
    mode_indicator = P(f"Running in {ENV} mode", cls=f"mode-{ENV}")
    return Titled("Reference Documents",
        mode_indicator,
        Ul(*items)
    )

@rt("/content/{fname:path}")
async def get_markdown(request):
    fname = request.path_params['fname']
    file_path = pathlib.Path("content") / fname
    
    # Check if file exists
    if not file_path.exists():
        return Titled("Error", P(f"File not found: {fname}"))
    
    content = file_path.read_text()
    # Add a favorite button with HTMX
    favorite_btn = Button(
        "Save as Favorite",
        hx_post=f"/favorite/{fname}",
        hx_swap="outerHTML"
    )
    return Titled(fname,
        Div(content, cls="markdown"),
        Div(favorite_btn, id="favorite-section")
    )

@rt("/favorite/{fname:path}", methods=["POST"])
async def save_favorite_route(request):
    fname = request.path_params['fname']
    # Save using the unified API
    success = await save_favorite(fname)
    # Return a confirmation message
    if success:
        return Div(
            P("Saved to favorites!"),
            id="favorite-section"
        )
    else:
        return Div(
            P("Error saving to favorites!", cls="error"),
            id="favorite-section"
        )

@rt("/favorites")
async def view_favorites(request):
    favorites = await get_favorites()
    if not favorites:
        return Titled("My Favorites",
                     P("You haven't saved any favorites yet."))
    # Create list of favorites with links
    items = []
    for data in favorites:
        fname = data['filename']
        updated_at = data.get('updated_at', "")
        date_display = P(f"Last updated: {updated_at}") if updated_at else ""
        items.append(
            Li(
                A(fname, href=f"/content/{fname}"),
                date_display,
                Button("Remove",
                       hx_delete=f"/favorite/{fname}",
                       hx_target="closest li",
                       hx_swap="outerHTML")
            )
        )
    # Add indicator of current storage mode
    storage_type = "PostgreSQL database" if ENV == "production" and db_pool is not None else "JSON file"
    mode_indicator = P(f"Storing favorites in: {storage_type}", cls=f"mode-{ENV}")
    return Titled("My Favorites",
                 mode_indicator,
                 Ul(*items))

@rt("/favorite/{fname:path}", methods=["DELETE"])
async def delete_favorite_route(request):
    fname = request.path_params['fname']
    # Delete using the unified API
    await delete_favorite(fname)
    # Return empty string to remove the element
    return ""

serve()
