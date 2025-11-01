# Linting and Formatting Guide

## **How the Linting System Works**

### **CI/CD Pipeline (GitHub Actions)**

The `.github/workflows/lint.yaml` workflow now:

1. ✅ **Runs `ruff check`** - Validates code quality, imports, complexity, etc.
2. ✅ **Runs `ruff format`** - Automatically formats the code
3. ✅ **Auto-commits formatting changes** - Pushes formatted code back to the repo
4. 🚫 **No more failed builds** due to formatting issues!

### **Local Development Options**

#### **Option 1: Manual Formatting (Easiest)**
```powershell
# Windows PowerShell
.\scripts\format.ps1

# Or directly with ruff
ruff format .
ruff check . --fix
```

#### **Option 2: Pre-commit Hooks (Automatic)**
```bash
# Install pre-commit (one time setup)
pip install pre-commit
pre-commit install

# Now formatting happens automatically on every commit!
git commit -m "My changes"  # <- Formatting runs automatically
```

#### **Option 3: IDE Integration**

**VS Code:**
1. Install the "Ruff" extension
2. Add to your settings.json:
```json
{
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit"
        }
    }
}
```

**PyCharm:**
1. Go to Settings → Tools → External Tools
2. Add Ruff as an external tool
3. Set up file watchers for auto-formatting

## **What Changed**

### **Before (Problems):**
- CI would **fail** if code wasn't perfectly formatted
- Developers had to manually run formatting
- Inconsistent formatting between local and CI

### **After (Solutions):**
- CI **auto-formats and commits** formatting changes
- Multiple local development options available
- Consistent formatting everywhere

## **Ruff Configuration**

All configuration is in `pyproject.toml`:

```toml
[tool.ruff.lint]
select = [
    "E",       # pycodestyle errors
    "F",       # pyflakes
    "I",       # isort
    "UP",      # pyupgrade
    # ... more rules
]

ignore = [
    "E501",    # line too long (let formatter handle this)
    # ... other ignored rules
]
```

## **Workflow Benefits**

🚫 **No More Failed Builds** - Formatting is automatic  
⚡ **Faster Development** - No manual formatting needed  
🎯 **Consistent Code Style** - Same formatting everywhere  
🔧 **Flexible Local Options** - Choose your preferred workflow  

## **Troubleshooting**

### **"Files would be reformatted" Error**
This should no longer happen with the new auto-commit workflow. If it does:

```powershell
# Run formatting locally
.\scripts\format.ps1

# Commit the changes
git add .
git commit -m "Fix formatting"
git push
```

### **Pre-commit Hook Issues**
```bash
# Skip hooks if needed (not recommended)
git commit --no-verify -m "Emergency commit"

# Update hooks
pre-commit autoupdate

# Manually run hooks
pre-commit run --all-files
```

The key improvement is that the **CI pipeline now fixes formatting automatically** instead of just complaining about it!