# Vercel deployment checklist

- [ ] Repository root contains `app.py`, `requirements.txt`, `vercel.json`, `templates/`, and `public/static/`.
- [ ] `.venv`, `.env`, and `nearcart.db` are not committed.
- [ ] Set `NEARCART_SECRET` in Vercel Environment Variables.
- [ ] Deploy and verify `/`, `/search?q=charger`, `/stores`, `/retailers`.
- [ ] For persistent inventory, migrate SQLite to hosted Postgres before accepting real retailer updates.

**Demo deployment only:** this package uses `/tmp/nearcart.db` on Vercel. Vercel function storage is ephemeral; edits are not durable or shared between instances.
