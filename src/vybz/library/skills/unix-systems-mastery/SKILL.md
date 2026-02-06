---
name: unix-systems-mastery
description: Deep adherence to the Unix Philosophy, POSIX compliance, and the art
  of shell composition.
---

# Unix Systems Mastery
_Deep adherence to the Unix Philosophy, POSIX compliance, and the art of shell composition._

## Knowledge
* #### The Unix Philosophy
      *   **Do One Thing Well:** Write programs that do one thing and do it well. Write programs to work together.
      *   **Text Streams:** Write programs to handle text streams, because that is a universal interface.
      *   **Composition:** Prefer piping small, standard utilities (`grep`, `awk`, `sed`, `xargs`) over writing monolithic scripts.
* #### The Preferred Stack
      *   **OS:** FreeBSD 15.0 (The Reference Implementation) / Debian Stable (The Pragmatic Choice).
      *   **Shell:** POSIX `sh` is the standard. Bash-isms (arrays, `[[ ]]`) are forbidden in system scripts.
      *   **Editor:** vi, ex, or ed
      *   **Multiplexer:** Tmux v3.5a is the window manager.
* #### The Greybeard's Toolbelt
      *   **awk:** The preferred tool for columnar data processing.
      *   **sed:** The stream editor for text transformations.
      *   **find/xargs:** The standard way to operate on file trees.
      *   **man pages:** The ultimate source of truth. If it isn't in the man page, it doesn't exist.

## Abilities
* Living off the land: Solving complex problems using only base system utilities installed by default.
* Writing portable shell scripts that execute identically on FreeBSD `/bin/sh` and Linux `dash`.
* Constructing robust pipelines where the stdout of one process feeds the stdin of the next.
* Command-Line Proficiency: Effectively using powerful command-line tools like grep, awk, sed, find, and xargs.
* Handling signals (SIGINT, SIGTERM) gracefully in scripts.
