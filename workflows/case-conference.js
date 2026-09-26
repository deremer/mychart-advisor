export const meta = {
  name: 'case-conference',
  description: 'mychart-advisor case conference: panel seats in parallel, investigator, synthesizer, second reader',
  whenToUse: 'Only from the case-conference skill, for users who opted into multi-agent workflows. Pass args {caseDir, date, mode, seats: [slug...]}.',
  phases: [
    { title: 'Seats', detail: 'one agent per panel seat plus generalist and evidence researcher' },
    { title: 'Investigator' },
    { title: 'Synthesis' },
    { title: 'Verification' },
  ],
}

// args: { caseDir, date, mode: 'standard'|'fresh', seats: ['oncology', ...], literatureQuestions: [..] }
const A = args || {}
const dir = `${A.caseDir}/analysis/conference/${A.date}`
const refs = 'the case-conference roles reference (skills/case-conference/references/roles.md in the mychart-advisor plugin)'
const common = `You are working in the case folder ${A.caseDir}. Read ${dir}/inputs.md for the mode (${A.mode}) and your reading list, and follow only that list plus any text file under analysis/data/. Follow the shared seat rules in ${refs}.`

const units = [
  ...(A.seats || []).map(s => ({ slug: s, prompt: `${common} Your seat brief is ${A.caseDir}/panel/seats/${s}.md. Write your assessment to ${dir}/${s}.md, then return a five-line summary.` })),
  { slug: 'generalist', prompt: `${common} You are the clinical generalist, briefed in section 2 of ${refs}. Write ${dir}/generalist.md, then return a five-line summary.` },
  { slug: 'evidence-researcher', prompt: `${common} You are the evidence researcher, briefed in section 3 of ${refs}. Answer these questions: ${JSON.stringify(A.literatureQuestions || [])}. Search general clinical terms only, with no identifiers. Write ${dir}/evidence-researcher.md, then return a five-line summary.` },
]

phase('Seats')
const summaries = await parallel(units.map(u => () => agent(u.prompt, { label: `seat:${u.slug}`, phase: 'Seats' })))
const done = units.filter((u, i) => summaries[i]).map(u => `${dir}/${u.slug}.md`)
const skipped = units.filter((u, i) => !summaries[i]).map(u => u.slug)
if (skipped.length) log(`Seats that did not finish: ${skipped.join(', ')}`)

phase('Investigator')
await agent(`${common} You are the investigator, briefed in section 4 of ${refs}. Read every seat file: ${done.join(', ')}. Write ${dir}/investigator.md and return your three one-minute points.`, { label: 'investigator', phase: 'Investigator' })

phase('Synthesis')
await agent(`${common} You are the synthesizer, briefed in section 5 of ${refs}. Read ${done.join(', ')} and ${dir}/investigator.md. Write ${dir}/conference-note.md. Return the section 1 paragraph.`, { label: 'synthesizer', phase: 'Synthesis' })

phase('Verification')
const verdict = await agent(`${common} You are the second reader, briefed in section 6 of ${refs}. Check ${dir}/conference-note.md and write ${dir}/verification.md. Return the tally line.`, { label: 'second-reader', phase: 'Verification' })

return { seatsRun: done.length, skipped, verification: verdict }
