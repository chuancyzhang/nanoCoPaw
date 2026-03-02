# Security Policy

nanoCoPaw is designed for a single trusted operator on a local machine.

## Trust Model

- One user, one machine, one binary  
- Anyone who can run the binary is trusted  
- Channel credentials are entered at launch and not persisted  

## Reporting

If you discover a security issue, open a private report or contact the maintainers.

Include:

- Environment  
- Repro steps  
- Demonstrated impact  

## Out of Scope

- Multi-tenant isolation  
- Shared-host untrusted operators  
- Attacks that require local code modification by the operator  
