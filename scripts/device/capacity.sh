#!/bin/bash
# Read-only capacity probe; host can stream this before any device directory write.
PORT_ROOT=$1
df -Pk "$PORT_ROOT" || true
df -Pi "$PORT_ROOT" || true
