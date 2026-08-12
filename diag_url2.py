"""
Show URL structure to understand the @ positions.
Helps craft the fix without printing password.
"""
from urllib.parse import urlparse, quote

env_path = r"d:\Flutter\Library Management System\Backend\.env"

db_line = None
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n\r")
        if line.startswith("DATABASE_URL="):
            db_line = line
            break

raw = db_line[len("DATABASE_URL="):]

# Find positions of @ signs
at_positions = [i for i, c in enumerate(raw) if c == "@"]
print(f"URL length: {len(raw)}")
print(f"@ at positions: {at_positions}")

# The scheme+credentials part ends at last @
# scheme = up to ://
# credentials = username:password
# The URL format: scheme://username:password@host:port/db
# If password has @, urlparse will misparse

parsed_native = urlparse(raw)
print(f"\nurlparse (native, broken if @ in password):")
print(f"  username: {parsed_native.username}")
print(f"  hostname: {parsed_native.hostname}")
print(f"  port: {parsed_native.port}")
pw = parsed_native.password
if pw:
    print(f"  password: [MASKED len={len(pw)} contains_@={'@' in pw}]")

# Manual parsing: everything between :// and last @ is user:password
scheme_end = raw.find("://")
scheme = raw[:scheme_end]
remainder = raw[scheme_end+3:]
last_at = remainder.rfind("@")
userinfo = remainder[:last_at]
hostinfo = remainder[last_at+1:]

colon_pos = userinfo.find(":")
username = userinfo[:colon_pos]
password_raw = userinfo[colon_pos+1:]

print(f"\nManual parsing:")
print(f"  scheme  : {scheme}")
print(f"  username: {username}")
print(f"  password: [MASKED len={len(password_raw)} contains_@={'@' in password_raw}]")
print(f"  hostinfo: {hostinfo}")

# Show what percent-encoding the password would look like
encoded_pw = quote(password_raw, safe="")
fixed_url = f"{scheme}://{username}:{encoded_pw}@{hostinfo}"
print(f"\nFixed URL (password percent-encoded, masked):")
masked_fixed = fixed_url.replace(f":{encoded_pw}@", ":****@")
print(f"  {masked_fixed}")

# Verify the fix parses correctly
parsed_fixed = urlparse(fixed_url)
print(f"\nurlparse of FIXED URL:")
print(f"  username: {parsed_fixed.username}")
print(f"  hostname: {parsed_fixed.hostname}")
print(f"  port    : {parsed_fixed.port}")
print(f"  path    : {parsed_fixed.path}")
pw2 = parsed_fixed.password
if pw2:
    print(f"  password: [MASKED len={len(pw2)} contains_@={'@' in pw2}]")
    # Verify password round-trips correctly
    from urllib.parse import unquote
    decoded_pw = unquote(pw2)
    print(f"  password round-trip matches original: {decoded_pw == password_raw}")
