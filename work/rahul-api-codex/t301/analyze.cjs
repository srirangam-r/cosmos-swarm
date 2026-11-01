#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const crypto = require('node:crypto');
const {analyzeDial} = require('./dial_analysis.cjs');

function analyzeInput(raw) {
  const doc = JSON.parse(raw);
  if (!doc || !['synthetic','audited_measurements'].includes(doc.data_kind))
    throw Error('data_kind must be synthetic or audited_measurements');
  if (!Array.isArray(doc.plan) || !Array.isArray(doc.observations))
    throw Error('plan and observations arrays required');
  const result = analyzeDial(doc.plan, doc.observations);
  if (result.scenes !== 3 || result.seeds_per_scene !== 2 || result.planned !== 30)
    throw Error('task265/5950 requires exactly 3 scenes x 2 seeds x 5 doses');
  return {
    ...result,
    data_kind: doc.data_kind,
    input_sha256: crypto.createHash('sha256').update(raw).digest('hex'),
    source_contract_message: 5950,
    observation_status: doc.observations.length ? 'ROWS_SUPPLIED' : 'NO_ROWS',
    interpretation: 'Arithmetic acceptance only. Native/strip booleans and reader validation must be audited externally. No physical, model, causal, referee or NVIDIA certification.',
    context: doc.context ?? null,
  };
}

if (require.main === module) {
  try {
    if (process.argv.length !== 3) throw Error('Usage: node analyze.cjs input.json > report.json');
    const report = analyzeInput(fs.readFileSync(process.argv[2], 'utf8'));
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  } catch (err) {
    process.stderr.write('dial analysis: ' + err.message + '\n');
    process.exitCode = 2;
  }
}
module.exports = {analyzeInput};
