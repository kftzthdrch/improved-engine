from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=["ui"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ui", "templates")
templates = Jinja2Templates(directory=_templates_dir)

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")
