#!/bin/sh
# Install an audited release to this user's home, then open guided setup.
set -eu
case "$(uname -s)" in
  Darwin) install_root="$HOME/Library/Application Support/Runquay";;
  Linux) install_root="${XDG_DATA_HOME:-$HOME/.local/share}/runquay";;
  *) printf '%s\n' 'Runquay supports this installer on macOS and Linux. See docs/SETUP.md.' >&2; exit 2;;
esac
for tool in curl tar; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Runquay needs %s to download its release. See docs/SETUP.md.\n' "$tool" >&2
    exit 2
  fi
done
latest=$(curl --proto '=https' --tlsv1.2 -fsSL -o /dev/null -w '%{url_effective}' 'https://github.com/dibyapp/runquay/releases/latest')
case "$latest" in
  'https://github.com/dibyapp/runquay/releases/tag/v'*) version=${latest##*/v};;
  *) printf '%s\n' 'The latest release address is unexpected.' >&2; exit 2;;
esac
if ! printf '%s\n' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  printf '%s\n' 'The release version is invalid.' >&2; exit 2
fi
archive="runquay-$version-source.tar.gz"
url="https://github.com/dibyapp/runquay/releases/download/v$version/$archive"
printf 'Runquay %s - verified release found.\n' "$version"
if [ "${1:-}" = '--check' ]; then
  curl --proto '=https' --tlsv1.2 -fsSLI "$url" -o /dev/null
  curl --proto '=https' --tlsv1.2 -fsSLI "$url.sha256" -o /dev/null
  printf '%s\n' 'Check only: no download, installation or AI request was started.'
  exit 0
fi
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
curl --proto '=https' --tlsv1.2 -fsSL "$url" -o "$scratch/$archive"
curl --proto '=https' --tlsv1.2 -fsSL "$url.sha256" -o "$scratch/$archive.sha256"
expected=$(awk -v name="$archive" '{sub(/\r$/, "", $2)} $2 == name && length($1) == 64 && $1 !~ /[^0-9a-f]/ {print $1}' "$scratch/$archive.sha256")
if [ -z "$expected" ] || [ "$(wc -l < "$scratch/$archive.sha256" | tr -d ' ')" != 1 ]; then
  printf '%s\n' 'The release checksum file is invalid.' >&2; exit 2
fi
if command -v sha256sum >/dev/null 2>&1; then
  actual=$(sha256sum "$scratch/$archive" | cut -d ' ' -f 1)
elif command -v shasum >/dev/null 2>&1; then
  actual=$(shasum -a 256 "$scratch/$archive" | cut -d ' ' -f 1)
else
  printf '%s\n' 'A SHA256 checksum utility is required. See docs/SETUP.md.' >&2; exit 2
fi
if [ "$actual" != "$expected" ]; then printf '%s\n' 'The downloaded archive does not match its release checksum.' >&2; exit 2; fi
tar -tzf "$scratch/$archive" > "$scratch/entries"
while IFS= read -r entry; do
  case "$entry" in runquay/*) :;; *) printf '%s\n' 'The archive contains a file outside Runquay.' >&2; exit 2;; esac
  case "$entry" in *\\*|*/../*|*/./*|*//*) printf '%s\n' 'The archive contains an unsafe path.' >&2; exit 2;; esac
done < "$scratch/entries"
tar -tvzf "$scratch/$archive" > "$scratch/details"
if ! awk 'substr($0,1,1) != "-" {exit 1}' "$scratch/details"; then
  printf '%s\n' 'The archive contains a link or non-file entry.' >&2; exit 2
fi
mkdir -p "$scratch/extracted"
tar -xzf "$scratch/$archive" -C "$scratch/extracted"
source_dir="$scratch/extracted/runquay"
if [ ! -f "$source_dir/runquay.py" ] || [ ! -f "$source_dir/setup.sh" ]; then
  printf '%s\n' 'The release archive is missing Runquay.' >&2; exit 2
fi
if [ "${1:-}" = '--verify' ]; then
  printf '%s\n' 'Archive and checksum verified. No installation or AI request was started.'
  exit 0
fi
versions="$install_root/versions"
target="$versions/$version"
mkdir -p "$versions"
if [ -e "$target" ]; then
  if [ ! -f "$target/runquay.py" ]; then printf '%s\n' 'An incomplete installation exists for this version. Remove that version folder and retry.' >&2; exit 2; fi
  printf '%s\n' 'This release is already installed.'
else
  mv "$source_dir" "$target"
  printf '%s\n' 'Installed Runquay in your user folder.'
fi
launcher="$install_root/Open Runquay.command"
printf '%s\n' "$version" > "$install_root/current-version"
cat > "$launcher" <<'RUNQUAY_LAUNCHER'
#!/bin/sh
set -eu
case "$(uname -s)" in
  Darwin) root="$HOME/Library/Application Support/Runquay";;
  Linux) root="${XDG_DATA_HOME:-$HOME/.local/share}/runquay";;
  *) exit 2;;
esac
version=$(cat "$root/current-version")
exec sh "$root/versions/$version/setup.sh"
RUNQUAY_LAUNCHER
chmod 700 "$launcher"
if [ "$(uname -s)" = Darwin ]; then
  mkdir -p "$HOME/Applications"
  cp "$launcher" "$HOME/Applications/Runquay.command"
  chmod 700 "$HOME/Applications/Runquay.command"
  printf '%s\n' 'Open Runquay.command in Applications next time.'
else
  printf 'Open %s next time.\n' "$launcher"
fi
printf '%s\n' 'Opening guided setup now.'
exec sh "$target/setup.sh"
