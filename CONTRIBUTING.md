# Contributing

Thanks for taking the time to contribute. This project is a Model Context
Protocol server for the Zoho ecosystem.

## Getting set up

```bash
git clone https://github.com/aceAaronCharles/Zoho-MCP.git
cd Zoho-MCP
make setup          # creates .venv and installs dev dependencies
cp .env.example .env
pre-commit install  # optional but recommended
```

You do not need real Zoho credentials to run the unit tests — they mock the
Zoho API. Integration scripts that call Zoho directly require a refresh token
and are not part of the test suite.

## Development workflow

```bash
make test     # pytest
make lint     # pyflakes src tests
make fmt      # black + isort
make check    # lint + test
```

* Python 3.11+ is required; CI runs 3.11, 3.12 and 3.13.
* Keep lines at 120 columns (Black/isort config is in `pyproject.toml`).
* Add or update tests for behaviour changes. Tests live in `tests/`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scopes): add a preset for a single data centre
fix(portal): reject a reused session token
docs(deploy): document the systemd backup timer
```

The scope is usually the module or area (`scopes`, `portal`, `server`,
`apps`, `deploy`, ...). Keep the subject in the imperative mood.

## Pull requests

1. Branch from `main`.
2. Make the change small and focused; one concern per pull request.
3. Ensure `make check` passes locally.
4. Describe the motivation, the behaviour change, and how you verified it.

CI (`.github/workflows/tests.yml` and `image.yml`) runs tests, lint, an image
build with a smoke test, and a container vulnerability scan.

## Reporting security issues

Please do not open a public issue for vulnerabilities — see
[SECURITY.md](SECURITY.md).

## License

By contributing you agree that your contributions are licensed under the
[MIT License](LICENSE).
