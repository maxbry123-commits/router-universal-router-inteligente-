#!/bin/sh
# build.sh — Build del proyecto Vercel: copia el frontend canonico al output.
set -e
python3 build_public.py || python3 vercel/build_public.py
