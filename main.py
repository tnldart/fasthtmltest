from fasthtml.common import *
import pathlib
from fastcore.utils import *

app, rt = fast_app(hdrs=(MarkdownJS(),))

@rt("/")
def get():
    fnames = pathlib.Path("content").rglob("*.md")
    # Remove 'content/' from the href
    items = [Li(A(str(fname), href=f"/{fname}")) for fname in fnames]
    return Titled("Reference Documents",
    Ul(*items)
    )

@rt("/content/{fname:path}")
async def get_markdown(request):
    fname = request.path_params['fname']
    file_path = pathlib.Path("content") / fname
    content = file_path.read_text()
    return Titled(fname, Div(content, cls="marked"))

serve()