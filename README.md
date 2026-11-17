# Renaissance Labs · Learn

Films and lessons on how language models are trained and how human minds work. Static site, built with plain Python.

```
content/lessons/*.md     written lessons (front matter + light Markdown; format in content/BRIEF.md)
content/films/*.json     catalogue entry per film (title, chapters, takeaways, sources)
data/transcripts/        scene starts and timed narration lines, from the film sources (tools/ingest_films.py)
data/site.json           media base URL for the video files
tools/build.py           generates the site into the repo root
tools/make_og.py         renders social preview images with headless Chrome
tools/serve.py           local preview server with Range support (video seeking)
```

```bash
python3 tools/ingest_films.py     # needs the film folders next to this repo; links media/<id>.mp4 for local preview
python3 tools/build.py
python3 tools/make_og.py          # optional, resumable
python3 tools/serve.py 8791       # http://localhost:8791
```

Videos are not stored in this repository (about 2 GB). The player reads `<media_base>/<film-id>.mp4`; set `media_base` in `data/site.json` to wherever the files are hosted.
