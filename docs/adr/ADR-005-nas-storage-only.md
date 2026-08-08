# ADR-005: NAS is storage/backup only

Status: Accepted

The NAS is not part of the control plane. It receives encrypted backups, archives, model artifacts and retained logs. Loss of NAS availability must not stop core control-plane operations.
