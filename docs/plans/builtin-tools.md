# Plan: built-in tools after `nuke_vision`

Status: plan, not approved. No code yet.

Research and evidence: [builtin-tools-research.md](builtin-tools-research.md).

## Goal

Give the agent two more read-only tools in the panel: `nuke_graph` and `nuke_stats`. Maybe a third, `nuke_check`, later. They work when `allow_arbitrary_code` is `false`, so a studio with code off still gets a useful agent.

## Rules

- Follow [agent-vision.md](agent-vision.md): add a tool only when a real request fails without it.
- Build `nuke_graph`, then try it. Build `nuke_stats`, then try it. Decide on `nuke_check` after both trials.
- Every list in a reply has a cap and a `truncated` flag.
- Every reply says what was not checked.
- Each tool is a function that code in Nuke can also call, as `vision` is.

## Decisions to confirm

1. **Vision stays, for images only.** Today the **Vision** checkbox turns off every built-in tool (`server.py:156`). Change it to turn off only `nuke_vision`. `builtin_tools()` returns all tools, and `server.py` removes `nuke_vision` when Vision is off. `nuke_graph` and `nuke_stats` have no checkbox. They are on while the panel is connected.
   - Why: a studio turns Vision off so that images of client footage do not go to the AI provider. The checkbox must mean only that.
   - `nuke_graph` sends names, knob values and paths, like any tools-file tool. `nuke_stats` sends numbers.
   - Cost: a studio cannot hide the graph without disconnecting the panel. Add a second checkbox only if a studio asks.
   - No rename, so the settings key `vision` and the docs stay.
2. **One name prefix.** All temporary nodes start with `_nss_`. Vision's nodes (`_nss_vision_<id>`) already do, so no code changes. `docs/mcp.md` now tells pipelines to ignore `_nss_`.
3. **Name collisions.** No new code is needed. `load_tools` already skips a tools-file tool whose name matches a built-in ("a tool with this name is already loaded"). When built-ins are off, a studio can use the name. This is correct behaviour.

## Layout

```
nukeserversocket/controllers/nuke/builtin/
  __init__.py   builtin_tools(): add each new *_TOOL here
  vision.py     exists
  graph.py      nuke_graph
  stats.py      nuke_stats
  _temp.py      temporary nodes: _nss_ prefix, undo off, delete in finally
```

`_temp.py` comes out of `vision.py` when `stats.py` is written, not before.

## `nuke_graph`

Read-only. Returns one group of the graph, compact.

### Arguments

| Argument | Default | Notes |
|---|---|---|
| `group` | root | Full name of a Group. Only its direct children are listed. To go inside a child Group, call again with its name. |
| `max_nodes` | 200 | Cap on the node list. |
| `since` | none | A `snapshot` id from an earlier reply. Lists only the nodes that changed, were added or were removed since then. |

No `depth` argument. One group per call is simpler, and each Group node in the reply shows its child count.

### Reply (JSON)

- `script`: path (empty while unsaved), modified, frame, first and last frame, fps, format, proxy, views, colour management and OCIO config.
- `viewer`: name, the node on the active input, view. `null` when there is no Viewer.
- `selected`: names of the selected nodes. Selection is context ("this"), not a target.
- `nodes`: one entry per node:
  - `name`, `class`;
  - `inputs`: input names in order, `null` for an empty input;
  - `disabled`, `error` (`hasError()`);
  - `knobs`: non-default knobs as `.nk` text (`writeKnobs(WRITE_NON_DEFAULT_ONLY | TO_SCRIPT)`);
  - `children`: count, Group nodes only.
- `removed`: names, only with `since`.
- `snapshot`: an id for the next `since`.
- `truncated`: list of what was cut.

### Knob size cap

Per-knob cap, 1000 characters. A knob over the cap shows as `<curves: 299220 chars, cut>`. Read the full value with code.

Evidence: the `curves` knob of `Roto_woman` in the live session is 299,220 characters. The other nodes are under 200 characters each. Without a cap, one Roto node fills the reply.

### `since`

- The panel keeps the last 4 snapshots in memory: `{fullName: writeKnobs(... | WRITE_ALL)}`. `WRITE_ALL` adds position and name, so a moved or renamed node counts as changed.
- An unknown or expired id returns the full graph and a warning.
- Snapshots are lost when Nuke restarts. That is acceptable: the full graph comes back.
- Evidence: 200 nodes take 0.5 ms (headless). A changed knob shows in the diff.

### Cost and risk

- Main thread, about 1 ms for 200 nodes, headless. Not timed in the GUI.
- Reads only. Knob text can try to steer the agent; the server instructions already cover scene text.

### Annotations

`readOnlyHint` true, `destructiveHint` false, `idempotentHint` true, `openWorldHint` false.

## `nuke_stats`

Read-only in effect. Exact numbers for one frame of a node.

### Arguments

The same as `vision` where they overlap: `node` (default: the active Viewer input), `frame`, `view`, `channels` (default `rgb`, or a layer or one channel), `crop`.

### Reply (JSON)

- `node`, `frame`, `view`, `region`.
- Per channel: `min`, `min_at`, `max`, `max_at`, `mean`, `nan`, `inf` (counts).
- `warnings`, the same checks as `vision` (outside the frame range, proxy mode, node error).

### How

- `CurveTool` `Max Luma Pixel` gives the value and position of the brightest and darkest pixel, by luma. To get one channel, copy that channel into r, g and b first, as `vision` does. Then luma equals the channel value. One `CurveTool` run per channel. Runs after the first are warm.
- `CurveTool` `Avg Intensities` gives the mean of four channels in one run.
- NaN and infinity counts: an `Expression` node that outputs 1 for a NaN pixel and 0 otherwise, then `Avg Intensities` times the pixel count. Exact, one more run.
- Temporary nodes through `_temp.py`.

### Test first, before any code

Results (2026-11-09), headless, the same on 15.2v9 and 17.1v2. Probe script in the session scratchpad, not in the repo. Test image: 64 x 64, all 0.5, red NaN at (10, 10), red +inf at (20, 20), red 7 at (40, 40), green -2 at (30, 30).

| Question | Result |
|---|---|
| `Avg Intensities` with one NaN pixel | The mean of that channel is NaN. The fourth value of `intensitydata` is NaN too, so it is not alpha. Do not use it. |
| `Max Luma Pixel` with NaN and inf | It skips NaN. It reports +inf at (20, 20) as the maximum, so the finite maximum (7) is hidden. The minimum, -2 at (30, 30), is correct. |
| `isnan(r)`, `isinf(r)`, `r != r` in an Expression | All three work. `Avg Intensities` of the 0 or 1 result, times the pixel count, gives the exact count. |
| Finite maximum | Replace NaN and inf with a very low value, then `Max Luma Pixel`: 7 at (40, 40). |
| Per-channel min and max | Copy the channel into r, g and b, then `Max Luma Pixel`. Correct for red and green, with positions. |
| `ROI` smaller than the format | Works. |
| bbox smaller than the format | `CurveTool` averages the whole `ROI`. Outside the bbox Nuke repeats the edge pixels, so the mean (0.468) is neither the bbox mean nor the format mean. |

So, per request:

1. One count run: an Expression with `isnan` and `isinf` for up to two channels per run, then `Avg Intensities`. Gives `nan` and `inf`.
2. Mean of the finite pixels: an Expression that outputs the value where it is finite and 0 elsewhere, and a second channel that outputs 1 where finite. Mean = average of the first / average of the second. One run for up to two channels.
3. Min and max: one `Max Luma Pixel` run per channel, through a Copy. When the channel has NaN or inf, two runs: non-finite replaced with a very low value for the maximum, with a very high value for the minimum.

For rgb with no NaN or inf: 2 + 2 + 3 = 7 runs. Only the first one is cold.

Still open:

- Region (decided 2026-11-09): the format, or `crop`, as in `vision`. When the bbox does not cover the region, the reply warns that pixels outside the bbox repeat its edge and are in the numbers.
- The "Setting knob values from validate" warnings. They print in the log headless. Not checked in the GUI: that needs a test in a live session, which creates and deletes temporary nodes there.
- Cost of 7 runs on a heavy script: not measured.

### Cost and risk

- One render of the upstream graph, like `vision`. Then one fast run per channel.
- Creates and deletes nodes. `onCreate` callbacks run, as for `vision`.

### Annotations

The same as `vision`: `readOnlyHint` true, `idempotentHint` true.

## `nuke_check` (later, maybe)

Decide after the trials. Build it only if "why is this black" or "why is this red" fails with `nuke_graph`, `nuke_vision` and `nuke_stats`.

If built, it lists nodes with `hasError()` and adds a cause where a rule finds one:

- Read or Write file missing: `fileDependencies()` for the current frame, then `os.path.exists`.
- Empty required input. A Grade with no input reports no error, so check inputs directly.
- Current frame outside the node's range.

Cap the number of files and the time. Say "no cause found" when no rule matches. Stop at about five rules.

## Tests

- Unit tests in `tests/` with a mocked `nuke`, as for `vision`: arguments, caps, `truncated`, `since` with an unknown id, Vision off hides only `nuke_vision`.
- Headless checks with `Nuke -ti`, next to `scripts/vision_bench/check_vision.py`: real graphs, the Roto knob cap, the hot-pixel case from the research, NaN pixels, no leftover nodes or files, undo unchanged. Run on 15.2 and 17.1.

## Trials

In the live session, on real requests. For each: did the agent get there, how many calls, did it need code.

`nuke_graph`:

1. "What does this script do?"
2. "What did you change?" (after an edit, with `since`).
3. "Connect the new plate into the comp."

`nuke_stats`:

1. "Is this plate clipping?"
2. "Are there NaNs in this render?"
3. "Does the grade match the reference?" (with `nuke_vision`).

### First trial (2026-11-09)

Live Nuke 15.2v9 GUI, the artist's own script (Read of a mov, Crop, Roto, ColorCorrect, Merge, Write, Viewer). The MCP client still listed the old tools, so the functions ran through `nuke_execute_code`. This tests the tools, not an agent choosing them.

`nuke_graph`:

- 7 nodes: 2 ms, 2,900 characters. `since` with no change: 0.7 ms, nothing listed. Modified flag unchanged.
- The Roto `curves` knob (299,220 characters) was cut as planned.
- About 1,000 of the 2,900 characters are UI state: the Roto `toolbox` and `toolbar_*` knobs, and the Viewer's `roi`, `colour_sample_bbox` and flipbook `file`. Not fixed. Possible fix: skip `toolbox` and `toolbar_*`, and list a Viewer with its inputs only.
- Merge input order is not visible: inputs read `['Crop1', 'ColorCorrect1', 'Roto_woman']`. Nuke 15.2 has no `inputLabel()`. Fixed: the description says a Merge2 reads B, A, mask.

`nuke_stats`:

- Viewer input (Merge1, 640 x 640, rgb): 0.22 s. It showed the image is far over range (red maximum 255 at (262, 591), mean 1.7) from the ColorCorrect gain. The kind of answer it is for.
- The default frame was 0, outside the Read's range, and the warning said so.
- Roto alpha: 0.07 s.
- `channels='rgba'` on the mov (no alpha) gave "no channel or layer 'rgba'. Layers: ['rgba']". Fixed: it now names the missing channel.
- No `_nss` nodes left, node count and undo state unchanged. No dialog blocked the call. The `CurveTool` log lines were not seen: the Script Editor output is not returned for tool calls.

### Benchmark of `nuke_graph` (2026-11-09)

Headless Nuke 15.2v9, synthetic script built in the session scratchpad: 300 Read > Grade > Transform chains (200 Reads on a real local 10-frame EXR sequence, 100 on missing files), 50 Roto nodes each with the 299,220-character `curves` of the artist's real Roto, 20 Text2, and 10 Groups of 50 Blurs. 980 nodes at the root, 1,490 in all.

| Call | Time | Nodes | Characters (about tokens) |
|---|---|---|---|
| First call, `max_nodes` 1000 | 0.037 s | 980 | 133,423 (33,000) |
| Second call | 0.030 s | 980 | 133,423 |
| Default (`max_nodes` 200) | 0.020 s | 200 | 29,988 (7,500), `truncated` set |
| One Group | 0.001 s | 51 | 5,080 (1,300) |
| `since` after one knob change in a Group | 0.001 s | 1 | 485 |

- `hasError()` on all 980 nodes, which validates the Reads: 0.057 s. Fingerprints of all nodes, including 50 copies of the 300,000-character `curves`: 0.018 s.
- Average entry: Read 199 characters, Text2 161, Transform 119, Roto 98 (`curves` cut), Grade 89.
- Speed is not a problem on a local disk. Reads on network storage with a cold cache were not tested. In the GUI, most nodes are already validated, so the first call should be cheaper there.
- Size is the problem on a big flat script. 980 nodes cost about 33,000 tokens. The default cap keeps one reply near 7,500 tokens, but an agent then cannot reach nodes 201 to 980 except by raising the cap. There is no offset and no filter by class or name.

### Reply size options (2026-11-09)

Same 980 nodes. Tokens are a rough count of words, numbers and punctuation marks (no tokenizer installed): good for comparing formats, not exact.

| Format | Characters | About tokens |
|---|---|---|
| A. JSON as today | 133,423 | 62,000 |
| B. JSON without spaces and empty fields | 119,035 | 59,000 |
| C. One line per node: `Grade1 Grade <Read1 \| white=1.2` | 75,626 | 25,000 |
| D. C, with chain inputs as `<^` | 71,942 | 25,000 |
| E. Node count per class only | 83 | 38 |

- `classes=["Read"]` (added): 300 nodes, 60,770 characters, 0.019 s.
- JSON punctuation (quotes, braces, repeated keys) is more than half the tokens. Format C keeps all the content.
- Repeated long file paths are most of what is left in C.
- Byte compression (gzip, base64) does not help: the model reads tokens, and encoded bytes are unreadable and longer.

Decision: keep JSON. Other tools do the same: blender-mcp caps its scene summary at 10 objects, dcc-mcp-nuke caps at 256 nodes and 64 knobs with a node count. [Anthropic's tool guide](https://www.anthropic.com/engineering/writing-tools-for-agents) asks for defaults, filters and a truncation message that tells the agent what to do next, and says to pick a format by testing. Custom compact formats (TOON) save 18 to 40% but lose some accuracy. So the `truncated` message now lists the 10 most common classes and points to `classes`. A concise mode waits for the agent trials. Claude Code warns at 10,000 tokens and saves a reply over 25,000 tokens to a file.

### Agent trial 1 (2026-11-09)

New Claude Code session, request only "What does this script do?", no tool names. Same live script as the first trial.

- Calls: `script_info` (studio tool), `nuke_graph` once, `nuke_vision` twice. No `nuke_execute_code`.
- Right: the node flow, Merge1 as graded A over plain B through the Roto mask, Write1 with no input or path, frame range 1 to 20 against 162 video frames, never saved.
- It read the cut Roto `curves` (about 300K characters) as a hint that the shape is animated, and said it only looked at frame 1.
- It did not use `nuke_stats`; it said it did not measure clipping.

### Agent trial 2 (2026-11-09)

New session, request only "Is this plate clipping?".

- Calls: `nuke_graph` once, `nuke_stats` twice (Read1 and Merge1 at frame 1), `nuke_vision` once, then ffmpeg in Bash on the source mp4 for all 162 frames.
- Right answer: the plate touches 1.0 in a few dozen specular pixels per frame (under 0.013%); the hot values in the Viewer come from ColorCorrect1, not the plate.
- Gap: it left Nuke for two things `nuke_stats` does not give, a count of pixels at or over a value and a frame range. ffmpeg works only because the source is a plain movie. For a node inside the tree, it would need 162 calls or code.

Not done: "what did you change" with a real edit.

### Agent trial 2, after the frame range (2026-11-09)

New session, the same request. Calls: `nuke_graph`, `script_info`, `nuke_stats` three times, `nuke_vision` twice. No Bash, no ffmpeg, no `nuke_execute_code`. It measured all 162 frames in Nuke: about 43 red and 28 blue pixels per frame at 1.0, worst frame 139 (106 red pixels), no NaN or inf on any frame. Same conclusion as with ffmpeg. It also noted the 8-bit source and blacks at 0.

### Method compared (2026-11-09)

Headless, a black 2K frame (2048 x 1556) with one red pixel of 50 at (1500, 900).

| Method | 15.2v9 | 17.1v2 | Found the pixel |
|---|---|---|---|
| `nuke_stats` (CurveTool), rgb | 0.058 s | 0.055 s | yes, value and position |
| `nuke.sample` on every pixel, rgb (timed on 256 x 256, scaled up) | about 5 s | about 7 s | yes |
| 5 x 5 grid of `nuke.sample` | instant | instant | no, max 0 |

Neither Nuke has `numpy` or `OpenEXR` in its Python, so rendering to a file and reading it in Python needs packages the studio must install. The image is trivial to render; on a real comp both methods cost more, and the ratio is not measured.

### Range in the GUI (2026-11-09)

The 162-frame run looked bad in the live GUI: the loop ran one execute per pass per frame, about 1,500, and each opened the progress dialog and moved the timeline. The temporary nodes showed in the root graph. The script was clean after: no `_nss` nodes, frame back, undo on.

Nuke's background renders (Frame Server, `executeBackgroundNuke`) run child Nuke processes that render Write nodes to files. The API has no way to run a render off the main thread in the same process. So it stays in process, with fewer executes:

- Each pass runs once over the range. The first frame runs alone, to estimate how many frames fit in 40 s. The NaN and infinity passes run only on frames that have them. 6 frames, 3 channels, `over`: 20 executes, was 56. For 162 frames: about 18, plus 2 per frame with NaN or infinity.
- The temporary nodes go inside one temporary Group (`_temp.py`), for `nuke_vision` too. Every node in it keeps the `_nss_` prefix.

### Frame range probe (2026-11-09)

Headless Nuke 15.2v9, 50-frame 2K EXR sequence read back from disk: a checkerboard that gets brighter each frame, with NaN at (100, 100) on frame 7 only and a hot pixel 9 at (300, 200) on frame 30 only.

- `nuke.execute(curve, 1, 50)` keys one value per frame, in both modes (Avg Intensities and Max Luma Pixel). Keyed values equal single-frame runs exactly.
- Time: 12 ms per frame per pass, both as one range execute and as a Python loop of single-frame executes. A light image; real plates cost more.
- The NaN on frame 7 and the hot pixel on frame 30 (value and position) were found.
- Max Luma Pixel over a range logs "Setting knob values from validate is not supported" for its four knobs. The values were right.

Design from this: loop in Python over frames with the code that exists, not a range execute. Same speed, no new code path, and the loop can stop on a time limit and return what it has with a warning. One frame with 3 channels is 6 to 9 passes.

- `last` (default: `frame` only; `frame` stays the first frame, so the old calls work). Reply: per channel min and max over the range, each with its frame and position; NaN and inf totals; `bad_frames`, up to 10 frames with NaN or inf; `seconds`.
- `over` (optional value): count and fraction of pixels at or above it per channel, and the frame with the most. One more pass per channel.
- A 40 s time limit instead of a frame cap, under the bridge's 60 s default timeout: stop, warn, set `last` to the last frame measured.

Built. The CurveTools are made once per channel and run once per frame. Found while building: when one CurveTool runs on several frames, Nuke 17.1 keys each frame and `value()` reads the current frame, so every frame read back frame 1. Fixed with `getValueAt(frame)`. Nuke 15.2 did not show it. The old single-frame code was not affected: it made a new CurveTool for each call. check_stats passes on 15.2v9 and 17.1v2.


## Order of work

1. Settle the decisions above.
2. Vision gates only `nuke_vision`, and the `_nss_` prefix. One commit.
3. `nuke_graph`, its tests, its docs in `docs/mcp.md`. Trials.
4. The `nuke_stats` checks under "Test first". Then `_temp.py`, `nuke_stats`, tests, docs. Trials.
5. Decide on `nuke_check`.
