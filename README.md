# dotfiles

Shell, editor, terminal and Claude Code config for macOS and Ubuntu.

## Install

```sh
git clone https://github.com/ChewingGlass/dotfiles ~/dotfiles
~/dotfiles/install.sh
```

The script runs again without harm. A file that already exists where a link goes moves to
`<file>.bak-dotfiles.<time>`.

| | macOS | Ubuntu |
|---|---|---|
| Packages | Homebrew and `Brewfile` | apt, `apt-packages.txt`, fish 4 PPA |
| fish, re-search, fisher, nvm.fish | yes | yes |
| git, Claude Code and its config | yes | yes |
| herdr | config only, `WITH_HERDR=1` installs it | yes |
| VS Code, iTerm2 profiles, key repeat | yes | no |

## Remote Linux machines

VS Code Remote-SSH uses the local settings. It installs the extensions in
`remote.SSH.defaultExtensions` on the remote host. The integrated terminal opens fish on both systems.

The iTerm2 `herdr` profile runs `herdr-launch`. Put an SSH host name in `~/.config/herdr/host`, and
the profile opens herdr on that host. Without the file, it runs the local herdr. The herdr server
keeps its session when the connection drops.

## Files the repo does not track

- `~/.config/fish/local.fish`: secrets, tokens and machine-specific paths.
- `~/.gitconfig`: name, email and signing key.
- `~/.claude/settings.json`: the installer merges `claude/settings.json` into it, so
  project-specific settings that Claude Code writes stay on the machine.

## Secrets

The repo is public. The pre-commit hook runs `gitleaks` and stops a commit that contains a secret.

## iTerm2

The `herdr` profile maps each Cmd chord to F12 and a letter, so herdr gets the key and iTerm2 does
not. `herdr/config.toml` explains the prefix. Close iTerm2 before the install, or select the `Main`
profile as the default in Settings, because iTerm2 writes its preferences when it quits.

Key repeat changes apply after the next login.
