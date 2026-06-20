# Security Policy

OneEpis is a clinical software scaffold. It is public for early development visibility, but it is not ready for production healthcare use.

## Supported Scope

Security review currently applies to the `main` branch only.

## Do Not Publish Sensitive Data

Do not open public issues, pull requests, discussions, screenshots, logs, fixtures, seeds, or examples that include:

- real patient data or protected health information
- national identifiers, RUT, passport numbers, insurance IDs, or similar identifiers
- clinical documents, lab reports, images, prescriptions, or free-text notes from real care
- credentials, tokens, database dumps, production URLs, or private infrastructure details

Use obviously fictional demo data only.

## Reporting a Vulnerability

Because this repository may be public, do not disclose vulnerabilities with sensitive detail in a public issue.

Preferred flow:

1. Contact the maintainer privately through the GitHub account `gabriel2320`.
2. Share a minimal description, affected area, reproduction steps, and impact.
3. Avoid including real clinical data. Use synthetic examples.

If private contact is not available, open a public issue with only a high-level note such as "Potential security issue in authentication boundary" and ask for a private channel.

## Clinical Safety Boundaries

Current status:

- no production authentication or authorization
- no encryption-at-rest design completed
- no production backup or retention policy
- no legal/compliance review
- no AI clinical decision support approval

AI modules must remain assistive and review-only until explicit safety, audit, and governance controls are implemented.

## Maintainer Checklist Before Production

- role-based access control
- audit log hardening
- PHI-safe logging and observability
- secrets management
- encryption strategy
- backup and restore drills
- vulnerability scanning
- dependency review
- legal and clinical governance review
