---
doc_type: playbook
region: DE-BW
condition: powdery_mildew
---

# Diagnostic playbook — powdery mildew (multi-host)

Powdery mildew is the umbrella name for a family of related fungal
diseases (different fungi for roses, cucurbits, apples, oaks, etc.)
that share a strikingly similar appearance: a white, powdery coating
on leaves and stems that looks as though the plant has been dusted
with flour. The single highest-leverage prevention across all hosts is
good airflow.

## Visual indicators

- **Texture:** white to grey, powdery surface coating that wipes off
  with a finger (this distinguishes it from natural leaf surface).
- **Location:** typically upper leaf surface first, then spreading to
  the underside, stems, and (in late infections) flower buds.
- **Affected leaves:** distort, curl, and yellow underneath the
  coating. Severely affected leaves drop.
- **Conditions favouring outbreak:** warm days (above ~18 °C), humid
  air, still nights without dew, dense plant canopies.

## Differential diagnosis

- **Downy mildew** — white coating but typically on the *underside* of
  the leaf only; yellow patches on the upper surface above. Different
  fungal family, different treatment.
- **Slug or snail residue** — silvery, thin trails on individual
  leaves, not a coating.
- **Salt or hard-water residue** — only on plants regularly watered
  overhead; uniform thin film rather than fluffy texture.
- **Wax bloom on grapes / plums** — natural, easily wiped off; located
  on fruit only, not on leaves and stems.

## Host-specific notes

- **Roses** — most common in dense, poorly-pruned plantings. Powdery
  mildew on roses worsens through late summer in still, dry weather.
- **Apple trees** — powdery mildew here looks different from leaf
  surface (mildew) vs scab (dark embedded lesions). Mildew also
  affects developing shoots, distorting new growth.
- **Cucurbits** (cucumber, courgette) — common in mid-to-late summer;
  often the limiting factor for late-season harvest.
- **Oak trees** (especially young) — common on water-shoots and lower
  branches; usually cosmetic on established trees.

## Treatment

First-line interventions are cultural:

1. **Open the canopy** at the next appropriate pruning window. Most
   powdery-mildew outbreaks trace back to a dense, still interior.
2. **Improve air movement** — for vegetable beds, increase spacing on
   the next planting. For roses, the spring structural prune is the
   highest-leverage intervention.
3. **Water at the base only.** Overhead watering wets leaves and feeds
   the disease.
4. **Sanitation:** remove and bin (do not compost) heavily affected
   leaves, especially at end of season.

A milk-spray (10% milk in water, applied to foliage in early morning
once a week) has some evidence of effectiveness on early outbreaks on
cucurbits and roses. Approved fungicides exist for serious cases;
follow product instructions exactly and rotate active ingredients to
reduce resistance.

## Recovery

Powdery mildew affected leaves do not recover — they were damaged at
the cellular level. The success metric is whether the *new* growth
after intervention is clean. A well-managed plant with one mildew
flush typically grows out of it within 3-4 weeks.

## Confidence cue for the vision model

Powdery mildew is among the most visually distinctive plant diseases
and is one of the easier confident calls for the vision model on a
well-lit photograph showing the white coating clearly. Low confidence
on a suspected mildew call should still prompt the "second opinion"
suggestion — the difference between powdery and downy mildew (which
require different treatment) is a common confounder.

---

*This playbook is advisory only. Different hosts have different
treatment thresholds; consult a host-specific guide before applying
fungicides.*
