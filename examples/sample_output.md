# Output Directory

This directory contains generated README files from RepoReadme.

## Structure

- Generated README files are saved here by default
- Files are typically named `README.md` or with repository-specific names
- Backup files are created when overwriting existing README files

## Configuration

The output directory can be configured in `config/settings.json`:

```json
{
  "output": {
    "default_filename": "README.md",
    "backup_existing": true,
    "output_directory": "./output",
    "create_subdirectories": false
  }
}
```

## Generated Files

Generated README files will appear here after running the RepoReadme analysis and generation process.