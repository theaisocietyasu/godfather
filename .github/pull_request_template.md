## Summary

<!-- One logical change. A diagram, diff sketch or tree of the change, and one line on why. -->

## Evidence

<!-- Before and after: the test, command output or screenshot that shows the change works. -->

## Merge danger

**Door:** <!-- one-way or two-way -->

**Blast radius:** <!-- who or what breaks if this is wrong: members' CLIs, running pods, Platform -->

## Checklist

- [ ] `make check` passes
- [ ] New behavior has a test, and the test fails without the change
- [ ] Docs changed in the same PR (`README.md`, `cli/README.md`, `docs/ARCHITECTURE.md`, the image README)
- [ ] A change to the pod image contract names the matching Platform PR
- [ ] A user-visible change has a line for the next `docs/releases/v<version>.md`
- [ ] No token, key or `~/.godfather/config.json` content in the PR, logs or tests
