# Drafter foundation

Steps 1-2: a small example input and versioned input/output contracts. Model
inference and graph generation are future steps. No LLM is called by this code.

From the repository root, using Python 3.12:

```sh
python3 -m pip install -r drafter/requirements.txt
python3 -m drafter --validate-request drafter/cases/scenario_a.request.json
python3 -m unittest discover -s drafter/tests -t . -v
```

The validation command returns zero for a valid **fixture contract**, and one for
rejected input. It does not certify the evidence or robot behavior.

The example preserves Nikta's original archived registry export and all five
configured objects. Its new illustrative configuration limits the demonstration
to saved frames 10-12; it is not a full-execution assessment. The export provides
metadata and source references, not numerical observation arrays. Original
producer statuses remain unchanged; their source files were not replayed here.
Physical support/fall evidence remains blocked and missing objects/frames remain
explicit. No checker assessment, safety conclusion or generated graph is supplied.

See [CONTRACT.md](CONTRACT.md) for the exact input/output boundary, versions,
provenance rules and future Critic/retrieval integration.

Regenerate the example without changing source evidence:

```sh
python3 drafter/tools/build_scenario_a.py
```

This foundation uses the original registry export format. A Phase 5 bundle needs a
separate lossless adapter; grouped citations cannot be inserted as registry records.
The current fixture profile deliberately keeps empirical admission disabled.
