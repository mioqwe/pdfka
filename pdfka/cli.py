import argparse
import json
import os
import subprocess
import sys
import webbrowser
from typing import Optional

from pdfka.pdf_generator import PDFGenerator, _get_project_root
from pdfka.template import TemplateContext

# Import livereload conditionally (only when serve command is used)
livereload = None


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate branding PDF from JSON template"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate PDF from JSON")
    gen_parser.add_argument("input_file", help="Path to input JSON file")
    gen_parser.add_argument(
        "--template", type=str, default=None, help="Path to custom HTML template"
    )
    _add_common_args(gen_parser)

    # Preview command
    preview_parser = subparsers.add_parser(
        "preview", help="Generate HTML preview for browser editing"
    )
    preview_parser.add_argument(
        "--output", type=str, default=None, help="Output HTML file path"
    )
    preview_parser.add_argument(
        "--header", type=str, default="Sample Company Name", help="Sample header text"
    )
    preview_parser.add_argument(
        "--content", type=str, default=None, help="Sample content (HTML)"
    )
    preview_parser.add_argument(
        "--name", type=str, default="Sample Company", help="Sample company name"
    )
    preview_parser.add_argument(
        "--rating", type=float, default=4.8, help="Sample rating"
    )
    preview_parser.add_argument(
        "--reviews", type=int, default=1500, help="Sample reviews count"
    )
    preview_parser.add_argument(
        "--template", type=str, default=None, help="Path to custom HTML template"
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Create template files for customization"
    )
    init_parser.add_argument(
        "--output-dir",
        type=str,
        default="templates",
        help="Output directory for templates",
    )

    # Build-css command
    build_parser = subparsers.add_parser(
        "build-css", help="Compile Tailwind CSS for PDF generation"
    )
    build_parser.add_argument(
        "--watch", action="store_true", help="Watch for changes and rebuild"
    )

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve", help="Start development server with live reload"
    )
    serve_parser.add_argument(
        "--input", "-i", type=str, help="Input JSON file to preview (optional)"
    )
    serve_parser.add_argument(
        "--port", "-p", type=int, default=5500, help="Port to serve on (default: 5500)"
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )
    serve_parser.add_argument(
        "--template", type=str, default=None, help="Path to custom HTML template"
    )

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser."""
    parser.add_argument("--country-code", type=str, default=None, help="Country code")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument(
        "--max-chars", type=int, default=None, help="Maximum characters per page"
    )
    parser.add_argument(
        "--max-words", type=int, default=None, help="Maximum words per page"
    )
    parser.add_argument("--name", type=str, default=None, help="Company name")
    parser.add_argument("--rating", type=float, default=None, help="Company rating")
    parser.add_argument("--reviews", type=int, default=None, help="Number of reviews")


def cmd_generate(args) -> None:
    """Generate PDF from JSON."""
    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    context = TemplateContext(
        name=args.name,
        rating=args.rating,
        reviews=args.reviews,
        country_code=args.country_code,
    )

    generator = PDFGenerator(template_path=args.template)

    if args.max_chars or args.max_words:
        from pdfka.config import OverflowConfig

        generator.overflow_config = OverflowConfig(
            max_characters=args.max_chars or generator.overflow_config.max_characters,
            max_words=args.max_words or generator.overflow_config.max_words,
        )

    try:
        output_path, output_name = generator.generate_pdf(
            json_data, context, args.output
        )
        print(f"PDF generated: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_preview(args) -> None:
    """Generate HTML preview file."""
    context = TemplateContext(
        name=args.name,
        rating=args.rating,
        reviews=args.reviews,
    )

    default_content = """
    <p>Welcome to our company. We are proud to serve you with the best products and services available in the market.
    Our team is dedicated to excellence and customer satisfaction.</p>
    <p>With over <strong>1500 reviews</strong> and an average rating of <strong>4.8/5.0</strong>, we have earned the trust
    of thousands of customers worldwide. Our commitment to quality and innovation sets us apart from the competition.</p>
    <p>We constantly strive to improve and adapt to meet the changing needs of our clients. Choose us for your next project
    and experience the difference that expertise and dedication can make.</p>
    """

    content = args.content or default_content

    generator = PDFGenerator(template_path=args.template)

    output_path = args.output or os.path.join(_get_project_root(), "preview.html")

    try:
        generator.save_preview(
            output_path=output_path,
            h1=args.header,
            content=content,
            context=context,
        )
        print(f"Preview HTML saved: {output_path}")
        print(f"Open this file in your browser to edit styles.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _find_tailwind_exe(project_root: str):
    """Find the tailwindcss executable path."""
    # Check local node_modules .bin
    local_bin = os.path.join(project_root, "node_modules", ".bin", "tailwindcss")
    if os.path.exists(local_bin):
        return local_bin

    # Check Windows .bin
    win_bin = os.path.join(project_root, "node_modules", ".bin", "tailwindcss.cmd")
    if os.path.exists(win_bin):
        return win_bin

    return None


def cmd_build_css(args) -> None:
    """Compile Tailwind CSS."""
    project_root = _get_project_root()

    # Check if tailwind.config.js exists
    config_path = os.path.join(project_root, "tailwind.config.js")
    if not os.path.exists(config_path):
        print("Error: tailwind.config.js not found.", file=sys.stderr)
        print("Run 'pdfka init' first.", file=sys.stderr)
        sys.exit(1)

    input_css = os.path.join(project_root, "templates", "input.css")
    output_css = os.path.join(project_root, "templates", "tailwind.css")

    # Find tailwind executable
    tailwind_exe = _find_tailwind_exe(project_root)

    if tailwind_exe:
        cmd = [tailwind_exe, "-i", input_css, "-o", output_css]
    else:
        # Try using npx with node
        cmd = [
            "node",
            "./node_modules/tailwindcss/lib/cli.js",
            "-i",
            input_css,
            "-o",
            output_css,
        ]

    if args.watch:
        cmd.append("--watch")
    else:
        cmd.append("--minify")

    print(f"Building Tailwind CSS...")
    print(f"  Input:  {input_css}")
    print(f"  Output: {output_css}")

    try:
        result = subprocess.run(
            cmd, cwd=project_root, check=True, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        print(f"✓ CSS compiled successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to compile CSS", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        print(f"\nTry reinstalling:", file=sys.stderr)
        print(f"  rm -rf node_modules package-lock.json", file=sys.stderr)
        print(f"  npm install -D tailwindcss", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: Command not found - {e}", file=sys.stderr)
        print(f"\nMake sure you have Node.js installed:", file=sys.stderr)
        print(f"  node --version", file=sys.stderr)
        print(f"\nThen install Tailwind:", file=sys.stderr)
        print(f"  npm install -D tailwindcss", file=sys.stderr)
        sys.exit(1)


TAILWIND_CONFIG = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'print-xs': ['12px', { lineHeight: '1.4' }],
        'print-sm': ['14px', { lineHeight: '1.5' }],
        'print-base': ['16px', { lineHeight: '1.6' }],
        'print-lg': ['20px', { lineHeight: '1.4' }],
        'print-xl': ['24px', { lineHeight: '1.3' }],
        'print-2xl': ['32px', { lineHeight: '1.2' }],
      },
      colors: {
        brand: {
          50: '#ebf8ff',
          100: '#bee3f8',
          500: '#3182ce',
          600: '#2b6cb0',
          700: '#2c5282',
          900: '#1a365d',
        },
      },
    },
  },
  plugins: [],
}
"""

INPUT_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;

/* Inter Font for PDF */
@layer base {
  @font-face {
    font-family: 'Inter';
    src: url('../fonts/Inter/web/Inter-Regular.woff2') format('woff2');
    font-weight: 400;
    font-style: normal;
  }
  @font-face {
    font-family: 'Inter';
    src: url('../fonts/Inter/web/Inter-Medium.woff2') format('woff2');
    font-weight: 500;
    font-style: normal;
  }
  @font-face {
    font-family: 'Inter';
    src: url('../fonts/Inter/web/Inter-SemiBold.woff2') format('woff2');
    font-weight: 600;
    font-style: normal;
  }
  @font-face {
    font-family: 'Inter';
    src: url('../fonts/Inter/web/Inter-Bold.woff2') format('woff2');
    font-weight: 700;
    font-style: normal;
  }
}

@layer base {
  @page {
    size: 297mm 210mm;
    margin: 0;
  }

  * { box-sizing: border-box; }

  body { margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
}

@layer components {
  .pdf-page {
    @apply w-[297mm] h-[210mm] p-[20mm] relative overflow-hidden bg-white;
    page-break-after: always;
  }

  .pdf-page:last-child {
    page-break-after: avoid;
  }
}

@layer utilities {
  .page-break { page-break-after: always; }
  .page-break-avoid { page-break-after: avoid; }
}
"""


def cmd_init(args) -> None:
    """Create template files for customization."""
    project_root = _get_project_root()
    output_dir = os.path.join(project_root, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Create package.json if not exists
    package_json_path = os.path.join(project_root, "package.json")
    if not os.path.exists(package_json_path):
        package_json = '{"name": "pdfka-project", "version": "1.0.0", "private": true}'
        with open(package_json_path, "w", encoding="utf-8") as f:
            f.write(package_json)
        print(f"Created: {package_json_path}")

    # Create Tailwind config
    config_path = os.path.join(project_root, "tailwind.config.js")
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(TAILWIND_CONFIG)
        print(f"Created: {config_path}")
    else:
        print(f"Exists: {config_path}")

    # Create input.css
    input_css_path = os.path.join(output_dir, "input.css")
    if not os.path.exists(input_css_path):
        with open(input_css_path, "w", encoding="utf-8") as f:
            f.write(INPUT_CSS)
        print(f"Created: {input_css_path}")
    else:
        print(f"Exists: {input_css_path}")

    # Create HTML template
    template_path = os.path.join(output_dir, "page_template.html")
    if not os.path.exists(template_path):
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(get_tailwind_template())
        print(f"Created: {template_path}")
    else:
        print(f"Exists: {template_path}")

    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Install Tailwind CSS:")
    print("   npm install -D tailwindcss")
    print("\n2. Build the CSS for PDF generation:")
    print("   pdfka build-css")
    print("\n3. Generate a preview (uses CDN, no build needed):")
    print("   pdfka preview")
    print("\n4. Generate PDF:")
    print("   pdfka generate input.json --cp-name 'Company')")


def get_tailwind_template() -> str:
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ header }}</title>
    <!-- Tailwind CDN for browser preview -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    },
                    fontSize: {
                        'print-xs': ['12px', { lineHeight: '1.4' }],
                        'print-sm': ['14px', { lineHeight: '1.5' }],
                        'print-base': ['16px', { lineHeight: '1.6' }],
                        'print-lg': ['20px', { lineHeight: '1.4' }],
                        'print-xl': ['24px', { lineHeight: '1.3' }],
                        'print-2xl': ['32px', { lineHeight: '1.2' }],
                    },
                    colors: {
                        brand: {
                            50: '#ebf8ff',
                            100: '#bee3f8',
                            500: '#3182ce',
                            600: '#2b6cb0',
                            700: '#2c5282',
                            900: '#1a365d',
                        },
                    }
                }
            }
        }
    </script>
    <!-- Inter Font -->
    <style>
        @font-face {
            font-family: 'Inter';
            src: url('/fonts/Inter/web/Inter-Regular.woff2') format('woff2');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }
        @font-face {
            font-family: 'Inter';
            src: url('/fonts/Inter/web/Inter-Medium.woff2') format('woff2');
            font-weight: 500;
            font-style: normal;
            font-display: swap;
        }
        @font-face {
            font-family: 'Inter';
            src: url('/fonts/Inter/web/Inter-SemiBold.woff2') format('woff2');
            font-weight: 600;
            font-style: normal;
            font-display: swap;
        }
        @font-face {
            font-family: 'Inter';
            src: url('/fonts/Inter/web/Inter-Bold.woff2') format('woff2');
            font-weight: 700;
            font-style: normal;
            font-display: swap;
        }
    </style>
    <style type="text/tailwindcss">
        @layer base {
            @page {
                size: 297mm 210mm;
                margin: 0;
            }
            * { box-sizing: border-box; }
            body { margin: 0; padding: 0; }
        }

        @layer components {
            .pdf-page {
                @apply w-[297mm] h-[210mm] p-[20mm] relative overflow-hidden bg-white;
                page-break-after: always;
            }
            .pdf-page:last-child {
                page-break-after: avoid;
            }
        }

        @layer utilities {
            .page-break { page-break-after: always; }
            .page-break-avoid { page-break-after: avoid; }
        }
    </style>
    <style>
        /* Browser preview styles */
        @media screen {
            body { background: white; padding: 2rem; }
            .pdf-page { margin: 0 auto 2rem auto; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); }
        }
    </style>
</head>
<body class="font-sans bg-white">
    <div class="pdf-page">
        <!-- Header -->
        <div class="border-b-4 border-brand-500 pb-4 mb-8">
            <h1 class="text-print-2xl font-bold text-brand-900">{{ header }}</h1>
        </div>

        <!-- Content -->
        <div class="text-print-base text-black leading-relaxed space-y-4">
            {{ content }}
        </div>

        <!-- Warning -->
        {% if warning %}
        <div class="mt-6 bg-orange-50 border border-orange-400 text-orange-700 px-4 py-3 rounded text-print-sm">
            {{ warning }}
        </div>
        {% endif %}

        <!-- Footer -->
        <div class="absolute bottom-[20mm] left-[20mm] right-[20mm] border-t border-black pt-4 text-center text-print-xs text-black">
            {% if name %}{{ name }} - {% endif %}Page {{ page_num }}
        </div>
    </div>
</body>
</html>"""


def main() -> None:
    # Check if first argument is a file (backward compatibility)
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        # Old style: pdfka input.json --cp-name "Company"
        parser = argparse.ArgumentParser(
            description="Generate branding PDF from JSON template"
        )
        parser.add_argument("input_file", help="Path to input JSON file")
        _add_common_args(parser)
        args = parser.parse_args()
        cmd_generate(args)
        return

    # New style with subcommands
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "preview":
        cmd_preview(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "build-css":
        cmd_build_css(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "serve":
        cmd_serve(args)
    else:
        parser.print_help()


def cmd_serve(args) -> None:
    """Start development server with live reload."""
    import uvicorn
    from pdfka.live_server import app, start_file_watcher

    project_root = _get_project_root()

    url = f"http://{args.host}:{args.port}"
    preview_url = f"{url}/live_preview"

    print(f"=" * 50)
    print(f"Starting live preview server...")
    print(f"URL: {preview_url}")
    print(f"=" * 50)
    print()
    print("Watching for changes in:")
    print(f"  - Templates: {project_root}/templates/")
    if args.input:
        print(f"  - Input: {args.input}")
    print(f"  - Python: {project_root}/pdfka/")
    print()
    print("Press Ctrl+C to stop")
    print()

    if not args.no_browser:
        webbrowser.open(preview_url)

    watcher = start_file_watcher(args.input)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
