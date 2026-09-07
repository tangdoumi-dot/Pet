This is a desktop pet designed for Codex. Its name is Cicereius.

## pet 1.0

This version preserves the original 8-column, 9-row pet artwork (1536 x 1872),
including the smiling-sigh animation. The Git version tag is `pet-1.0`.
This project version does not indicate compatibility with the v2 sprite format.

The repository includes the build script, prompts, reference artwork, final
`hatch-pet-runs/xiselius/final/spritesheet.webp`, and validation/QA reports.
Generated intermediate frames, previews, duplicate exports, and local backups
are excluded from Git.

### Window Troubleshooting

`repair-pet-window.py` is an optional Windows utility that backs up local
configuration and pet assets before clearing only saved pet window bounds.
Exit Codex completely before running it. `--check` performs a read-only check.
The `.cmd` launcher uses this workstation's bundled Python path; adjust that
path on another computer or run the Python script directly with Python 3.

Mouse clicks passing through the pet after a Codex update remain an unresolved
issue. The reset utility has not been confirmed to fix it. This version does
not regenerate artwork or upgrade the sprite format.
