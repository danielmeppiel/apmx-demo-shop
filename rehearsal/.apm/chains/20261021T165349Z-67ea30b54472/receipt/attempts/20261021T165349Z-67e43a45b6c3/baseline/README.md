# Hermetic rehearsal input

`factory.yml` with `mode=hermetic-rehearsal` runs apmx's protocol fixture
package against this directory: a stand-in agent copies `notes.md` to
`handoff.json`, with no model. The CI check job, the signature and the
`apmx audit` gate are the real ones.
