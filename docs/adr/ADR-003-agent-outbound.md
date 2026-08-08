# ADR-003: Agents initiate outbound connections

Status: Accepted

Managed sites do not require inbound administrative ports. Agents connect outward to Agent Gateway over authenticated TLS. This reduces exposure and supports NAT/remote users.
