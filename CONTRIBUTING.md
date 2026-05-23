# Contributing

Thanks for contributing to ngoviet projects!

## Development Setup

1. Fork the repo
2. Clone your fork
3. Create a branch: `git checkout -b feature/your-feature`
4. Make changes
5. Test locally
6. Push and open a PR

## For Home Assistant integrations

- Run `python -m hassfest` to validate manifests
- Run `python -m pytest` for tests
- Test with a local HA instance before submitting

## For ESPHome projects

- Validate YAML: `esphome config your-device.yaml`
- Compile test: `esphome compile your-device.yaml`
- Test on real hardware before submitting

## Pull Request Guidelines

- Keep PRs focused and small
- Follow existing code style
- Update documentation if needed
- Add tests for new features
