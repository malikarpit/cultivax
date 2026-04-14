"""Convert USER_MANUAL.md to USER_MANUAL.html with Mermaid diagram support."""
import re
import markdown

with open("USER_MANUAL.md", "r") as f:
    md = f.read()

# Step 1: Extract Mermaid blocks and replace with placeholders
mermaid_blocks = []
def stash_mermaid(match):
    idx = len(mermaid_blocks)
    mermaid_blocks.append(match.group(1).strip())
    return f"MERMAID_PLACEHOLDER_{idx}_END"

md = re.sub(r"```mermaid\n(.*?)\n```", stash_mermaid, md, flags=re.DOTALL)

# Step 2: Convert MD to HTML
html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])

# Step 3: Restore Mermaid blocks as <pre class="mermaid">
for i, block in enumerate(mermaid_blocks):
    placeholder = f"MERMAID_PLACEHOLDER_{i}_END"
    replacement = f'<pre class="mermaid">\n{block}\n</pre>'
    html_body = html_body.replace(f"<p>{placeholder}</p>", replacement)
    html_body = html_body.replace(placeholder, replacement)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CultivaX — User Manual v3.0</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {
    mermaid.initialize({ startOnLoad: true, theme: "default", securityLevel: "loose" });
});
</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{font-family:"Inter",-apple-system,BlinkMacSystemFont,sans-serif;font-size:11pt;color:#1a1a2e;line-height:1.7;max-width:920px;margin:0 auto;padding:50px 40px;background:#fff}
h1{color:#0f3460;border-bottom:3px solid #0f3460;padding-bottom:12px;margin-top:2.5em;font-size:22pt;font-weight:700}
h2{color:#16213e;border-bottom:2px solid #cbd5e1;padding-bottom:8px;margin-top:2.5em;font-size:16pt;font-weight:600}
h3{color:#533483;margin-top:2em;font-size:13pt;font-weight:600}
h4{color:#e94560;font-size:11pt;font-weight:600}
table{border-collapse:collapse;width:100%;margin:1.2em 0;font-size:10pt;border-radius:6px;overflow:hidden}
th{background:linear-gradient(135deg,#0f3460,#16213e);color:#fff;padding:10px 14px;text-align:left;font-weight:600;border:none}
td{border:1px solid #e2e8f0;padding:8px 14px;vertical-align:top}
tr:nth-child(even){background:#f8fafc}
tr:hover{background:#eef2ff}
code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:10pt;font-family:"JetBrains Mono","Fira Code","Cascadia Code",monospace;color:#e94560}
pre{background:#1e293b;color:#e2e8f0;padding:18px 22px;border-radius:10px;overflow-x:auto;font-size:9.5pt;line-height:1.55;margin:1.2em 0;border:1px solid #334155}
pre code{background:none;color:inherit;padding:0;font-size:inherit}
pre.mermaid{background:#ffffff;color:#333;text-align:center;padding:24px;border:2px solid #e2e8f0;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
blockquote{border-left:4px solid #533483;margin:1.2em 0;padding:14px 22px;background:#faf5ff;border-radius:0 8px 8px 0;font-style:italic}
blockquote strong{color:#533483;font-style:normal}
hr{border:none;border-top:2px solid #e2e8f0;margin:3em 0}
strong{color:#16213e}
a{color:#533483;text-decoration:none;border-bottom:1px dotted #533483}
a:hover{color:#e94560}
em{color:#64748b}

/* Print styles for PDF */
@media print{
    body{max-width:100%;padding:0 20px;font-size:10pt}
    h1,h2,h3{page-break-after:avoid}
    table,pre,.mermaid{page-break-inside:avoid}
    pre.mermaid svg{max-width:100%!important}
    a{color:#333;border:none}
    blockquote{background:#f5f5f5;border-color:#999}
}
</style>
</head>
<body>
""" + html_body + """
</body>
</html>"""

with open("USER_MANUAL.html", "w") as f:
    f.write(html)

print(f"SUCCESS: USER_MANUAL.html created ({len(html)} bytes, {len(mermaid_blocks)} diagrams)")
