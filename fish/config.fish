for brew in /opt/homebrew/bin/brew /home/linuxbrew/.linuxbrew/bin/brew
    if test -x $brew
        $brew shellenv | source
        break
    end
end

fish_add_path -g ~/.local/bin ~/bin ~/.cargo/bin

set -g fish_greeting

# Secrets and machine-specific settings. The repo never tracks this file.
test -f ~/.config/fish/local.fish; and source ~/.config/fish/local.fish
