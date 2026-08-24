# Examples

## `scripts/ep1-ten-carrots.json`

A fully worked example script/storyboard, in the exact JSON format
`script_generator.py` produces, so you can see the shape of the data before
generating your own.

Generate audio and a rough-cut preview from it directly:

```bash
python main.py generate-audio examples/scripts/ep1-ten-carrots.json --out-dir examples
python main.py assemble-video examples/scripts/ep1-ten-carrots.json \
  --audio-dir examples/audio/bounce-the-counting-bunny---ep1-ten-carrots
```

It already carries a clean `_safety_report` (see `src/content_safety.py`) —
re-run the check yourself any time with:

```bash
python main.py check-safety examples/scripts/ep1-ten-carrots.json
```
