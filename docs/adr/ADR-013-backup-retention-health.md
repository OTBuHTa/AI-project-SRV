# ADR-013 — Backup retention and storage health

## Decision

AI-project SRV manages backup retention independently from backup creation.

Retention protects the newest backups while removing artifacts that exceed the configured age policy.

Backup storage is accessed through a storage adapter. NAS support uses an operating-system mounted filesystem rather than embedding SMB/NFS credentials in the application.

## Safety

- cleanup may only delete files contained within the configured backup root
- the newest configured number of artifacts are always protected
- restore verification remains independent from retention
- NAS credentials and mount lifecycle remain outside the API process
- storage health checks verify basic read/write availability without modifying production data
