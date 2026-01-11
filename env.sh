#Use RipGrep to ignore .git and venv files
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow'
alias gc="vybz-commit > /tmp/commit; vybz-fmt /tmp/commit | git commit -F - -e"
