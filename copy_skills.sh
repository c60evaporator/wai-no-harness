#!/bin/bash
# Copy all skills from this repository to ~/.claude/skills/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/skills"
DEST_DIR="$HOME/.claude/skills"

echo "Copying skills from $SRC_DIR to $DEST_DIR ..."

for skill_dir in "$SRC_DIR"/*/; do
    skill_name="$(basename "$skill_dir")"
    dest="$DEST_DIR/$skill_name"

    cp -r "$skill_dir" "$dest"
    echo "  Copied: $skill_name"
done

echo "Done."
