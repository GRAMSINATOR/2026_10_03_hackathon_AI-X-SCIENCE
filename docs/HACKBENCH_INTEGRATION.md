# HackBench × Parallax integration (qte77, 2026-10-04)

**Roles** (per #6 and #7):
- **Parallax:** the opportunity map. New markers extractable from existing data, blind spots, and measurement capabilities that would unlock them.
- **HackBench:** the trust and evaluation layer around Parallax, plus agent-native exposure and the agentic literature search that feeds the map.

HackBench repo: https://github.com/qte77/2026-10-03-london-ai-science-hack (data exchange only; no code copied either way).

## 1. Literature for the opportunity map (proposed, not yet adopted)

`research/proposed/qte77.research.0001.json` is a `marker-research/1` bundle (`kind: research_agent`) with **18 papers**. Each title, author list, year and venue was checked against its DOI landing page, Crossref or the arXiv page. It contains evidence only, with no scores, confidences or `status` keys. It answers the literature questions in `docs/FIELD_MODEL.md` §7.

Validation on this branch (base `d747fc6`):
- `jsonschema` against `schema/marker_research.v1.schema.json`: 0 errors. Every assessment target exists in `research/seed.controller.json`.
- `python -m qc.frontier build --fields fixtures/epistemic_field.Batch_{2,3}.json --bundles research`, with the bundle placed in `research/`: **coherent**.
- Gate changes versus the seed alone:

| Case | Gate | Seed only | With this bundle |
|---|---|---|---|
| `capability:tomography_3d` | literature_convergence | open | **met** |
| `capability:eds` | literature_convergence | open | **contested** |
| `marker:fines_subfloor_size` | scientific_relevance | open | partial |
| `marker:high_z_composition` | scientific_relevance | open | partial |
| `marker:pore_connectivity_3d` | scientific_relevance | open | partial |
| `marker:spatial_correlation_length` | scientific_relevance | open | partial |

**Why `proposed/`:** the bundle genuinely advances gates. Dropping it into `research/` makes the committed `fixtures/marker_frontier*.json` and 7 assertions in `tests/test_frontier.py` stale; with it in `proposed/`, all 30 tests pass. Following your rule that a person selects what crosses into the product, adopting it is your call:
1. `git mv research/proposed/qte77.research.0001.json research/`
2. `python -m qc.frontier fixtures`
3. Update the oracles of the 7 tests that depend on the committed frontier. Those that broke in our check: both `test_committed_fixture_is_coherent_and_reproducible` variants, `test_seeded_states_follow_the_current_field`, `test_candidate_classes_separate_capture_from_observability`, `test_fixture_evidence_never_advances_a_gate`, `test_contradictory_papers_are_represented` and `test_one_source_or_one_group_is_not_replication`.

**Not answered by the literature found** (open, worth stating as limits):
- no source quantifies ion-milling or polishing artefacts on porosity correlation length;
- no Si/SiOx/C-specific BSE separability study exists in a graphite anode;
- no EDS test exists on sub-µm Si in graphite at 5–10 kV.

## 2. Trust and evaluation layer (live)

- **Pre-registration:** tag `prereg-2026-10-04-unseen` with a GitHub server-timestamped release, 2026-10-04 10:04:32 BST, made before HackBench reads any new batch.
- **Planted-drift test** (known answers, material vs imaging drift): HackBench's reference scores held-out 5/9 at k = 2.5 (calibrated on a separate training suite). 0 material drifts accepted, 2 blurred-image false rejects, 1 contrast over-flag, 1 coarsening under-call. Parallax has not been run on this suite yet; that is the planned known-answer test from #5.
- **Cross-check on real batches:** on Batch_2 both say ACCEPT. On Batch_3 Parallax says REJECT (M2060 additive density) and HackBench says ACCEPT with acquisition flags. HackBench has no particle-count KPI, so it is blind to that signal, and the console states the disagreement and why.
- **Live, agent-native:**
  - console: https://thismay52--hackbench-web.modal.run/results/ (renders your decision briefs; polymer, console and lab80 looks)
  - JSON: `/v1/results` (`hackbench-results/1`)
  - markdown: `/results.md`
  - The whole cycle (reference, suite, agents, literature, briefs) runs on Modal with a hash-chained journal.

## 3. Next (HackBench side)

- A read-only `/v1/marker-frontier` endpoint and an `inspect-marker-frontier` skill serving `fixtures/marker_frontier.json` (it contains no imagery), as proposed in #6.
- A micrograph-level bootstrap using `fixtures/provenance_map.json`. 27/27 of HackBench's fields of view match your tile ids. Parent micrographs span batches, so resampling must cluster by parent across batches.
- Run your pipeline on the planted-drift suite (#5).
