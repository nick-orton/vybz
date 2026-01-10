Write a self-containted python executable script that will do the following.

The tool is designed to write git commit messages explaining what changes happened.

- It should use best-in-class commit message best practices.
- Assumes that it is working inside of a git directory.  Error appropriately if
  not.
- It will be given an optional argument of a log file that containst the intent
  prompts and responses of the agents that were vibe coding the changes
- It should accept that humans also made additional changes to the files
- It will look at the staged commits as the source of truth for what changed. 
  - if it has the log file it will use it to deduce why these changes were made
