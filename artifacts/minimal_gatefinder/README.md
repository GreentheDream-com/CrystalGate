# Minimal GateFinder reference artifact

> Copyright © 2026 Derrick Covington.<br>
> Published through Green The Dream Research Lab.<br>
> Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).<br>
> Commercial and adaptation permissions: derrick@greenthedream.com

This directory is the executable smoke test described in Section 9.3 of the
CrystalGate manuscript. It uses only the Python standard library.

The Python implementation and tests are licensed under the PolyForm
Noncommercial License 1.0.0; the schema, claims, generated reports, and this
documentation are non-code research artifacts licensed under CC BY-NC-ND 4.0.
See the repository [license overview](../../LICENSE.md) and [notices](../../NOTICE.md).

The artifact contains:

- one closed synthetic matrix-to-phase domain schema;
- eight typed, versioned translators;
- two accepted claims, two rejected claims, one rerouted claim, and one
  underdetermined claim;
- a high-residual soft-gate case showing that machine status `pass` is reported
  to readers as `evaluated`, not as “small mismatch”;
- generated route manifests with certificate, evidence, score, repair, and
  provenance records; and
- six executable checks over the verdict and certificate behavior.

Run it from the repository root:

~~~powershell
python artifacts/minimal_gatefinder/gatefinder_demo.py
python -m unittest discover -s artifacts/minimal_gatefinder -p "test_*.py" -v
git diff --exit-code -- artifacts/minimal_gatefinder/generated/route_reports.json
~~~

The first command regenerates the committed report; the second runs the
artifact's executable checks; and the final command proves that the report at
the repository root is reproducible from its committed schema, claims, and
implementation. Use `--check` to validate the inputs and expected verdicts
without rewriting the report.

## Scope

This is a deterministic formal demonstration of the finite, nonnegative,
edge-additive routing case. It shows that the paper's manifest and verdict rules
can be executed on declared fixtures. It does not establish empirical utility,
automatic claim decomposition, completeness of a scientific schema, or the
correctness of evidence supplied by an external evaluator.
