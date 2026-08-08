# ADR-004: Approval-based mutations

Status: Accepted

Read-only diagnostics may execute automatically subject to RBAC. Mutating operations are represented as typed capabilities, evaluated by policy and may require explicit approval. Arbitrary root shell execution is not a platform capability.
