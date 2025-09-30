# Tests Directory

This directory contains test scripts, debug utilities, and verification tools for the RepoReadme application.

## 📁 Directory Structure

### Test Scripts (`test_*.py`)
- `test_cost_tracking.py` - Tests OpenRouter cost calculation accuracy
- `test_credential_management.py` - Tests credential saving/loading
- `test_openrouter_persistence.py` - Tests OpenRouter API key persistence
- `test_settings_keys.py` - Tests settings configuration keys
- `test_simple_credentials.py` - Basic credential functionality tests
- `test_enhancement_fix.py` - Tests OpenRouter enhancement fixes
- `test_save_fix.py` - Tests credential save functionality
- `test_final_persistence.py` - Comprehensive persistence verification
- `test_ai_bio_logging.py` - Tests AI bio logging functionality
- `test_log_message_fix.py` - Verifies log_message method fixes
- `test_integration.py` - Integration tests for core features
- `test_unified_workflow.py` - End-to-end workflow tests

### Debug Scripts (`debug_*.py`)
- `debug_settings.py` - Debug settings loading/saving issues
- `debug_github_username.py` - Debug GitHub API connectivity

### Fix Scripts (`fix_*.py`)
- `fix_github_token.py` - Fix corrupted GitHub tokens

## 🚀 Running Tests

### Individual Tests
```bash
python tests/test_cost_tracking.py
python tests/test_credential_management.py
python tests/test_openrouter_persistence.py
```

### Debug Tools
```bash
python tests/debug_settings.py
python tests/debug_github_username.py
```

### Fix Utilities
```bash
python tests/fix_github_token.py
```

## 📋 Test Categories

### 🔐 **Credential Management**
- Credential persistence across app restarts
- GitHub token and username saving
- OpenRouter API key storage
- Settings file integrity

### 💰 **Cost Tracking**
- OpenRouter API cost calculation
- Token usage tracking
- Actual vs estimated costs
- Pricing database accuracy

### 🤖 **AI Features**
- Bio generation functionality
- Enhancement with OpenRouter
- Logging system fixes
- Error handling

### ⚙️ **Core Functionality**
- Settings management
- GitHub API integration
- Application startup
- Error handling

## 🧪 Test Status

All tests should pass for a healthy application state. If any test fails, check the specific error messages and fix the underlying issue before proceeding.

## 📝 Adding New Tests

When adding new functionality, create corresponding test files following the naming convention:
- `test_[feature_name].py` for feature tests
- `debug_[issue_name].py` for debugging tools
- `fix_[problem_name].py` for one-time fixes