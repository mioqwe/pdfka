import os
import re
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import CSS, HTML

from pdfka.config import DEFAULT_OVERFLOW_CONFIG, DEFAULT_PAGE_CONFIG
from pdfka.template import TemplateContext, TemplateRenderer
from pdfka.utils import apply_truncation, count_words, validate_json_structure

# Regex to match body tag with optional attributes
_BODY_START_RE = re.compile(r"<body[^>]*>", re.IGNORECASE)
_BODY_END_RE = re.compile(r"</body>", re.IGNORECASE)


def _get_project_root() -> str:
    """Get the project root directory (parent of pdfka package)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_default_output_path(company_name: Optional[str]) -> str:
    """Generate default output path in project output directory."""
    project_root = _get_project_root()
    output_dir = os.path.join(project_root, "output")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename: offer_{company_name}.pdf
    safe_name = company_name.strip().replace(" ", "_") if company_name else "unknown"
    filename = f"offer_{safe_name}.pdf"

    return os.path.join(output_dir, filename)


def _get_template_dir() -> str:
    """Get the templates directory path."""
    return os.path.join(_get_project_root(), "templates")


def _get_tailwind_css() -> Optional[str]:
    """Load compiled Tailwind CSS if available."""
    css_path = os.path.join(_get_template_dir(), "tailwind.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _prepare_html_for_pdf(html: str) -> str:
    """
    Prepare HTML for PDF generation:
    1. Remove Tailwind CDN script
    2. Inject compiled CSS if available
    3. Remove browser-only styles
    """
    # Remove Tailwind CDN script
    html = re.sub(
        r'<script src="https://cdn\.tailwindcss\.com"></script>',
        "",
        html,
    )

    # Remove the tailwind config script (handle nested braces)
    def remove_tailwind_config(text):
        result = []
        i = 0
        while i < len(text):
            if text[i : i + 7] == "<script":
                script_start = i
                script_end = text.find("</script>", i)
                if script_end != -1:
                    script_content = text[i:script_end]
                    if "tailwind.config" in script_content:
                        i = script_end + len("</script>")
                        continue
                    else:
                        result.append(text[i])
                        i += 1
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    html = remove_tailwind_config(html)

    # Remove style[type="text/tailwindcss"] (browser-only Tailwind directives)
    html = re.sub(
        r'<style type="text/tailwindcss">.*?</style>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Remove @media screen styles (browser preview styles)
    html = re.sub(
        r"<style>\s*/\* Browser preview styles \*/.*?</style>",
        "",
        html,
        flags=re.DOTALL,
    )

    # Inject compiled CSS if available
    tailwind_css = _get_tailwind_css()
    if tailwind_css:
        # Find </head> and insert CSS before it
        css_block = f"<style>{tailwind_css}</style>"
        html = html.replace("</head>", f"{css_block}</head>")

    return html


def _prepare_html_for_preview(html: str) -> str:
    """
    Prepare HTML for live preview to match PDF rendering:
    1. Remove Tailwind CDN script
    2. Remove tailwind.config script
    3. Remove style[type="text/tailwindcss"] (Tailwind directives)
    4. Remove @media screen styles
    5. Inject compiled CSS for accurate preview
    """
    html = _prepare_html_for_pdf(html)
    return html


class PDFGenerator:
    def __init__(self, page_config=None, overflow_config=None, template_path=None):
        self.page_config = page_config or DEFAULT_PAGE_CONFIG
        self.overflow_config = overflow_config or DEFAULT_OVERFLOW_CONFIG
        self.template_renderer = TemplateRenderer()
        self.template_path = template_path or os.path.join(
            _get_template_dir(), "page_template.html"
        )

        # Setup Jinja2 environment for file-based templates
        template_dir = os.path.dirname(self.template_path)
        if os.path.exists(template_dir):
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.env = Environment()

    def _load_template(self) -> Template:
        """Load the HTML template from file."""
        if os.path.exists(self.template_path):
            with open(self.template_path, "r", encoding="utf-8") as f:
                return Template(f.read())
        else:
            # Fallback to default template
            return Template(self._get_default_template())

    def _get_default_template(self) -> str:
        """Default inline template as fallback."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {
                    size: {{ width }} {{ height }};
                    margin: {{ margin_top }} {{ margin_right }} {{ margin_bottom }} {{ margin_left }};
                }
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .page { page-break-after: always; }
                .page:last-child { page-break-after: avoid; }
                .global-header { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
                .h1 { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
                .content { font-size: 14px; }
                .footer { position: absolute; bottom: 20px; width: 100%; text-align: center; }
            </style>
        </head>
        <body>
            <div class="page">
                {% if global_header %}<div class="global-header">Vidgyk x {{ global_header }}</div>{% endif %}
                {% if h1 %}<div class="h1">{{ h1 }}</div>{% endif %}
                <div class="content">{{ content }}</div>
                {% if is_last_page and global_footer %}<div class="footer">{{ global_footer }}</div>{% endif %}
            </div>
        </body>
        </html>
        """

    def render_single_page(
        self,
        h1: str,
        content: str,
        context: TemplateContext,
        page_num: int = 1,
        total_pages: int = 1,
        global_header: str = "",
        global_footer: str = "",
        image: Optional[str] = None,
        warning: Optional[str] = None,
    ) -> str:
        """Render a single page using the template."""
        template = self._load_template()

        return template.render(
            h1=h1,
            content=content,
            image=image,
            warning=warning,
            page_num=page_num,
            total_pages=total_pages,
            global_header=global_header,
            global_footer=global_footer,
            is_last_page=(page_num == total_pages),
            country_code=context.country_code,
            width=self.page_config.width,
            height=self.page_config.height,
            margin_top=self.page_config.margin_top,
            margin_bottom=self.page_config.margin_bottom,
            margin_left=self.page_config.margin_left,
            margin_right=self.page_config.margin_right,
        )

    def generate_html(
        self, rendered_data: Dict[str, Any], context: TemplateContext
    ) -> str:
        """Generate full HTML document with all pages."""
        pages_list = []
        rendered_pages = rendered_data.get("pages", {})
        global_header = rendered_data.get("header", "")
        global_footer = rendered_data.get("footer", "")

        sorted_keys = sorted(
            rendered_pages.keys(), key=lambda x: int(x) if x.isdigit() else x
        )
        total_pages = len(sorted_keys)

        for key in sorted_keys:
            page_data = rendered_pages[key]

            truncated_content, was_truncated = apply_truncation(
                page_data["content"],
                self.overflow_config.max_characters,
                self.overflow_config.max_words,
            )

            warning = None
            if was_truncated:
                char_count = len(page_data["content"])
                warning = self.overflow_config.warning_message.format(
                    page_num=key,
                    char_count=char_count,
                    max_chars=self.overflow_config.max_characters,
                )

            # Render each page individually using the template
            page_html = self.render_single_page(
                h1=page_data.get("h1", ""),
                content=truncated_content,
                context=context,
                page_num=int(key),
                total_pages=total_pages,
                global_header=global_header,
                global_footer=global_footer,
                image=page_data.get("image"),
                warning=warning,
            )
            pages_list.append(page_html)

        # Combine all pages - each page is already a full HTML document,
        # so we extract just the body content and wrap in a single document
        return self._combine_pages(pages_list)

    def _combine_pages(self, page_htmls: List[str]) -> str:
        """Combine multiple page HTMLs into a single document."""
        if not page_htmls:
            return ""

        combined_content = []
        for html in page_htmls:
            # Extract body content using regex (handles attributes on body tag)
            body_start_match = _BODY_START_RE.search(html)
            body_end_match = _BODY_END_RE.search(html)
            if body_start_match and body_end_match:
                content = html[body_start_match.end() : body_end_match.start()]
                combined_content.append(content)

        # Use the first page as base for the combined document
        base_html = page_htmls[0]
        body_start_match = _BODY_START_RE.search(base_html)
        body_end_match = _BODY_END_RE.search(base_html)

        if not body_start_match or not body_end_match:
            # Fallback: return first page if we can't parse it
            return base_html

        combined_body = "\n".join(combined_content)

        return (
            base_html[: body_start_match.start()]
            + "<body>\n"
            + combined_body
            + "\n</body>"
            + base_html[body_end_match.end() :]
        )

    def generate_preview_html(
        self,
        h1: str = "Sample Header",
        content: str = "<p>This is sample content for preview.</p>",
        context: Optional[TemplateContext] = None,
    ) -> str:
        """Generate a preview HTML file for browser viewing."""
        if context is None:
            context = TemplateContext()

        return self.render_single_page(h1, content, context, page_num=1, total_pages=1)

    def save_preview(
        self,
        output_path: str,
        h1: str = "Sample Header",
        content: str = "<p>This is sample content for preview.</p>",
        context: Optional[TemplateContext] = None,
    ) -> str:
        """Save a preview HTML file to disk."""
        html = self.generate_preview_html(h1, content, context)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def generate_full_preview(
        self,
        json_data: Dict[str, Any],
        context: TemplateContext,
    ) -> str:
        """Generate full HTML with all pages for live preview.

        Uses the same CSS as PDF generation for accurate preview.
        """
        validate_json_structure(json_data)

        rendered_pages = self.template_renderer.render_pages(json_data, context)
        global_header = rendered_pages.get("header", "")
        global_footer = rendered_pages.get("footer", "")

        pages_html = []
        sorted_keys = sorted(
            rendered_pages["pages"].keys(), key=lambda x: int(x) if x.isdigit() else x
        )
        total_pages = len(sorted_keys)

        for key in sorted_keys:
            page_data = rendered_pages["pages"][key]
            page_html = self.render_single_page(
                h1=page_data.get("h1", ""),
                content=page_data.get("content", ""),
                context=context,
                page_num=int(key),
                total_pages=total_pages,
                global_header=global_header,
                global_footer=global_footer,
                image=page_data.get("image"),
            )

            pages_html.append(page_html)

        full_html = self._combine_pages(pages_html)
        return _prepare_html_for_preview(full_html)

    def generate_pdf(
        self,
        json_data: Dict[str, Any],
        context: TemplateContext,
        output_path: Optional[str] = None,
    ) -> Tuple[str, str]:
        validate_json_structure(json_data)

        rendered_pages = self.template_renderer.render_pages(json_data, context)
        html_content = self.generate_html(rendered_pages, context)

        # Prepare HTML for PDF (inject compiled CSS, remove CDN)
        html_content = _prepare_html_for_pdf(html_content)

        if output_path is None:
            output_path = _get_default_output_path(None)

        HTML(string=html_content).write_pdf(output_path)

        return output_path, os.path.basename(output_path)
