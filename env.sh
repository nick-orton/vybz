#Use RipGrep to ignore .git and venv files
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow'
alias gc="./bin/autocommit_gen.py > /tmp/commit; ./bin/mdformat /tmp/commit | git commit -F - -e"
