# CocoCloud Kids Video Factory (free GitHub Actions starter)

This is an importable starter workflow. It does **not** make changes to your GitHub account or repository. You must review the files and explicitly add them to a repository yourself.

## What it does

- Runs manually or every Sunday at 09:00 UTC using GitHub-hosted Actions.
- Reads public RSS feeds (NASA and NOAA) and maps matching stories to kid-friendly themes.
- Falls back to a built-in topic list if feeds are unavailable or no safe match is found.
- Creates an original short rhyme using a reusable template (not an AI language model).
- Downloads the open Piper `en_US-lessac-medium` voice and generates spoken narration.
- Draws a reusable, simple cartoon bus scene with animated motion using Pillow.
- Uses FFmpeg to render an MP4 and adds a very quiet generated tone under the narration.
- Uploads the MP4, poem, topic metadata, and thumbnail as a workflow artifact for 7 days.

## Honest limitations

- This is a **starter**, not Cocomelon-quality 3D animation. The bus is a simple 2D cartoon with lightweight animation, not a 3D model.
- Piper makes spoken narration, not singing.
- The rhyme uses a reusable template and is not written by a cloud AI model. Topic discovery is RSS-based and keyword matching, not trend analytics.
- GitHub Actions is not unlimited free hosting. Free account quotas, runner limits, storage, and artifact retention apply and can change. This workflow is designed to fit a short run, but success is not guaranteed on every account.
- GitHub Actions artifacts expire after 7 days in this workflow. Download the MP4 before expiry. Permanent cloud storage is not included.
- The workflow requires internet access to fetch RSS and the Piper voice. If a feed or voice download fails, the run may fail.
- No paid APIs, subscriptions, or trials are configured. No YouTube upload is performed.
- The Piper voice is hosted in the public `rhasspy/piper-voices` repository. Check the voice model's license and attribution requirements before publishing at scale.
- The generated tone is not a musical composition. Replace it only with audio you have rights to use.

## Setup for a beginner

1. Sign in to GitHub and create a **new repository** named `cococloud-kids-video-factory`. A public repository makes this starter easy to inspect; don't add secrets or private files.
2. On your computer, unzip this package.
3. In the new repository, use **Add file → Upload files** and upload the contents of this folder, including the hidden `.github` folder. Make sure the final path is `.github/workflows/make-video.yml`.
4. Commit the files.
5. Open the repository's **Actions** tab and enable workflows if GitHub asks.
6. Choose **CocoCloud Kids Video Factory** in the left sidebar, click **Run workflow**, leave the topic blank for RSS discovery or enter a topic such as `The Happy Little Bus`, then click **Run workflow**.
7. When the run completes, open the run summary and download the artifact named `cococloud-kids-video-...`.
8. The ZIP artifact contains `cococloud_kids_video.mp4`, `poem.txt`, `topic.json`, and `thumbnail.png`.

## Schedule

The included cron is `0 9 * * 0` (Sunday at 09:00 UTC). You can change it in `.github/workflows/make-video.yml`. Scheduled workflows may be delayed during high GitHub load, and GitHub can disable schedules in inactive repositories.

## Local test (optional)

Requires Python 3.11+, Pillow, FFmpeg, Piper, and internet access. Run:

```bash
pip install -r requirements.txt
python scripts/make_video.py
```

For local runs, install FFmpeg and Piper separately first. The script downloads the voice model on its first run.

## Troubleshooting

- **Actions is disabled:** open the repository's Actions tab and enable workflows.
- **Piper command not found:** inspect the install step logs; package or runner availability may have changed.
- **RSS feed error:** the script logs the feed error and should fall back to the built-in topic list.
- **Artifact missing:** open the failed step in the run logs. The workflow only uploads outputs after a successful render.
- **Need actual AI-generated lyrics:** this starter intentionally avoids paid AI APIs. A future free local language model could be evaluated, but GitHub runner memory/time constraints make that a separate experiment.
