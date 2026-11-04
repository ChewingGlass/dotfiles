status is-interactive; or exit

# Without re-search, Ctrl-R stays on the built-in fish history pager.
if type -q re-search
    bind \cr re_search
end

alias k=kubectl
alias tf=tofu
alias gb="git branch --sort=-committerdate"
