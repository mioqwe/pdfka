# pdfka

Generate branded PDF files and presentations from JSON templates using Jinja2 + Tailwind CSS.

## Features

- **JSON-based page structure** - Define pages with headers and content in simple JSON format
- **Tailwind CSS styling** - Use utility classes for rapid styling
- **Browser preview** - Edit styles and see changes instantly in browser
- **Live reload server** - Auto-refresh browser on file changes
- **Jinja2 templating** - Use variables and logic in your content
- **Dynamic content injection** - Pass company data via CLI arguments
- **A4 Landscape layout** - Wider format perfect for presentations

## Installation

```bash
# Install Python dependencies
pip install weasyprint jinja2

# Or use uv
uv sync

# Install Node.js (for Tailwind CSS) from https://nodejs.org/
# Then install Tailwind:
npm install -D tailwindcss
```

## Quick Start

### 1. Initialize template files

```bash
pdfka init
```

This creates:
- `tailwind.config.js` - Tailwind configuration with custom colors/fonts
- `templates/input.css` - Tailwind directives
- `templates/page_template.html` - HTML template with Tailwind classes

### 2. Build CSS for PDF generation

```bash
pdfka build-css
```

This compiles `templates/tailwind.css` - required for PDF generation.

### 3. Development server with live reload

```bash
pdfka serve
```

Starts a development server at `http://127.0.0.1:5500` that auto-refreshes when you edit:
- Template files (`templates/*.html`)
- Python code (`pdfka/*.py`)

With an input file:
```bash
pdfka serve --input input/example_input.json
```

### 4. Generate preview (browser)

```bash
pdfka preview
```

Open `preview.html` in your browser. Edit `templates/page_template.html` and refresh to see changes.

### 5. Rebuild CSS after changes

```bash
pdfka build-css
```

### 6. Create input JSON

The JSON structure supports a global header/footer and page-specific content:

- **`header`** (optional) - Global header displayed on all pages as "Vidgyk x {header}"
- **`footer`** (optional) - Footer displayed only on the last page
- **Page keys** (`"1"`, `"2"`, etc.) - Each page has:
  - `h1` (required) - Page heading
  - `content` (required) - HTML content
  - `image` (optional) - Path to image file

```json
{
  "header": "{{ cp_name if cp_name else 'Brand Name' }}",
  "footer": "<p>Contact us at info@vidgyk.com</p>",
  "1": {
    "h1": "Welcome to Our Partnership",
    "content": "<p>Welcome to our company with {{ cp_reviews }} reviews!</p>",
    "image": "./images/hero.png"
  },
  "2": {
    "h1": "Our Services",
    "content": "<p>We offer <strong>premium</strong> solutions.</p>"
  }
}
```

### 7. Generate PDF

```bash
pdfka generate input.json --cp-name "My Company" --cp-rating 4.8 --cp-reviews 1500
```

PDF saved to: `./output/offer_My_Company.pdf`

## Workflow

```bash
# First time setup
pdfka init
npm install -D tailwindcss

# Development loop (recommended)
pdfka serve --input input.json   # Live reload server
pdfka build-css --watch          # Auto-rebuild CSS (separate terminal)

# Or step by step
pdfka preview                    # Generate preview HTML
pdfka build-css                  # Compile CSS after changes
pdfka generate input.json ...    # Generate PDF
```

## Tailwind Classes Available

The template uses custom Tailwind classes optimized for print:

### Custom Font Sizes
- `text-print-xs` (12px)
- `text-print-sm` (14px)
- `text-print-base` (16px)
- `text-print-lg` (20px)
- `text-print-xl` (24px)
- `text-print-2xl` (32px)

### Custom Colors
- `bg-brand-50`, `text-brand-500`, `border-brand-900`
- Standard Tailwind colors: `bg-gray-100`, `text-blue-600`, etc.

### Page Layout
- `pdf-page` - Main page container (297mm × 210mm)
- `page-break` - Force page break
- `page-break-avoid` - Avoid page break

### Example Template Structure

```html
<div class="pdf-page">
  <!-- Header -->
  <div class="border-b-4 border-brand-500 pb-4 mb-8">
    <h1 class="text-print-2xl font-bold text-brand-900">{{ header }}</h1>
  </div>
  
  <!-- Content -->
  <div class="text-print-base text-gray-700 leading-relaxed space-y-4">
    {{ content }}
  </div>

  <!-- Company Info -->
  <div class="mt-8 bg-brand-50 border-l-4 border-brand-500 p-5 rounded-r-lg">
    <h3 class="text-print-lg font-semibold text-brand-600">{{ cp_name }}</h3>
    <p class="text-amber-500">★★★★★ {{ cp_rating }}/5.0</p>
  </div>

  <!-- Footer -->
  <div class="absolute bottom-[20mm] left-[20mm] right-[20mm] text-center text-print-xs text-gray-500">
    Page {{ page_num }}
  </div>
</div>
```

## CLI Commands

```bash
pdfka <command> [OPTIONS]
```

| Command | Description |
|---------|-------------|
| `init` | Create template and config files |
| `serve` | Development server with live reload |
| `build-css` | Compile Tailwind CSS for PDF |
| `preview` | Generate HTML preview for browser |
| `generate` | Generate PDF from JSON |

### Init Command

```bash
pdfka init [--output-dir templates]
```

Creates:
- `tailwind.config.js`
- `templates/input.css`
- `templates/page_template.html`

### Serve Command

```bash
pdfka serve [OPTIONS]
```

Start a development server with live reload.

| Option | Default | Description |
|--------|---------|-------------|
| `--input`, `-i` | None | Input JSON file to preview |
| `--port`, `-p` | `5500` | Server port |
| `--host` | `127.0.0.1` | Host to bind |
| `--no-browser` | - | Don't open browser |
| `--template` | - | Custom template path |

**Examples:**
```bash
# Serve default preview
pdfka serve

# Serve with input file (auto-regenerate on JSON changes)
pdfka serve --input input/example_input.json --port 3000

# Serve without opening browser
pdfka serve --no-browser
```

### Build-CSS Command

```bash
pdfka build-css [--watch]
```

Compiles `templates/tailwind.css` from `templates/input.css`.
Use `--watch` for auto-rebuild during development.

### Preview Command

```bash
pdfka preview [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output` | `./preview.html` | Output HTML path |
| `--header` | `"Sample Company"` | Sample header |
| `--content` | Sample paragraphs | Sample content (HTML) |
| `--cp-name` | `"Sample"` | Sample company name |
| `--cp-rating` | `4.8` | Sample rating |
| `--cp-reviews` | `1500` | Sample reviews |

### Generate Command

```bash
pdfka generate input.json [OPTIONS]
# or shorthand:
pdfka input.json --cp-name "Company"
```

| Option | Description |
|--------|-------------|
| `input_file` | Path to JSON file (required) |
| `--cp-name` | Company name |
| `--cp-rating` | Company rating |
| `--cp-reviews` | Number of reviews |
| `--cp-country-code` | Country code |
| `--output` | Output PDF path |
| `--max-chars` | Max chars per page (default: 4000) |
| `--max-words` | Max words per page (default: 600) |
| `--template` | Custom template path |

## JSON Structure

```json
{
  "header": "Global Brand Name",
  "footer": "<p>Contact information</p>",
  "1": {
    "h1": "Page 1 Title",
    "content": "<p>HTML content with {{ variables }}</p>",
    "image": "./images/page1.png"
  },
  "2": {
    "h1": "Page 2 Title",
    "content": "<ul><li>Item 1</li><li>Item 2</li></ul>"
  }
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `header` | No | Global header, displayed as "Vidgyk x {header}" on all pages |
| `footer` | No | Footer HTML, displayed only on the last page |
| `1`, `2`, ... | Yes | Page objects with numeric keys starting from 1 |

### Page Object Fields

| Field | Required | Description |
|-------|----------|-------------|
| `h1` | Yes | Page heading |
| `content` | Yes | HTML content for the page |
| `image` | No | Path to image file (optional) |

### Available Variables

| Variable | Source |
|----------|--------|
| `{{ global_header }}` | JSON "header" field (global) |
| `{{ global_footer }}` | JSON "footer" field (global, last page only) |
| `{{ h1 }}` | Page "h1" field |
| `{{ content }}` | Page "content" field |
| `{{ image }}` | Page "image" field (optional) |
| `{{ is_last_page }}` | Boolean, true on last page |
| `{{ page_num }}` | Current page number |
| `{{ total_pages }}` | Total number of pages |
| `{{ cp_name }}` | CLI `--cp-name` |
| `{{ cp_rating }}` | CLI `--cp-rating` |
| `{{ cp_reviews }}` | CLI `--cp-reviews` |

## Customizing Styles

Edit `templates/page_template.html` and use any Tailwind classes:

```html
<!-- Change header color -->
<h1 class="text-print-2xl font-bold text-red-600">

<!-- Add background -->
<div class="bg-gradient-to-r from-blue-500 to-purple-600">

<!-- Change spacing -->
<div class="p-10 mt-12 mb-8">

<!-- Flexbox layout -->
<div class="flex justify-between items-center">
```

After editing, rebuild CSS:
```bash
pdfka build-css
```

## Project Structure

```
.
├── pdfka/                      # Python package
│   ├── cli.py
│   ├── pdf_generator.py
│   ├── template.py
│   └── ...
├── templates/
│   ├── input.css              # Tailwind source
│   ├── tailwind.css           # Compiled CSS (generated)
│   └── page_template.html     # HTML template
├── tailwind.config.js         # Tailwind config
├── preview.html               # Browser preview (generated)
├── output/                    # Generated PDFs
└── package.json               # Node dependencies
```

## Troubleshooting

### PDF has no styles
Run `pdfka build-css` to compile Tailwind CSS.

### Tailwind classes not working in PDF
The PDF generator uses the compiled `templates/tailwind.css`. Make sure to rebuild after template changes.

### Watch mode not working
Use `pdfka build-css --watch` in a separate terminal while editing the template.

Or use `pdfka serve` which has built-in live reload for browser preview.

## Dependencies

- **Python**: weasyprint, jinja2
- **Node.js**: tailwindcss

## License

MIT
