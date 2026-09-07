# External exact-head reviews

`tools/external_review.py` is an optional maintainer-run bridge for posting Claude Code and Grok Build reviews directly to the top-level conversation on an open GitHub pull request. It is developer tooling, not a required CI, runtime, benchmark, or release dependency.

## One-time setup

Install the official provider CLIs and authenticate them outside the repository:

```text
curl -fsSL https://claude.ai/install.sh | bash
claude auth login

curl -fsSL https://x.ai/cli/install.sh | bash
grok login --device-auth
```

The bridge uses the existing authenticated `gh` session for GitHub publication. Provider authentication may use the providers' local OAuth or device sessions, or intentionally configured local provider secrets. Never place credentials in this repository or a review prompt.

Check the complete local setup without posting or invoking a review model:

```text
python3 tools/external_review.py doctor
```

`doctor` checks `git`, `gh`, GitHub authentication, both provider executables and versions, provider authentication, repository context, and the exact safety-critical CLI flag spellings used for structured output, noninteractive permissions, tool restriction, sandboxing, customization isolation, web/subagent disabling, and session suppression. Required options are matched as complete help tokens rather than substrings of longer option names. It reports an actionable login command when authentication is missing, fails when an installed CLI does not advertise the required invocation surface, and does not print credential material. Whitespace-only prompt lines are excluded from diagnostic redaction so blank diff context cannot replace every space; complete prompts, meaningful prompt lines, and secrets remain redacted. Grok model listing remains a separate authentication/model-access health probe in `doctor`; it does not select or bind the review model. Grok's hidden `--no-auto-update --no-memory` controls are also exercised with a harmless version lookup rather than inferred from help text.

## Run a review

The normal current-PR command waits for CI and passes its approved head SHA to the bridge:

```text
npm run review:ready
```

Each provider runs independently in its own detached checkout. A Claude failure does not skip Grok, and a Grok failure does not discard a validated Claude result. Nothing is posted until every requested provider validates and the PR head and base are rechecked.

Every CLI attempt prints a private checkpoint path under `.cache/external-reviews/`. After a failure, resume it with:

```text
npm run review:ready -- --resume .cache/external-reviews/ATTEMPT.json
```

Resume rechecks CI, revalidates retained results, and invokes only providers without a validated result. It requires the same repository, PR head and base, provider selection, full wrapped prompt/diff, and bridge implementation. Changed inputs require a fresh attempt. A plain invocation always starts fresh; retained output is never silently substituted.

For a custom scope, prepare one provider-neutral Markdown prompt and use the bridge directly:

```text
python3 tools/external_review.py review \
  --pr 142 --provider all --prompt-file /path/to/review-prompt.md

python3 tools/external_review.py review \
  --pr 142 --provider all --prompt-file /path/to/review-prompt.md \
  --resume .cache/external-reviews/ATTEMPT.json
```

`--provider claude` and `--provider grok` select one reviewer. `--collect-only` validates and retains results without posting, which is useful before stacked-branch CI is available. Resume the same checkpoint without `--collect-only` to publish after obtaining the required CI evidence. Direct bridge commands do not claim to check CI; `review:ready` supplies that gate and uses `--expected-head` to prevent a race into reviewing a different unchecked head. A custom prompt must be reused exactly; `review:ready` always uses the repository's release-gate prompt.

`doctor` remains a standalone setup diagnostic. It is not a blanket prerequisite in `review:ready`: cached providers need no fresh authentication probe, and one broken provider should not prevent collecting another. Every invoked adapter still performs its own required capability checks and isolation enforcement. There are no automatic paid retries; the checkpoint makes retrying explicit and selective.

The prompt file is read locally. Provider-specific temporary prompt and configuration paths are outside committed source and are removed after the command. Claude uses the maintainer's normal local OAuth login, disables session persistence, and receives wrapper-owned ephemeral settings and MCP configuration without relocating or copying OAuth state. Grok runs with an ephemeral home containing a generated sandbox profile and discards the review session, prompt copy, configuration, and logs after execution. The bridge resolves the existing Grok authentication target to a readable regular file and never copies or modifies its contents.

## Exact-head and identity contract

Before either provider runs, the bridge resolves the live PR number, state, base SHA, and head SHA through `gh`. It fetches missing commit objects without creating a permanent review branch, generates the complete base-to-head diff itself, and creates a separate temporary detached worktree at the exact head for each invoked provider. Providers receive that wrapper-generated diff, one common review request, and a machine-readable contract containing `pr_number`, `head_sha`, `verdict`, `body_markdown`, and structured `findings`.

Every structured finding contains a `severity` (`BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`), `title`, and `detail`. `INCOMPLETE` is an explicit nonpublishable outcome with an empty findings collection and a concise reason in the body. `PASS` requires an empty findings collection; `FINDINGS` requires at least one valid structured finding. Provider output must be final: a review body, finding title, or finding detail that explicitly describes the provider's own result as bootstrap, progress-only, unfinished, or placeholder state fails validation and is not posted. Bare placeholder fields and explicit statements that this review is unfinished, incomplete, or not performed are also rejected in the body, finding title, or finding detail. In all-provider mode, either provider returning such a result prevents every review from being posted. Findings about unfinished product functionality remain valid. The status check recognizes “not yet” and contracted negation such as “haven’t” or “hasn’t”. Quoted or backtick-delimited payloads explicitly introduced as fixtures, examples, test cases/inputs/payloads, sample inputs/payloads, or literals are excluded from self-status checks; their original text remains in the posted review. Quotation alone is not exempt, and surrounding self-status claims still reject the result. This is a finality check, not a review-quality score; concise final PASS results and concrete findings remain valid. The bridge never manufactures findings from prose. Structured findings are rendered into the posted comment beneath the provider's human-readable review body. Grok may return the authoritative schema object under the JSON envelope's camelCase `structuredOutput` field; the bridge prefers that object to prose fields and keeps strict JSON parsing for any fallback.

The bridge owns provider identity. Model prose is never authoritative. An explicit provider or reviewer claim that conflicts with the invoked adapter fails validation and posts nothing. Claim recognition normalizes harmless GitHub-rendered presentation forms—including ATX, setext, blockquoted, list-prefixed, bold-only, HTML-heading, and common Unicode-dash variants—without rewriting unrelated Markdown. Fenced code examples are preserved and are not treated as live metadata. Redundant matching identity and syntactically exact PR, full-head, verdict, and review-role metadata are removed so they cannot compete with the trusted comment header. Metadata-shaped explanatory prose, short SHAs, placeholders, and extended verdict sentences are retained because they are not valid wrapper metadata claims.

Each provider checkout must remain clean and be removed successfully before its result is retained as validated. The bridge re-queries the live PR after collection. A closed PR, moved head, or changed base is stale evidence: the command exits nonzero and posts nothing. In `--provider all` mode, both results must validate before either is posted; PASS and FINDINGS are both valid verdicts and may be posted together.

Each successful result appears as a top-level PR conversation comment with a wrapper-owned provider, provider CLI version, independently discoverable model metadata when available, PR number, exact reviewed head, verdict, and review role. Claude is labeled as the Issue #98 external second-pair review, and Claude Code chooses its provider-owned default model. Grok is labeled as additional independent review evidence, and Grok CLI likewise chooses its provider-owned default model. The bridge records an explicit envelope model identifier when available; otherwise it may select useful provider-consistent `modelUsage` evidence using observed usage rather than a model-family or version preference. A flat provider-authored contract cannot create a trusted Model row from its own claim. Model aliases, versions, and suffixes may change without invalidating an otherwise valid review, and the bridge does not enforce requested-versus-reported model equality. Cross-provider model or provider identity conflicts still fail closed. Provider CLI and model values are length-bounded, whitespace-normalized single-line values before table rendering. Before publication, the wrapper redacts secret-shaped content—including GitHub fine-grained `github_pat_` values—and any exact resolved Grok-auth path from provider-generated content. Wrapper-owned PR and exact-head metadata are not subject to provider-content redaction. Posted external evidence still requires human disposition.

## Security boundary

Provider processes receive read-only repository inspection permissions and no shell tool. Claude uses `--setting-sources user` so project and local settings from the reviewed checkout are excluded while the maintainer's trusted local OAuth/user state remains available. Wrapper-owned ephemeral settings disable all hooks and auto-memory, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` reinforces that boundary, and `--strict-mcp-config` points exclusively to a wrapper-owned empty MCP configuration. Claude receives no explicit model argument and exposes only `Read`, with an absolute rule scoped to the exact detached checkout under `dontAsk`; Grep and Glob are not enabled. Bash, Edit, Write, NotebookEdit, WebFetch, WebSearch, and Agent remain denied. `--safe-mode` is retained as provider defense in depth rather than the sole customization boundary. Independently returned Claude model provenance remains recorded in the posted evidence when available. Grok also receives no explicit model argument and exposes only Read and Grep through checkout-relative `Read(./**)` and `Grep(./**)` rules, with explicit tool-level denies for both the complete canonical authentication-directory tree and the resolved authentication file. Bash remains denied, web search and subagents are disabled, and memory is disabled.

Grok review and configuration inspection use the same ephemeral custom sandbox profile extending `strict`. Grok Build 1.0.5 accepts only literal directories in a profile's `read_only` field, not individual files, so the narrowest supported runtime exception is the resolved authentication file's canonical parent directory. The bridge rejects filesystem root, the user's home, shared temporary and broad system directories, and any directory overlapping the detached review worktree; the supported layout is a bounded Grok-specific or dedicated credential directory. Sibling files within that accepted directory remain process-readable, while model-facing Read and Grep explicitly deny the entire directory tree and retain exact-auth-file denies as defense in depth. The exception exists only so the runtime can authenticate, adds no writable path, and leaves GitHub credentials outside the provider environment. Any detected sandbox-application warning fails closed even when the CLI returns success. The sandbox is defense in depth, not the sole confinement boundary.

Before either provider runs, the wrapper resolves every repository symlink and rejects broken links or links escaping the detached checkout; the regular linked-worktree `.git` pointer file is unaffected. The wrapper supplies the base-to-head diff, so removing provider shell access does not remove PR comparison evidence. Before a Grok run, the bridge rejects discovered project instructions, hooks, skills, plugins, MCP servers, or permission sources so reviewed code cannot widen the adapter. The bridge verifies that the detached worktree remains clean after each provider.

Safe local synthetic-sentinel probes against Claude Code 2.1.234 and Grok Build 1.0.5 confirmed that the configured file tools could read repository files but could not read a sibling file outside the checkout. The Claude probe additionally confirmed that OAuth worked with project/local setting sources excluded, wrapper hooks and auto-memory disabled, the strict empty MCP configuration active, Grep/Glob and the other denied tools unavailable, project customization inert, and provider-reported model provenance independently recorded. A Grok probe using the custom auth exception additionally confirmed that authentication worked while model tools could not access either the auth file or a synthetic sibling in its directory. `doctor` verifies the exact invocation capability surface on every setup check and each adapter repeats it before invocation. This is still dependent on the installed CLIs continuing to honor their documented permission and sandbox semantics; repeat both safe probes after a significant provider upgrade.

The child environment removes `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`, and points `GH_CONFIG_DIR` at an empty temporary directory. Providers cannot use the bridge's authenticated `gh` configuration. Only the wrapper revalidates the head and posts the final comment. Providers cannot push, merge, delete branches, mutate issues or releases, or post GitHub comments through the granted tool set.

Ordinary unit tests mock provider and GitHub interactions. They do not call provider APIs, require provider authentication, or post to GitHub.

## Failure diagnostics

Failures identify the component, operation stage, exit code when available, a bounded sanitized diagnostic, and known login remediation. Examples include version/capability lookup, temporary isolation setup, sandbox configuration inspection/enforcement, review invocation, structured-output parsing, contract validation, dirty-worktree validation, cleanup, exact-head revalidation, and GitHub posting.

`doctor` retains its compact OK/FAIL list but preserves safe runner exceptions instead of replacing them with an empty failure. Missing capabilities name the actual CLI flag. Authentication failures include the provider's login command.

Provider stderr is redacted before display. When stderr is empty, only a JSON error-message field or a recognized authentication failure is surfaced from stdout; arbitrary stdout is explicitly omitted because it can contain prompt or review content. Diagnostics strip terminal/control noise, redact token-shaped values, configured/resolved Grok authentication paths and known prompt text, and bound the displayed detail. Raw provider logs and rejected review bodies are not persisted. Checkpoints retain validated, sanitized results and bounded failure diagnostics. Finality failures identify the exact field and the kind of completion contradiction; INCOMPLETE returns a bounded redacted explanation. These diagnostics do not establish review quality or expose the complete rejected output.

If an all-provider run fails before posting, both providers are attempted independently and the error identifies each validated or failed result plus `posted reviews: none`. Fix the reported access or output issue and use the printed checkpoint with `--resume`; successful reviews remain reusable only while their identity still matches.

## Checkpoints and posting recovery

Checkpoints contain identity hashes, sanitized validated results, safe diagnostics, timestamps, and confirmed comment receipts. They exclude the full input prompt and rejected raw output. They live outside the provider checkouts in a user-owned directory with mode 0700; files use mode 0600. Writes are atomic, and a POSIX process lock prevents two resumes of the same attempt from racing. Symlinked or public-readable state files are rejected. This uses the supported Linux/dev-container or other POSIX environment. `--state-dir` selects another private directory; supply it again when resuming a file there. Treat checkpoints as trusted local evidence, never accept them from a reviewed PR or edit them to manufacture a successful result.

A confirmed posted result is not posted again on resume. The bridge records posting intent before each GitHub call and its receipt afterward. GitHub comments are separate writes, so network failures can leave one confirmed comment or an uncertain write even though all-provider validation succeeded. A checkpoint with an uncertain write blocks automatic reposting and tells you to inspect GitHub; the bridge does not claim a remote rollback or silently create duplicates. Do not start a fresh posting run until that uncertainty is reconciled. Completed checkpoints may be removed once their evidence is no longer needed.
