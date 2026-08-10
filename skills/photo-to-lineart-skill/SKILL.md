---
name: photo-to-lineart-skill
description: Convert uploaded photos into recognizable, configurable visual styles including fidelity-preserving editorial treatment, line art, sketches, film looks, and poster styles using the repository's deterministic image-processing app. Use when a user asks to transform a photo, preserve the original subject, apply a visual style, create a line-art variant, or batch-process image outputs.
---

# Photo to Lineart

Use the repository's `lineart_core.py` as the source of truth for deterministic processing. Keep the original image unchanged and always save a new output.

## Workflow

1. Confirm that the user supplied an image or a local image path.
2. Choose a style from the registry: `极简保真`, `简约线条`, `铅笔素描`, `黑白线稿`, `漫画轮廓`, `编辑感抽象`, `复古胶片`, or `高对比海报`.
3. Start with intensity `0.65` and detail `0.60`; adjust one parameter at a time.
4. For local files, run the web app or call `process_image` from `lineart_core.py`.
5. Report the selected style, parameters, original size, output size, and output path.
6. Never claim that an image was processed if the result was not generated and checked.

## Product behavior

- Prefer local deterministic processing for privacy, repeatability, and offline demos.
- Use `简约线条` when the user wants sparse outlines, clean avatars, product thumbnails, or cover sketches.
- Use `极简保真` as the default when the source subject, colors, and composition must remain recognizable.
- Use `编辑感抽象` for muted color blocks and editorial-style visual experiments.
- Use `复古胶片` for a warm, restrained photo treatment.
- Use `高对比海报` for monochrome cover or poster concepts.
- Do not overwrite the input file.
- Reduce the maximum side of very large images to keep the demo responsive.
- Explain that the current version is an image filter, not a trained generative model.
- If AI restyling is requested, treat it as an optional future mode and preserve the original composition where possible.

## Validation checklist

- Verify the output exists and opens as an RGB image.
- Verify the output dimensions are valid and bounded.
- Test a normal photo, a grayscale photo, a transparent PNG, and a very large image.
- Test empty input and unsupported file formats with a clear user-facing error.
- Keep before/after examples and exact parameters for portfolio demonstrations.

## Useful commands

```powershell
python app.py
python -m pytest -q
```
