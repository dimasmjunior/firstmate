#!/usr/bin/env bash
if [ "${1-}" = -a ] && [ "${2-}" = 256 ]; then
  shift 2
  exec sha256sum "$@"
fi
exit 2
