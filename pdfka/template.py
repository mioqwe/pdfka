from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from jinja2 import Environment, Template


@dataclass
class TemplateContext:
    name: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    country_code: Optional[str] = None
    extra_vars: Optional[Dict[str, Any]] = None


class TemplateRenderer:
    def __init__(self):
        self.env = Environment()

    def render(self, template_content: str, context: TemplateContext) -> str:
        template = self.env.from_string(template_content)

        render_vars = {
            "name": context.name,
            "rating": context.rating,
            "reviews": context.reviews,
            "country_code": context.country_code,
        }

        if context.extra_vars:
            render_vars.update(context.extra_vars)

        return template.render(**render_vars)

    def render_pages(
        self, json_data: Dict[str, Any], context: TemplateContext
    ) -> Dict[str, Any]:
        rendered_data = {}
        rendered_pages = {}

        # Render global header if present
        if "header" in json_data:
            rendered_data["header"] = self.render(json_data["header"], context)

        # Render global footer if present
        if "footer" in json_data:
            rendered_data["footer"] = self.render(json_data["footer"], context)

        # Render each page (numeric keys only)
        for key, page in json_data.items():
            if key.isdigit():
                rendered_h1 = self.render(page.get("h1", ""), context)
                rendered_content = self.render(page["content"], context)
                rendered_image = (
                    self.render(page.get("image", ""), context)
                    if "image" in page
                    else None
                )

                rendered_pages[key] = {
                    "h1": rendered_h1,
                    "content": rendered_content,
                }
                if rendered_image:
                    rendered_pages[key]["image"] = rendered_image

        rendered_data["pages"] = rendered_pages
        return rendered_data
