# Capability matrix — Triple-AAA closure R1

Observed scope: local ComfyUI at `127.0.0.1:8188`, runtime `0.34.0`, observed 2026-09-08. Values below are scoped to exact model assets, node inventory, workflow hash/fingerprint and hardware snapshot; they are not universal model claims.

| Feature | H3 T2V profile | H3 R2V probe profile | Evidence / decision |
|---|---|---|---|
| text-to-video | `CONFIRMED` | not claimed | `profiles/comfyui-h3-local-probed.json`; exact 384×224/124-frame workflow |
| native audio stream generation | `CONFIRMED` stream-level only | `UNKNOWN` pending probe | Stream presence is not listening, event causality or mix quality |
| image-to-video | `UNKNOWN` | not claimed | No accepted I2V artifact in current scope |
| reference conditioning / R2V | `UNKNOWN` | `UNKNOWN` until probe is collected and observed | `assets/workflows/h3-r2v-probe-api.json`, proposed profile revision 1 |
| first/last frame | `UNKNOWN` | `UNKNOWN` | No accepted endpoint probe |
| dialogue / voice / lip-sync | `UNKNOWN` | `UNKNOWN` | No generated dialogue artifact or phonetic oracle |
| camera controls | `UNKNOWN` | `UNKNOWN` | Camera text is not a runtime control or visual proof |
| 10–15s physical interaction | `BLOCKED` | `BLOCKED` | Exact H3 envelope is ~5.1667s; no accepted two-shot chain |
| 20–30s dialogue + interaction | `BLOCKED` | `BLOCKED` | Dialogue/lip-sync capability and chain unobserved |
| 45–60s demanding bounded production | `BLOCKED` | `BLOCKED` | No accepted dependent long-form artifact package |
| 90–120s extended production | `BLOCKED` | `BLOCKED` | Optional ladder; no evidence |
| second independent model | `BLOCKED_BY_EXTERNAL_CAPABILITY` | `BLOCKED_BY_EXTERNAL_CAPABILITY` | No Wan weights present locally; no external call authorized |

## Exact local runtime observation

- ComfyUI: `0.34.0`; node inventory hash observed in the current run: `sha256:6ef19d283e798646f9b9bdc353194d8ce7c55b6df85400e2acc15fad729b8674`.
- H3 R2V workflow hash: `sha256:6db1096e8cb6c7258413edef1d1290156a1f273d36fa7d1cbdbc24e4f3a2d3a6`.
- H3 R2V workflow fingerprint: `sha256:1b455641a3d4c9e11b91cc1a92517d68fb7ced70c63b39f24367609429e9f9b1`.
- H3 REF2VA asset hash: `sha256:de2c6c29c4ee702b45e48e40daae3834aeee58ab681c732d9152589a87c89910`.
- Observed GPUs: two RTX 3060 devices; the probe was queued against the exact workflow and its actual queue ID is stored in `verification/h3-r2v-probe-runs/`.

The R2V profile is not promoted to `CONFIRMED` merely because the node and model exist. Promotion requires a successful collected artifact plus endpoint/reference identity, motion, object state and media inspection records. If the probe times out or fails, the same queue ID is reconciled and the profile stays `UNKNOWN`/`BLOCKED`.
