"""
Safe URL diagnostic script - never prints the password.
Run from: d:\Flutter\Library Management System\Backend\
"""
from urllib.parse import urlparse
import sys

env_path = r"d:\Flutter\Library Management System\Backend\.env"

db_line = None
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n").rstrip("\r")
        if line.startswith("DATABASE_URL="):
            db_line = line
            break

if not db_line:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

raw = db_line[len("DATABASE_URL="):]

print(f"Raw URL length: {len(raw)}")
print(f"Number of '@' in URL: {raw.count('@')}")
print(f"Starts with 'postgresql://': {raw.startswith('postgresql://')}")
print(f"Starts with 'postgres://': {raw.startswith('postgres://')}")
print(f"Starts with 'postgresql+asyncpg://': {raw.startswith('postgresql+asyncpg://')}")

# Count @ signs and show what comes after each
at_positions = [i for i, c in enumerate(raw) if c == "@"]
print(f"@ sign positions: {at_positions}")

# Show scheme and everything after LAST @
last_at = raw.rfind("@")
after_last_at = raw[last_at + 1:]
print(f"Host:port:db after last '@': {after_last_at}")

# Use urlparse
try:
    parsed = urlparse(raw)
    print(f"\nurlparse results:")
    print(f"  scheme   : {parsed.scheme}")
    print(f"  username : {parsed.username}")
    print(f"  hostname : {parsed.hostname}")
    print(f"  port     : {parsed.port}")
    print(f"  path/db  : {parsed.path}")
    pw = parsed.password
    if pw:
        at_in_pw = "@" in pw
        pct_in_pw = "%" in pw
        print(f"  password : [MASKED - len={len(pw)}, contains_@={at_in_pw}, contains_%={pct_in_pw}]")
    else:
        print(f"  password : [EMPTY or None]")
except Exception as e:
    print(f"urlparse error: {e}")

# Check for hidden characters (BOM, CRLF embedded, non-ASCII)
non_ascii = [(i, hex(ord(c))) for i, c in enumerate(raw) if ord(c) > 127]
if non_ascii:
    print(f"\nWARNING: Non-ASCII chars found at positions: {non_ascii}")
else:
    print("\nNo non-ASCII characters found in URL.")

# Check for leading/trailing whitespace
if raw != raw.strip():
    print(f"WARNING: URL has leading/trailing whitespace: repr={repr(raw[:5])}...{repr(raw[-5:])}")
else:
    print("No leading/trailing whitespace in URL.")
