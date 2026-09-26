export const meta = {
  name: 'consult-blind',
  description: 'mychart-advisor independent consult, blind stage: fact base, generators, triage, investigators, red team, second round, test planner',
  whenToUse: 'Only from the independent-consult skill after the blinding probe passes, for users who opted into multi-agent workflows. Pass args {snapshot, preset, agentType}.',
  phases: [
    { title: 'Fact base' }, { title: 'Generators' }, { title: 'Triage' },
    { title: 'Investigators' }, { title: 'Red team' }, { title: 'Second round' }, { title: 'Test plan' },
  ],
}

// args: { snapshot: '/abs/consult/<date>/snapshot', preset: 'standard'|'deep'|'max', agentType: 'mychart-advisor:blind-reader' }
const A = args || {}
const S = A.snapshot
const P = A.preset || 'standard'
const type = A.agentType || 'mychart-advisor:blind-reader'
const pre = `Read ${S}/AGENTS.md first and follow it exactly. Your snapshot directory is ${S}. Role prompts are in ${S}/_method/roles.md, schemas in ${S}/_method/schemas.md, and families in ${S}/_method/family-taxonomy.md.`
const blind = (prompt, opts) => agent(`${pre}\n\n${prompt}`, { agentType: type, ...opts })
const out = {}

const DOMAINS = P === 'standard'
  ? ['results and imaging', 'notes and clinical course']
  : ['specimen-based diagnostics: fluid studies, pathology, microbiology', 'imaging',
     'blood, urine, and systemic labs', 'clinical course: history, exposures, exam by instrument, medications with dates given, function']
const GENERATORS = ['core outward', 'periphery inward', 'exposures and host']
  .concat(P === 'max' ? ['dangerous if missed', 'two diseases at once'] : [])
  .slice(0, P === 'standard' ? 2 : undefined)

phase('Fact base')
const facts = await parallel(DOMAINS.map(d => () =>
  blind(`Role: fact-base extractor for the domain "${d}", as in roles.md. Return the full write-up.`, { label: `facts:${d.split(':')[0]}`, phase: 'Fact base' })))
out.facts = DOMAINS.map((d, i) => ({ domain: d, text: facts[i] }))
const factText = out.facts.filter(f => f.text).map(f => `## Fact base: ${f.domain}\n${f.text}`).join('\n\n')

const GEN_SCHEMA = { type: 'object', required: ['entry_point', 'hypotheses'], properties: {
  entry_point: { type: 'string' }, unexplained_findings: { type: 'array', items: { type: 'string' } },
  hypotheses: { type: 'array', items: { type: 'object', required: ['hypothesis', 'fit', 'conflict', 'tests_already_bearing'], properties: {
    hypothesis: { type: 'string' }, is_mechanism: { type: 'boolean' }, fit: { type: 'string' }, conflict: { type: 'string' }, tests_already_bearing: { type: 'string' } } } } } }

phase('Generators')
const gens = await parallel(GENERATORS.map(g => () =>
  blind(`Role: hypothesis generator, entry point "${g}", as in roles.md. You have not seen any other generator's list. Fact base from the extractors:\n\n${factText}`,
    { label: `gen:${g}`, phase: 'Generators', schema: GEN_SCHEMA })))
out.generators = gens.filter(Boolean)

const TRIAGE_SCHEMA = { type: 'object', required: ['families', 'merges'], properties: {
  merges: { type: 'array', items: { type: 'string' } },
  families: { type: 'array', items: { type: 'object', required: ['family', 'hypotheses'], properties: {
    family: { type: 'string' }, hypotheses: { type: 'array', items: { type: 'string' } } } } } } }

phase('Triage')
const triage = await blind(`Role: triage, as in roles.md. ${P === 'standard' ? 'Group the families into three investigator groups.' : ''} Generator outputs:\n${JSON.stringify(out.generators)}`,
  { label: 'triage', phase: 'Triage', schema: TRIAGE_SCHEMA })
out.triage = triage

const ROW = { type: 'object', required: ['hypothesis', 'family', 'status', 'confidence_in_status', 'probability_band', 'stakes', 'one_line', 'strongest_for', 'strongest_against', 'next_tests'], properties: {
  hypothesis: { type: 'string' }, family: { type: 'string' },
  status: { enum: ['excluded', 'unlikely', 'open', 'supported', 'untested'] },
  confidence_in_status: { enum: ['low', 'moderate', 'high'] }, probability_band: { enum: ['very low', 'low', 'moderate', 'high'] },
  stakes: { enum: ['low', 'moderate', 'high'] }, one_line: { type: 'string' }, strongest_for: { type: 'string' }, strongest_against: { type: 'string' },
  test_adequacy_issues: { type: 'string' }, shares_failure_mode_with: { type: 'array', items: { type: 'string' } },
  next_tests: { type: 'array', items: { type: 'object', required: ['test', 'burden', 'discriminates'], properties: {
    test: { type: 'string' }, specimen_or_procedure: { type: 'string' }, burden: { type: 'string' }, discriminates: { type: 'string' } } } } } }
const INV_SCHEMA = { type: 'object', required: ['write_up', 'rows'], properties: { write_up: { type: 'string' }, rows: { type: 'array', items: ROW } } }

phase('Investigators')
const families = (triage && triage.families) || []
const inv = await parallel(families.map(f => () =>
  blind(`Role: investigator for the family "${f.family}", as in roles.md. Hypotheses: ${JSON.stringify(f.hypotheses)}.\n\nFact base:\n${factText}`,
    { label: `inv:${f.family}`, phase: 'Investigators', schema: INV_SCHEMA })))
out.investigators = inv.filter(Boolean)
let ledger = out.investigators.flatMap(r => r.rows)

const RT_SCHEMA = { type: 'object', required: ['role', 'write_up', 'challenges', 'new_hypotheses'], properties: {
  role: { type: 'string' }, write_up: { type: 'string' }, new_hypotheses: { type: 'array', items: { type: 'string' } },
  challenges: { type: 'array', items: { type: 'object', required: ['target', 'claim', 'severity', 'proposed_change'], properties: {
    target: { type: 'string' }, claim: { type: 'string' }, severity: { enum: ['low', 'moderate', 'high'] }, proposed_change: { type: 'string' } } } } } }
const ROLES = P === 'standard' ? ['combined: attack the leader, the exclusions, and the framing, then run the completeness critique']
  : ['attack-leader', 'attack-exclusions', 'attack-framing', 'completeness']

phase('Red team')
const rt = await parallel(ROLES.map(r => () =>
  blind(`Role: red team, ${r}, as in roles.md. Do not manufacture doubt the records do not support. Ledger:\n${JSON.stringify(ledger)}`,
    { label: `redteam:${r.split(':')[0]}`, phase: 'Red team', schema: RT_SCHEMA })))
out.redTeam = rt.filter(Boolean)
const fresh = [...new Set(out.redTeam.flatMap(r => r.new_hypotheses))]

phase('Second round')
if (fresh.length && P !== 'standard') {
  const r2 = await blind(`Role: second round, as in roles.md. New hypotheses: ${JSON.stringify(fresh)}. Existing ledger:\n${JSON.stringify(ledger)}`,
    { label: 'second-round', phase: 'Second round', schema: INV_SCHEMA })
  if (r2) { out.secondRound = r2; ledger = ledger.concat(r2.rows) }
} else if (fresh.length) {
  log(`Standard preset: ${fresh.length} red-team hypotheses go to the synthesizer instead of a second-round investigator`)
  out.unexaminedNewHypotheses = fresh
}

phase('Test plan')
out.testPlan = P === 'standard' ? null : await blind(`Role: test planner, as in roles.md. Ledger:\n${JSON.stringify(ledger)}\n\nRed-team challenges:\n${JSON.stringify(out.redTeam.map(r => r.challenges))}`,
  { label: 'test-planner', phase: 'Test plan' })
out.ledger = ledger
out.urgent = [facts, out.investigators.map(i => i.write_up), out.redTeam.map(r => r.write_up)].flat()
  .filter(t => typeof t === 'string' && t.includes('URGENT')).length
return out
