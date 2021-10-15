from app.core import config
from app.core.templating import Jinja2Templates

TemplateResponse = Jinja2Templates(directory=str(config.TEMPLATE_DIR)).TemplateResponse
