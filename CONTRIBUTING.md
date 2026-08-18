# Contribution guide for Orthos 2

Please try to create issues for any feature that you need or issue that you encounter.

Please be aware that this project is in maintenance mode. We still welcome contributions to stabilize this project! For more details, see: <https://github.com/openSUSE/orthos2/issues/219>

## Commit messages

Orthos 2 follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must be structured as:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Purpose                                                    |
|------------|-------------------------------------------------------------|
| `feat`     | A new feature                                                |
| `fix`      | A bug fix                                                    |
| `docs`     | Documentation only changes                                   |
| `style`    | Formatting, whitespace, etc. (no code meaning change)        |
| `refactor` | Code change that neither fixes a bug nor adds a feature      |
| `perf`     | A code change that improves performance                      |
| `test`     | Adding or correcting tests                                   |
| `build`    | Changes to the build system or dependencies                  |
| `ci`       | Changes to CI configuration/scripts                          |
| `chore`    | Other changes that don't modify src or test files             |

### Enforcement

This is enforced in two places:

- **Locally**, via a `pre-commit` `commit-msg` hook. If you already have `pre-commit` set up for this repo, run `pre-commit install --hook-type commit-msg` once (in addition to your existing `pre-commit install`) to start linting your commit messages before they're created.
- **In CI**, via the `commitlint` job in the "Coding Style" workflow, which runs on every pull request.

For security issues and the Code of Conduct please refer to the dedicated documents.
