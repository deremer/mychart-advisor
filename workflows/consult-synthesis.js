export const meta = {
  name: 'consult-synthesis',
  description: 'mychart-advisor independent consult, synthesis stage: reconciler, blind synthesizer, verifiers, fixer',
  whenToUse: 'Only from the independent-consult skill after the blind stage outputs are saved to snapshot/work and prior/ is assembled. Pass args {caseDir, consultDir, snapshot, preset, agentType}.',
  phases: [{ title: 'Reconcile' }, { title: 'Synthesize' }, { title: 'Verify' }, { title: 'Fix' }],
}

// args: { caseDir, consultDir, snapshot, preset, agentType }
const A = args || {}
const P = A.preset || 'standard'
const type = A.agentType || 'mychart-advisor:blind-reader'
const pre = `Read ${A.snapshot}/AGENTS.md first and follow it exactly. Your snapshot directory is ${A.snapshot}. Role prompts are in ${A.snapshot}/_method/roles.md and the report template in ${A.snapshot}/_method/report-template.md.`

phase('Reconcile')
const reconciliation = await agent(`You are the reconciler in an independent consult, as described in ${A.snapshot}/_method/roles.md. Read the blind outputs in ${A.snapshot}/work/, then the notes in ${A.snapshot}/notes-text/, then the prior analysis in ${A.consultDir}/prior/. Return reconciliation.md content as your final message. Do not write files.`,
  { label: 'reconciler', phase: 'Reconcile', agentType: 'general-purpose' })

phase('Synthesize')
const draft = await agent(`${pre}\n\nRole: synthesizer. Read everything in ${A.snapshot}/work/. The reconciliation text is below, because you may not read prior analysis directly. Return the complete report.\n\n# Reconciliation\n${reconciliation}`,
  { label: 'synthesizer', phase: 'Synthesize', agentType: type })

const V = { type: 'object', required: ['assertions_checked', 'issues'], properties: { assertions_checked: { type: 'integer' },
  issues: { type: 'array', items: { type: 'object', required: ['location', 'exact_text', 'problem', 'severity', 'correction'], properties: {
    location: { type: 'string' }, exact_text: { type: 'string' }, problem: { type: 'string' }, severity: { enum: ['low', 'medium', 'high'] },
    correction: { type: 'string' }, evidence: { type: 'string' } } } } } }
const JOBS = P === 'standard' ? ['numbers, quotes, absence claims, literature, citations, style, and directive language']
  : P === 'max' ? ['numbers, units, ranges, dates, times, and quotations', 'absence claims, literature figures, citation integrity, style, and directive language', 'over-hedging and under-supported claims']
  : ['numbers, units, ranges, dates, times, and quotations', 'absence claims, literature figures, citation integrity, style, and directive language']

phase('Verify')
const checks = await parallel(JOBS.map(j => () =>
  agent(`${pre}\n\nRole: verifier checking ${j}. Check the report below against the snapshot text.\n\n${draft}`, { label: `verify:${j.split(',')[0]}`, phase: 'Verify', agentType: type, schema: V })))
const issues = checks.filter(Boolean).flatMap(c => c.issues)

phase('Fix')
const report = issues.length
  ? await agent(`${pre}\n\nRole: fixer. Apply each correction after confirming it against the snapshot source. Return the corrected report in full.\n\nCorrections:\n${JSON.stringify(issues)}\n\nReport:\n${draft}`,
    { label: 'fixer', phase: 'Fix', agentType: type })
  : draft

return { reconciliation, report, verification: { checked: checks.filter(Boolean).reduce((n, c) => n + c.assertions_checked, 0), issues } }
