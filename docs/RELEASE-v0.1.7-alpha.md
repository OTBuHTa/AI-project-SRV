# AI-project SRV v0.1.7-alpha

## Backup lifecycle management

Added:

- backup retention policy
- protected newest-backup count
- maximum backup age
- backup cleanup service
- backup health evaluator
- local/NAS-mounted storage backend selection
- storage read/write health probe
- path containment protection for backup deletion
- backup health API
- cleanup API
- storage health API

## Validation

Retention, health, cleanup and storage backend behavior are covered by automated tests.
