# yard-pro Knowledge Assistant corpus

Curated, own-authored gardening + tool-care reference seeded for the Vector
Search index ``yard_pro_gardening_kb``. Read by ``scripts/yard_pro/deploy_ka.py``
to chunk and upsert into the index.

**Trust tier:** ``ground-truth`` (per plan §8 AI-security row). Coach
responses on recommendation turns MUST cite at least one chunk from this
corpus; ungrounded answers fall back to "I don't have a grounded answer —
consider your local dealer."

**Licensing:** all content is own-authored. No third-party copyrighted
almanac, manual, or website text. The KA-extraction nightly canary
(scripts/yard_pro/canary_ka_extraction.py, P1) verifies the coach
cannot regurgitate verbatim chunks > 200 chars.

**Region anchor:** Stuttgart kettle (DE-BW). Mid-April late-frost window
and the warm-microclimate pruning calendar drive almost every almanac
entry.

## Documents

| Path | doc_type | Coverage |
|------|----------|----------|
| `plant_care/apple.md` | plant_care | Apple-tree care, Stuttgart varieties |
| `plant_care/cherry.md` | plant_care | Cherry-tree care, silver-leaf prevention |
| `plant_care/plum.md` | plant_care | Plum-tree care, pruning windows |
| `plant_care/lawn.md` | plant_care | Lawn care, mowing height, watering depth |
| `plant_care/beech_hedge.md` | plant_care | Beech hedge trims (June + August) |
| `plant_care/lavender.md` | plant_care | Lavender shaping, avoid old wood |
| `plant_care/hydrangea.md` | plant_care | Endless-summer pruning windows |
| `plant_care/boxwood.md` | plant_care | Boxwood care + moth pheromone refresh |
| `plant_care/rhododendron.md` | plant_care | Acidic soil, shaping prune |
| `plant_care/rose.md` | plant_care | Rose care, Schneewittchen specifics |
| `regional_almanac/stuttgart_year_round.md` | almanac | Year-round Stuttgart kettle calendar |
| `regional_almanac/stuttgart_may.md` | almanac | May tasks (weekend planner) |
| `regional_almanac/stuttgart_june.md` | almanac | June tasks |
| `regional_almanac/stuttgart_july.md` | almanac | July tasks |
| `consumables/fertilizer_npk.md` | consumables | NPK fertilizer timing + dosing |
| `consumables/copper_fungicide.md` | consumables | Copper fungicide dilution + windows |
| `consumables/two_stroke_oil.md` | consumables | 2-stroke fuel + bar-and-chain oil |
| `consumables/robotic_mower_blades.md` | consumables | Robotic-mower blades, trimmer grease |
| `diagnostic_playbooks/apple_scab.md` | playbook | Apple scab vs powdery mildew |
| `diagnostic_playbooks/fusarium_blight_lawn.md` | playbook | Fusarium blight in lawns |
| `diagnostic_playbooks/powdery_mildew.md` | playbook | Powdery mildew across hosts |
| `diagnostic_playbooks/boxwood_moth.md` | playbook | Boxwood moth intervention |
