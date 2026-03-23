# Contributing to SYMIONE

## What we accept

- Validation schema contributions (new proof types)
- SDK improvements (JS + Python)
- Bug fixes with tests
- Documentation corrections

## What we do not accept

- Changes to core execution primitive logic without prior discussion
- New validation tiers without spec update
- Breaking changes to API surface

## How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-schema-name`
3. Make changes
4. Run tests: `pytest apps/api/tests/`
5. Submit PR with description of what and why

## Validation schema contributions

Add to: `spec/schemas/community/`
Format: JSON matching spec/v0.1.md schema section
Include: example proof, validation criteria, test case

## Questions

Open an issue. Keep it technical.
