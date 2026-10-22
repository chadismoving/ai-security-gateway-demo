# Securing Enterprise AI Applications

A 14-slide Reveal.js presentation for a Solutions Engineer technical interview. The deck runs approximately 14–15 minutes and transitions directly into a 15-minute SecureAI Gateway demo.

## Run locally

From this folder, start any static web server:

```bash
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000).

The deck uses Reveal.js and Highlight.js from jsDelivr, so the browser requires internet access. No build step or package installation is needed.

## Deploy to object storage

Upload the complete folder without changing its structure. Configure the bucket or CDN for static website hosting and use `index.html` as the default document.

- Keep `index.html`, `styles.css`, `presentation.js`, and `assets/` together.
- Serve the site over HTTP or HTTPS rather than opening the HTML as a local file.
- Use the correct content types: HTML, CSS, JavaScript, PNG, and SVG.
- Allow browsers to reach `cdn.jsdelivr.net`, which hosts the Reveal.js dependencies.
- Reveal.js uses URL hashes for slides, so no server-side routing rule is required.

Typical targets include an S3 static website or CloudFront distribution, Azure Static Website, Google Cloud Storage website hosting, or any CDN-backed object store.

## Controls

- `←` / `→` — previous or next slide
- `Space` — next slide
- `F` — fullscreen
- `S` — speaker view with notes
- `O` or `Esc` — overview
- `Home` / `End` — first or last slide

## Files

- `index.html` — all 14 slides and speaker notes
- `styles.css` — custom 16:9 visual system and diagrams
- `presentation.js` — Reveal.js configuration

## Source notes

The customer-chatbot scope example uses the screenshot supplied for this presentation. The July 2026 incident slide is based on the official disclosures from Hugging Face and OpenAI. The Llama Guard role is grounded in Meta’s official Llama Guard publication and Purple Llama repository. Direct links appear in the relevant speaker notes; the incident sources also appear visibly on slide 5.
