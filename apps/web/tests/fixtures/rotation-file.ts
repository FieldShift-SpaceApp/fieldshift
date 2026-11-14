// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// TEST FIXTURE. Not agronomic data: every text field says so, and nothing here is shown on a public page.
// rotation-file.json is the pipeline output (fieldshift rotation) for the TEST FIXTURE input in
// services/science/tests/fixtures/rotation/; pytest checks they stay identical
// (tests/test_rotation_stage.py::test_web_fixture_is_the_pipeline_output) and validates the contract.
import type { RotationFile } from "@fieldshift/contracts";
import json from "./rotation-file.json";

// JSON imports widen literals (and tuples) to plain types; the shape is checked by pydantic in pytest.
export const fixtureRotationFile = json as unknown as RotationFile;

/** `ag_year.start_month` of the TEST FIXTURE site (services/science/tests/fixtures/rotation/.../site.yaml). */
export const FIXTURE_START_MONTH = 9;
