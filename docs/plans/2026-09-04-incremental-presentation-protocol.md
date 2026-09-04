# Incremental Presentation Protocol Plan

1. Add a pure protocol module and CLI to synthesize and validate a task-local
   sidecar from existing workflow state and `design.html`.
2. Add unit coverage for deterministic construction and mutation detection.
3. Make the execution validator consume a declared protocol while retaining the
   legacy no-protocol path.
4. Add the protocol pointer to the new-task template and document the `sync`
   step in authoring, delivery, and studio skills.
5. Run focused protocol and workflow tests, then the repository test entry.
