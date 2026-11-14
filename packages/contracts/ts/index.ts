// @fieldshift/contracts — the only hand-written file in this package (ADR-4).
// Types come from generated.ts (pydantic → JSON Schema → json-schema-to-typescript).
// CONTRACT_MAJOR must match the major of SCHEMA_VERSION in
// services/science/src/fieldshift/contracts/common.py (checked by pytest).
export * from './generated';

/** The app checks only the major version at build time; the data is already validated. */
export const CONTRACT_MAJOR = 1;
