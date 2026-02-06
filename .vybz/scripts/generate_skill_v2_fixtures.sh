#!/bin/sh
# scripts/generate_skill_v2_fixtures.sh
# Generates filesystem fixtures for testing the AgentSkills.io (v2) implementation.
# Covers scenarios defined in blueprints/agentskills/agentskillsio-standard-phase-1-implementation.md

set -e # Fail fast

# Define the target directory for test fixtures
# We use a distinct directory to avoid confusing existing tests
TARGET_DIR="tests/fixtures/skills_v2"

echo ">> Setting up test fixtures in $TARGET_DIR..."

# 1. Clean Slate
if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
fi
mkdir -p "$TARGET_DIR"

# -----------------------------------------------------------------------------
# Scenario 1: The Happy Path
# A fully compliant skill with metadata, instructions, and resources.
# -----------------------------------------------------------------------------
SKILL_NAME="valid-skill"
SKILL_PATH="$TARGET_DIR/$SKILL_NAME"

echo "   [+] Creating '$SKILL_NAME' (Valid structure with resources)..."
mkdir -p "$SKILL_PATH/scripts"
mkdir -p "$SKILL_PATH/references"

# Create SKILL.md
cat <<EOF > "$SKILL_PATH/SKILL.md"
---
name: $SKILL_NAME
description: A compliant skill for testing resource discovery.
---
# Instructions
This is the primary instruction block for the valid skill.
It should be rendered first.
EOF

# Create Resources (for testing recursive discovery)
cat <<EOF > "$SKILL_PATH/scripts/utils.py"
def hello():
    print("Hello from skill script")
EOF

cat <<EOF > "$SKILL_PATH/references/api_docs.md"
# API Documentation
This is a reference file that should be listed in the prompt.
EOF

# -----------------------------------------------------------------------------
# Scenario 2: The Name Mismatch (Spec Violation)
# The directory name does not match the YAML 'name' field.
# -----------------------------------------------------------------------------
SKILL_NAME="mismatched-skill"
SKILL_PATH="$TARGET_DIR/$SKILL_NAME"

echo "   [+] Creating '$SKILL_NAME' (Invalid: Directory != YAML Name)..."
mkdir -p "$SKILL_PATH"

cat <<EOF > "$SKILL_PATH/SKILL.md"
---
name: wrong-name-entirely
description: This skill should raise a ValueError upon loading.
---
# Instructions
You should not see this.
EOF

# -----------------------------------------------------------------------------
# Scenario 3: Malformed YAML
# Tests the resilience of the parser.
# -----------------------------------------------------------------------------
SKILL_NAME="broken-yaml-skill"
SKILL_PATH="$TARGET_DIR/$SKILL_NAME"

echo "   [+] Creating '$SKILL_NAME' (Invalid: Corrupt Frontmatter)..."
mkdir -p "$SKILL_PATH"

cat <<EOF > "$SKILL_PATH/SKILL.md"
---
name: $SKILL_NAME
description: [ This list is never closed
---
# Instructions
Parsing this should raise a YAMLError (or ValueError wrapper).
EOF

# -----------------------------------------------------------------------------
# Scenario 4: Missing SKILL.md
# Tests FileNotFoundError.
# -----------------------------------------------------------------------------
SKILL_NAME="ghost-skill"
SKILL_PATH="$TARGET_DIR/$SKILL_NAME"

echo "   [+] Creating '$SKILL_NAME' (Invalid: Empty Directory)..."
mkdir -p "$SKILL_PATH"
# Intentionally creating an empty directory

# -----------------------------------------------------------------------------
# Scenario 5: Nested Content (Future Proofing)
# Tests if the loader can handle subdirectories with markdown content
# -----------------------------------------------------------------------------
SKILL_NAME="nested-skill"
SKILL_PATH="$TARGET_DIR/$SKILL_NAME"

echo "   [+] Creating '$SKILL_NAME' (Valid: Nested Markdown content)..."
mkdir -p "$SKILL_PATH/advanced"

cat <<EOF > "$SKILL_PATH/SKILL.md"
---
name: $SKILL_NAME
description: Testing nested content aggregation.
---
# Root Instructions
EOF

cat <<EOF > "$SKILL_PATH/advanced/details.md"
# Advanced Details
This content should be appended to the instructions.
EOF

echo ""
echo ">> Fixture generation complete."
echo "   Location: $(pwd)/$TARGET_DIR"

