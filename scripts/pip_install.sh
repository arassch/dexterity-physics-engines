#!/usr/bin/env bash
# Install one of a short list of Python packages into Isaac Lab's Python (user site). Anything else is refused.
# Usage: scripts/pip_install.sh <cma|matplotlib>
set -euo pipefail
PKG="${1:?usage: pip_install.sh <cma|matplotlib>}"
case "$PKG" in cma|matplotlib) ;; *) echo "not on the list: $PKG (edit scripts/pip_install.sh to add it)" >&2; exit 1 ;; esac
cd "${ISAACLAB_DIR:-/workspace/isaaclab}"
./isaaclab.sh -p -m pip install --user "$PKG"
