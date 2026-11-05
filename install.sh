#!/usr/bin/env bash
# Installs the dotfiles on macOS or Ubuntu. Every step is safe to run again.
# A file that already exists at a link target moves to <file>.bak-dotfiles.<time>.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="$(uname -s)"
STAMP="$(date +%Y%m%d%H%M%S)"
WITH_HERDR="${WITH_HERDR:-$([ "$OS" = Linux ] && echo 1 || echo 0)}"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
has() { command -v "$1" >/dev/null 2>&1; }

link() {
	local src="$DOTFILES/$1" dest="$2"
	mkdir -p "$(dirname "$dest")"

	if [ "$(readlink "$dest" 2>/dev/null)" = "$src" ]; then
		return
	fi

	if [ -e "$dest" ] || [ -L "$dest" ]; then
		mv "$dest" "$dest.bak-dotfiles.$STAMP"
	fi

	ln -s "$src" "$dest"
}

install_packages_macos() {
	if ! has brew; then
		log "Installing Homebrew"
		/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
		eval "$(/opt/homebrew/bin/brew shellenv)"
	fi

	log "Installing Brewfile packages"
	brew bundle --file "$DOTFILES/Brewfile"
}

install_packages_linux() {
	log "Installing apt packages"
	sudo apt-get update -y
	sudo apt-get install -y software-properties-common

	if ! grep -rqs fish-shell /etc/apt/sources.list /etc/apt/sources.list.d; then
		sudo add-apt-repository -y ppa:fish-shell/release-4
		sudo apt-get update -y
	fi

	xargs sudo apt-get install -y fish < "$DOTFILES/apt-packages.txt"

	# Ubuntu names the fd binary fdfind.
	if has fdfind && ! has fd; then
		mkdir -p "$HOME/.local/bin"
		ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
	fi
}

install_re_search() {
	if [ -x "$HOME/.local/bin/re-search" ] || has re-search; then
		return
	fi

	log "Building re-search"
	local build
	build="$(mktemp -d)"
	git clone --depth 1 https://github.com/jbonjean/re-search "$build"
	make -C "$build"
	install -m 755 "$build/re-search" "$HOME/.local/bin/re-search"
	rm -rf "$build"
}

set_login_shell() {
	local fish_path
	fish_path="$(command -v fish)"

	if [ "${SHELL:-}" = "$fish_path" ]; then
		return
	fi

	grep -qx "$fish_path" /etc/shells || echo "$fish_path" | sudo tee -a /etc/shells >/dev/null

	if sudo chsh -s "$fish_path" "$USER"; then
		return
	fi

	# Some managed hosts do not allow chsh. Interactive bash then starts fish. VS Code sets
	# VSCODE_RESOLVING_ENVIRONMENT when it reads the shell environment, and that read must stay in bash.
	log "chsh failed, so ~/.bashrc starts fish"
	grep -q 'exec fish' "$HOME/.bashrc" 2>/dev/null || cat >> "$HOME/.bashrc" <<-'EOF'
		if [[ $- == *i* && -z "${VSCODE_RESOLVING_ENVIRONMENT:-}" ]] && command -v fish >/dev/null; then
			exec fish
		fi
	EOF
}

install_fish() {
	log "Linking fish config"
	link fish/config.fish "$HOME/.config/fish/config.fish"
	link fish/fish_plugins "$HOME/.config/fish/fish_plugins"

	for f in "$DOTFILES"/fish/conf.d/*.fish "$DOTFILES"/fish/functions/*.fish; do
		local rel="${f#"$DOTFILES"/}"
		link "$rel" "$HOME/.config/${rel}"
	done

	touch "$HOME/.config/fish/local.fish"
	install_re_search

	log "Installing fish plugins and Node LTS"
	fish -c 'type -q fisher; or begin
		curl -fsSL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source
	end
	fisher update
	set -q nvm_default_version; or set -U nvm_default_version lts
	nvm install lts'

	set_login_shell
}

install_git() {
	log "Linking git config"
	link git/config "$HOME/.config/git/config"
	link git/ignore "$HOME/.config/git/ignore"

	if ! git config --global user.email >/dev/null; then
		log "Set your identity: git config --global user.name ...; git config --global user.email ..."
	fi
}

install_herdr() {
	link herdr/config.toml "$HOME/.config/herdr/config.toml"
	link bin/herdr-launch "$HOME/.local/bin/herdr-launch"

	if [ "$WITH_HERDR" = 1 ] && [ ! -x "$HOME/.local/bin/herdr" ]; then
		log "Installing herdr"
		curl -fsSL https://herdr.dev/install.sh | sh
	fi
}

install_claude() {
	if ! has claude && [ ! -x "$HOME/.local/bin/claude" ]; then
		log "Installing Claude Code"
		curl -fsSL https://claude.ai/install.sh | bash
	fi

	log "Linking Claude config"
	link claude/CLAUDE.md "$HOME/.claude/CLAUDE.md"
	link claude/hooks/comment-budget.py "$HOME/.claude/hooks/comment-budget.py"

	for skill in "$DOTFILES"/claude/skills/*/; do
		local name
		name="$(basename "$skill")"
		link "claude/skills/$name" "$HOME/.claude/skills/$name"
	done

	(cd "$DOTFILES/claude/skills/brief/scripts" && fish -c 'npm install --silent --no-audit --no-fund')
	merge_claude_settings
	install_claude_plugins
}

# Claude Code writes to settings.json, for example project-specific autoMode notes.
# A symlink would carry those writes into this public repo, so the shared keys merge into a local file.
merge_claude_settings() {
	local dest="$HOME/.claude/settings.json" merged
	[ -f "$dest" ] || echo '{}' > "$dest"
	merged="$(jq -s '.[0] * .[1]' "$dest" "$DOTFILES/claude/settings.json")"
	printf '%s\n' "$merged" > "$dest"
}

install_claude_plugins() {
	local claude_bin
	claude_bin="$(command -v claude || echo "$HOME/.local/bin/claude")"

	"$claude_bin" plugin marketplace add openai/codex-plugin-cc >/dev/null 2>&1 || true

	for plugin in $(jq -r '.enabledPlugins | keys[]' "$DOTFILES/claude/settings.json"); do
		"$claude_bin" plugin install "$plugin" >/dev/null 2>&1 || log "Plugin $plugin did not install"
	done
}

install_vscode() {
	local user_dir="$HOME/Library/Application Support/Code/User"
	log "Linking VS Code settings and installing extensions"
	link vscode/settings.json "$user_dir/settings.json"
	link vscode/keybindings.json "$user_dir/keybindings.json"

	local code_bin="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
	has code && code_bin="$(command -v code)"

	while read -r ext; do
		"$code_bin" --install-extension "$ext" --force >/dev/null
	done < "$DOTFILES/vscode/extensions.txt"

	"$code_bin" --install-extension "$DOTFILES/claude/skills/brief/vscode-ext/brief.vsix" --force >/dev/null
}

install_iterm() {
	log "Installing iTerm2 profiles"
	local dir="$HOME/Library/Application Support/iTerm2/DynamicProfiles"
	mkdir -p "$dir"

	# iTerm2 loads dynamic profile files in name order, so a parent in another file can be missing.
	# The herdr profile is built as Main with its own keys on top, so it needs no parent.
	rm -f "$dir/main.json" "$dir/herdr.json"
	jq -s '.[0].Profiles[0] as $main | .[1].Profiles[0] as $herdr
		| ($main["Keyboard Map"] + $herdr["Keyboard Map"]) as $keys
		| {Profiles: [$main, ($main + $herdr + {"Keyboard Map": $keys})]}' \
		"$DOTFILES/iterm2/main.json" "$DOTFILES/iterm2/herdr.json" |
		sed "s#__HOME__#$HOME#g" > "$dir/dotfiles.json"

	# iTerm2 writes its preferences when it quits, so this setting holds only while iTerm2 is closed.
	defaults write com.googlecode.iterm2 "Default Bookmark Guid" -string dotfiles-main-profile
}

main() {
	mkdir -p "$HOME/.local/bin"
	export PATH="$HOME/.local/bin:$PATH"

	case "$OS" in
	Darwin) install_packages_macos ;;
	Linux) install_packages_linux ;;
	*) echo "Unsupported OS: $OS" >&2; exit 1 ;;
	esac

	install_fish
	install_git
	install_herdr
	install_claude

	if [ "$OS" = Darwin ]; then
		install_vscode
		install_iterm
		"$DOTFILES/macos/defaults.sh"
	fi

	git -C "$DOTFILES" config core.hooksPath .githooks
	log "Done. Open a new shell. Put secrets in ~/.config/fish/local.fish."
}

main "$@"
