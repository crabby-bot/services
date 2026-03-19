# How to Add a New Example Page

No code changes needed. Just create a new folder.

## Steps

1. Create a folder in `~/services/web/examples/` named after your project (use hyphens, no spaces):
   ```
   mkdir -p ~/services/web/examples/my-project/img
   ```

2. Create `meta.json` in that folder:
   ```json
   {
     "title": "My Project Name",
     "description": "One or two sentences about what this project is.",
     "tags": ["Small Business", "E-commerce"],
     "thumbnail": "img/hero.jpg",
     "status": "live"
   }
   ```
   Set `"status": "draft"` to hide it from the listing while you work on it.

3. Create `index.html` — a complete, standalone HTML file. Use relative paths for images (e.g. `img/hero.jpg` not `/static/...`).

4. Add any images to `img/` inside the folder.

5. Restart the web service:
   ```
   sudo systemctl restart crabby-web
   ```

The example will automatically appear on `/examples`. That's it.

## What NOT to touch
- `app.py` — never edit this to add examples
- `templates/examples.html` — never hardcode examples here
- Other example folders — each is isolated, you can't break them
