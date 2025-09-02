# Contributing to RepoReadme

Thank you for your interest in contributing to RepoReadme! This project uses modern Python architecture patterns and welcomes contributions that maintain its quality and extensibility.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/reporeadme.git
   cd reporeadme
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python main.py  # Test GUI
   python demo.py . --template modern  # Test CLI
   ```

## Code Style and Standards

### Code Standards and Patterns
- **Modular Architecture**: Maintain clear separation between analyzers, templates, GUI, and utilities
- **Comprehensive Logging**: Use the existing logging framework for all operations
- **Error Handling**: Include robust exception handling for all user-facing operations
- **Type Hints**: Use type annotations for all functions and class methods
- **Docstrings**: Provide clear documentation for all public methods
- **Clean Code**: Follow PEP 8 and maintain readable, maintainable code

### Code Organization
- **Analyzers** (`src/analyzers/`): Repository analysis and technology detection
- **Templates** (`src/templates/`): README generation and template management
- **GUI** (`src/gui.py`): Interface components and user interaction
- **Config** (`src/config/`): Settings and configuration management
- **Utils** (`src/utils/`): Shared utilities and helper functions

## Contributing Guidelines

### Adding New Templates
1. Follow existing template patterns in `src/templates/readme_templates.py`
2. Add template configuration options to `TemplateConfig` dataclass
3. Test with various repository types and sizes
4. Update template selection UI in GUI

### Extending Repository Analysis
1. Add new detection logic to `src/analyzers/repository_analyzer.py`
2. Update `ProjectMetadata` dataclass if new fields are needed
3. Ensure caching works correctly for new analysis features
4. Test with repositories that use the new technology

### GUI Improvements
1. Maintain consistency with existing interface design
2. Use the established threading patterns for non-blocking operations
3. Update progress tracking for new operations
4. Test thoroughly with different screen sizes

## Testing Your Changes

Since this project currently lacks automated tests, please manually test:

### Repository Types
- Python projects (with requirements.txt, setup.py, pyproject.toml)
- JavaScript/Node.js projects (with package.json)
- Java projects (with pom.xml, build.gradle)
- C/C++ projects (with Makefile, CMakeLists.txt)
- Go projects (with go.mod)
- Local directories and GitHub repositories

### Template Verification
Test all templates with your changes:
```bash
python demo.py path/to/test/repo --template modern
python demo.py path/to/test/repo --template classic
python demo.py path/to/test/repo --template minimalist
python demo.py path/to/test/repo --template developer
python demo.py path/to/test/repo --template academic
python demo.py path/to/test/repo --template corporate
```

### GUI Testing
- Repository addition (local and GitHub)
- Analysis and template generation
- Batch operations
- Settings persistence
- Error handling and user feedback

## Submitting Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow existing code patterns
   - Add appropriate logging
   - Test thoroughly

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: clear description of your changes"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request using the provided template.

## Code Review Process

1. **Automated Checks**: Ensure your code follows existing patterns
2. **Manual Review**: Maintainers will review for architecture consistency
3. **Testing**: Changes will be tested with various repository types
4. **Documentation**: Update documentation if needed

## Questions or Issues?

- Open an issue for bugs or feature requests
- Use discussions for general questions
- Follow established Python patterns and architectural best practices

## Recognition

Contributors will be acknowledged in the project README and release notes. Thank you for helping make RepoReadme better for everyone!