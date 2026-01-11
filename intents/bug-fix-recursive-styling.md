---
status: "Fixed"
type: "Intent"
last_updated: "date"
references: 
---

# Bug-Fix recursive styling

There is currently a bug with the UI rendering.  As it renders out it's owncode,
it will crash on displaying tagged markdown.  Here is an example of the crash:

This is from the output log: 

   def _handle_input(self, text: str) -> None:
        """
        Sends input to the model, streams the response, and logs the turn.
        """
        # Log User Input
        self._log_interaction("USER", text)

        ui.console.print(f"[bold cyanTraceback (most recent call last):
  File "/home/nerp/.local/bin/vybz", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/nerp/src/vybz/src/vybz/tools/work.py", line 110, in main
    ui.print_error(f"Critical Runtime Error: {e}")
  File "/home/nerp/src/vybz/src/vybz/ui.py", line 104, in print_error
    error_console.print(f"[error]ERROR:[/error] {message}")
  File "/home/nerp/.local/lib/python3.11/site-packages/rich/console.py", line 1698, in print
    renderables = self._collect_renderables(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nerp/.local/lib/python3.11/site-packages/rich/console.py", line 1558, in _collect_renderables
    self.render_str(
  File "/home/nerp/.local/lib/python3.11/site-packages/rich/console.py", line 1448, in render_str
    rich_text = render_markup(
                ^^^^^^^^^^^^^^
  File "/home/nerp/.local/lib/python3.11/site-packages/rich/markup.py", line 167, in render
    raise MarkupError(
rich.errors.MarkupError: closing tag '[/bold cyan]' at position 59 doesn't match any open tag
