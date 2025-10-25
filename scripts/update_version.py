#!/usr/bin/env python3
"""
Update version across all files in MenuMind AI project.

Usage:
    python scripts/update_version.py 1.0.0
    python scripts/update_version.py 0.9.1
    
This script will:
1. Update backend/__init__.py
2. Update backend/settings.py
3. Update frontend/package.json
4. Update frontend/src/config/version.ts
5. Update build date to today

Author: Alexey Kozlov
"""

import sys
import re
from datetime import date
from pathlib import Path


def update_version(new_version):
    """Update version in all relevant files."""

    print(f"📦 Updating MenuMind AI to version {new_version}...")
    print("=" * 60)

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent

    today = date.today().isoformat()

    # 1. Update backend/__init__.py
    update_file(
        project_root / 'backend' / 'menumine_ai' / '__init__.py',
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"'
    )

    # 2. Update backend/settings.py
    update_file(
        project_root / 'backend' / 'menumine_ai' / 'settings.py',
        r'APP_VERSION = "[^"]+"',
        f'APP_VERSION = "{new_version}"'
    )

    # Parse version components
    parts = new_version.split('.')
    if len(parts) == 3:
        major, minor, patch = parts
        update_file(
            project_root / 'backend' / 'menumine_ai' / 'settings.py',
            r'VERSION_MAJOR = \d+',
            f'VERSION_MAJOR = {major}'
        )
        update_file(
            project_root / 'backend' / 'menumine_ai' / 'settings.py',
            r'VERSION_MINOR = \d+',
            f'VERSION_MINOR = {minor}'
        )
        update_file(
            project_root / 'backend' / 'menumine_ai' / 'settings.py',
            r'VERSION_PATCH = \d+',
            f'VERSION_PATCH = {patch}'
        )

    # 3. Update frontend/package.json
    update_file(
        project_root / 'frontend' / 'package.json',
        r'"version": "[^"]+"',
        f'"version": "{new_version}"'
    )

    # 4. Update frontend version config
    update_file(
        project_root / 'frontend' / 'src' / 'config' / 'version.ts',
        r"APP_VERSION = '[^']+'",
        f"APP_VERSION = '{new_version}'"
    )

    # Update build date
    update_file(
        project_root / 'frontend' / 'src' / 'config' / 'version.ts',
        r"APP_BUILD_DATE = '[^']+'",
        f"APP_BUILD_DATE = '{today}'"
    )

    # Update version components in version.ts
    if len(parts) == 3:
        update_file(
            project_root / 'frontend' / 'src' / 'config' / 'version.ts',
            r'major: \d+',
            f'major: {major}'
        )
        update_file(
            project_root / 'frontend' / 'src' / 'config' / 'version.ts',
            r'minor: \d+',
            f'minor: {minor}'
        )
        update_file(
            project_root / 'frontend' / 'src' / 'config' / 'version.ts',
            r'patch: \d+',
            f'patch: {patch}'
        )

    print("=" * 60)
    print(f"✅ Version updated to {new_version}")
    print(f"📅 Build date set to {today}")
    print()
    print("📋 Next steps:")
    print(f"1. Review changes: git diff")
    print(f"2. Update CHANGELOG.md with release notes")
    print(f"3. Test the application")
    print(f"4. Commit changes: git commit -am 'Bump version to {new_version}'")
    print(
        f"5. Create tag: git tag -a v{new_version} -m 'Release version {new_version}'")
    print(f"6. Push: git push && git push --tags")
    print()


def update_file(filepath, pattern, replacement):
    """Update a file with regex replacement."""
    try:
        if not filepath.exists():
            print(f"  ⚠️  File not found: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if pattern exists
        if not re.search(pattern, content):
            print(f"  ⚠️  Pattern not found in {filepath.name}")
            return

        new_content = re.sub(pattern, replacement, content)

        # Only write if content changed
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"  ✓ Updated {filepath.relative_to(Path.cwd())}")
        else:
            print(f"  - No changes needed in {filepath.name}")

    except FileNotFoundError:
        print(f"  ✗ File not found: {filepath}")
    except Exception as e:
        print(f"  ✗ Error updating {filepath.name}: {e}")


def validate_version(version):
    """Validate version format."""
    # Allow formats: X.Y.Z or X.Y.Z-suffix (e.g., 1.0.0-beta)
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'

    if not re.match(pattern, version):
        print("❌ Error: Invalid version format")
        print()
        print("Valid formats:")
        print("  - 1.0.0          (Release version)")
        print("  - 0.9.0          (Pre-release version)")
        print("  - 1.0.0-alpha    (Alpha version)")
        print("  - 1.0.0-beta     (Beta version)")
        print("  - 1.0.0-rc1      (Release candidate)")
        print()
        return False

    return True


def show_usage():
    """Show usage instructions."""
    print("📘 MenuMind AI Version Update Script")
    print()
    print("Usage:")
    print("  python scripts/update_version.py <version>")
    print()
    print("Examples:")
    print("  python scripts/update_version.py 1.0.0")
    print("  python scripts/update_version.py 0.9.1")
    print("  python scripts/update_version.py 1.0.0-beta")
    print()
    print("Version Format: MAJOR.MINOR.PATCH[-suffix]")
    print()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        show_usage()
        sys.exit(1)

    version = sys.argv[1]

    # Validate version format
    if not validate_version(version):
        sys.exit(1)

    # Confirmation
    print(f"⚠️  About to update MenuMind AI to version {version}")
    print("This will modify the following files:")
    print("  - backend/menumine_ai/__init__.py")
    print("  - backend/menumine_ai/settings.py")
    print("  - frontend/package.json")
    print("  - frontend/src/config/version.ts")
    print()

    response = input("Continue? [y/N]: ").strip().lower()

    if response != 'y':
        print("❌ Cancelled")
        sys.exit(0)

    print()
    update_version(version)
