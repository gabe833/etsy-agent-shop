# Etsy Agent Shop Project

This is a local Python automation project for an Etsy + Printify print-on-demand shop.

## Goal
Build a multi-agent system that:
1. Pulls Printify catalog data.
2. Selects product types.
3. Generates product ideas.
4. Writes Etsy listing drafts.
5. Checks compliance.
6. Creates styled PNG designs.
7. Reviews designs.
8. Uploads approved designs to Printify.
9. Creates Printify products.
10. Eventually monitors orders and drafts customer service replies.

## Current Stack
- Python
- SQLite
- Ollama local models
- Pillow for PNG design rendering
- Printify API
- Local `.env` for secrets

## Important Safety Rules
- Never commit `.env`.
- Never commit API tokens.
- Never commit `venv/`.
- Never publish to Etsy automatically yet.
- Printify product creation is okay only after design_review passes.
- Customer messages and refunds should stay manual for now.

## Current Main Commands
- `python main.py catalog`
- `python main.py pipeline`
- `python approve_item.py`
- `python main.py design`
- `python main.py design_review`
- `python main.py printify`
- `python main.py product_pipeline`

## Next Desired Upgrades
1. Improve design quality beyond basic text.
2. Add better phrase scoring.
3. Add product-specific renderers for shirts, totes, mugs, and sweatshirts.
4. Add automated tests.
5. Improve error handling and database status resets.
6. Add a simple local dashboard eventually.
