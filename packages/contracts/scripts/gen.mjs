// Generates ts/generated.ts from schema/contracts.schema.json (ADR-4).
// The schema itself comes from `uv run --directory services/science fieldshift contracts export`.
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { compileFromFile } from 'json-schema-to-typescript';

const root = fileURLToPath(new URL('..', import.meta.url));
const schemaPath = `${root}schema/contracts.schema.json`;
const outPath = `${root}ts/generated.ts`;

const banner = `/* eslint-disable */
/**
 * GENERATED FILE. DO NOT EDIT BY HAND.
 * Source: pydantic models in services/science/src/fieldshift/contracts (ADR-4).
 * Regenerate with \`npm run contracts\` at the repository root.
 */`;

const ts = await compileFromFile(schemaPath, {
  bannerComment: banner,
  unreachableDefinitions: true,
  additionalProperties: false,
  cwd: `${root}schema`,
});

await writeFile(outPath, ts.replace(/\r\n/g, '\n'), 'utf8');
console.log(`contracts types written: ${outPath}`);
