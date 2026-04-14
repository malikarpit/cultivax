module.exports = {
  stylesheet: [],
  css: `
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 11pt; color: #1a1a2e; line-height: 1.6; }
    h1 { color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 8px; page-break-after: avoid; }
    h2 { color: #0f3460; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-top: 2em; page-break-after: avoid; }
    h3 { color: #533483; page-break-after: avoid; }
    h4 { color: #e94560; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
    th { background: #0f3460; color: white; padding: 8px 12px; text-align: left; }
    td { border: 1px solid #e2e8f0; padding: 6px 12px; }
    tr:nth-child(even) { background: #f8fafc; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 10pt; }
    pre { background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 9.5pt; }
    pre code { background: none; color: inherit; }
    blockquote { border-left: 4px solid #0f3460; margin: 1em 0; padding: 0.5em 1em; background: #f0f4ff; }
    hr { border: none; border-top: 2px solid #e2e8f0; margin: 2em 0; }
    .mermaid { text-align: center; margin: 1.5em 0; }
    img { max-width: 100%; }
    @page { margin: 2cm; }
    @page:first { margin-top: 3cm; }
  `,
  body_class: [],
  marked_options: {},
  pdf_options: {
    format: 'A4',
    margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:8pt;color:#999;width:100%;text-align:center;padding:5px;">CultivaX — User Manual v3.0</div>',
    footerTemplate: '<div style="font-size:8pt;color:#999;width:100%;text-align:center;padding:5px;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
  },
  document_title: 'CultivaX User Manual',
  launch_options: { headless: 'new' },
  script: [
    { url: 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js' },
  ],
};
