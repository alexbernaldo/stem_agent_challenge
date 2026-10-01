# stem_agent_challenge

A prototype of an agent that writes its own data-cleaning function. You give it a CSV, GPT-4o generates the code, and when that code crashes at runtime the real `stderr` goes back into the model on the next turn. The version that passes the validator is frozen into `agent_state_<n>.json`.

## What works

**The loop hands the model the actual error, not a description of it.** Each attempt writes the generated code to a temporary file, runs it, and reads the result. If the subprocess dies, `result.stderr` — the literal traceback — becomes the error string. If the subprocess exits cleanly but the validator rejects the frame, the rejection message becomes the error string instead. Both go back to the model as part of the next request (`src/stem_core.py:75-86`), so the retry prompt says what actually happened rather than "your code did not work".

**The two failure paths are kept apart, and they produce different retry text.** A crash returns the traceback. A validator rejection returns the reason, for example `"The cleaned dataset retains less than 80% of the original data, which may indicate excessive cleaning."` (`src/test_agent.py:32`). The loop history keeps every failed attempt, and the model reads its own previous code again in the prompt before rewriting it.

**EDA → `eda_report` → cleaning is a hard pipeline, and the report cannot be bypassed.** The cleaning phase receives the whole `eda_report` dictionary as its only context, serialized into the user prompt (`json.dumps(eda_report, indent=2)`, `src/stem_core.py:64`). `metaprompt_cleaning.txt` requires every threshold to come from that report and states the rule literally: *"thresholds not derived from eda_report are a contract violation"*. The same rule reappears in the `REJECTION CONDITIONS` list at the end of the file. In practice this means no `fillna(0)` and no hardcoded IQR constant: the model has to cite the per-column null counts, the IQR and z-score outlier candidates, and the dtype mismatches that the EDA module measured, in its `reasoning` field.

**`freeze_agent()` persists the winner.** Once the code runs and passes validation, the three `agent_state` keys are written to `agent_state_<i+1>.json` with `indent=4`, and the phase ends. Those files are in the `.gitignore`.

**The model writes the system prompt that governs its deployed version.** `specialized_system_prompt` is one of the three mandatory `agent_state` keys, sits between `reasoning` and `python_code`, and carries second-person decision rules for nulls, outliers, and dtypes derived from that dataset's characteristics, plus the conditions under which it must escalate instead of fixing things on its own. What ends up frozen in `agent_state_<n>.json` is a prompt next to the code.

## How it works

Two phases, each with its own metaprompt and up to 20 attempts (`MAX_MUTATIONS = 20`, `src/stem_core.py:10`), so 40 API calls in the worst case.

The EDA phase asks for a generic diagnostic script. `sandbox_eda.py` prepends the dataset path and the line `dataset = pd.read_csv(DATASET_PATH)`, runs it with `subprocess.run(["python", f], capture_output=True, text=True, timeout=30)`, and pulls the `eda_report` dict out of stdout, because the scaffold appends `print(json.dumps(eda_report, default=str))` to the generated script. Null counts are cast to `int` before being returned.

The cleaning phase gets the full `eda_report` as its only context. `sandbox.py` prepends `DATASET_PATH` and `eda_report = {...}` to the generated code and runs it the same way. If the subprocess returns `returncode == 0`, the frame goes to the validator.

Both failure cases re-inject the same message pair: the complete `json.dumps(agent_state)` as the `assistant` turn, and a `user` turn reading `"The previous code did not work. The error was: {error}. Please fix the code and try again."`

## Architecture

```
stem_agent_challenge/
├── README.md
├── .gitignore                     .env, __pycache__/, agent_state_*.json
├── data/
│   ├── monster_com-job_sample.csv   68 MB · 22,000 real job postings × 14 columns
│   └── dirty_dataset.csv             200 synthetic rows with noise
└── src/
    ├── stem_core.py          93   both loops, the API call and freeze_agent()
    ├── sandbox.py            29   subprocess for the cleaning code; returns stderr or stdout
    ├── sandbox_eda.py        32   subprocess for the EDA code; appends the print and returns eda_report
    ├── test_agent.py         36   validator: exec() of the code and call to clean_dataframe()
    ├── make_dummy_data.py    61   generates dirty_dataset.csv
    ├── metaprompt_eda.txt         output and interface contract for the EDA module
    ├── metaprompt_cleaning.txt    output and interface contract for the CLEAN module
    └── metaprompt_og.txt          earlier metaprompt; no import loads it
```

That is 251 lines of Python across five files.

`make_dummy_data.py` puts four kinds of noise into 200 rows: nulls per column between 7 % and 15 %, outliers in `age` and `purchase_amount`, ten invalid strings (`"N/A"`, `"--"`, `"nan"`, `" "`) and fifteen impossible dates (`"2024/13/01"`, `"31-02-2024"`, `"2024.01.32"`). It also forces `purchase_amount` and `purchase_date` to `object` to reproduce dtype mismatches.

`metaprompt_og.txt` is the earlier metaprompt, from when `clean_dataframe` only took `df`. It is kept as a reference and nothing reads it.

## Requirements and installation

There is no `requirements.txt` or `pyproject.toml`, so dependencies are installed by hand. From the imports: `openai`, `python-dotenv`, `pandas` and `numpy` (the last one is only used by `make_dummy_data.py`). Everything else is stdlib: `subprocess`, `tempfile`, `json`, `os`.

```bash
pip install openai python-dotenv pandas numpy
```

The key goes in a `.env` in the repository root, which the `.gitignore` already covers:

```
OPENAI_API_KEY=sk-...
```

The model is fixed to `gpt-4o` (`src/stem_core.py:11`), so the key needs credit. The call uses `response_format={"type": "json_object"}` and the client is initialized once at module level.

Paths are relative to the working directory: `os.path.join('data', 'monster_com-job_sample.csv')` on line 94. Run it from the repository root.

## Usage

```bash
python src/stem_core.py
```

The imports in `stem_core.py` are flat (`import sandbox`, `import test_agent as test`, `import sandbox_eda`), with no package and no `__init__.py`, so `src/` has to be on `sys.path`. Running the script by path already does that.

To regenerate the dirty dataset and test against it:

```bash
python src/make_dummy_data.py
```

and change the call on line 94 to `os.path.join('data', 'dirty_dataset.csv')`.

## Design decisions

**The `eda_report` is the cleaning phase's only context, and its thresholds are not negotiable.** The behaviour this produces is described above: every cleaning decision has to trace back to a statistic the EDA module measured.

**The model writes the prompt that governs its own deployed version.** `specialized_system_prompt` is a required output artifact, not a comment. See "What works" above.

**The output contracts are strict down to key order.** Both metaprompts ask for a JSON object with exactly two or three keys *in that order*, the exact function signature (`run_eda(dataset: pd.DataFrame) -> dict`, `clean_dataframe(df: pd.DataFrame, eda_report: dict) -> pd.DataFrame`), a last line of `eda_report = run_eda(dataset)` in the EDA script, no line-continuation backslashes (`\`), and no `inplace=True` in any pandas operation, with `df[col] = df[col].fillna(value)` versus `df[col].fillna(value, inplace=True)` written into the metaprompt itself. Each file ends with a `REJECTION CONDITIONS` list enumerating what invalidates a response.

That requirement about the order of the JSON keys comes from the literature in the References section below, in particular the dsdev.in note on field order in structured output and the OpenAI guide: some models score worse when the keys do not follow the order in which they were declared.

The earlier README spent more lines on the metaprompt bibliography than on installation. The sources it leaned on are now collected at the end of this file.

## Limitations

Both metaprompts declare themselves "phase v0.1" and the code is at that level:

- **The sandbox isolates nothing.** `subprocess.run` launches the generated code with the same user, the same filesystem and an open network. The only bound on execution is a 30-second timeout; there is no memory, CPU or network limit.
- **`test_agent.py` calls `exec()` in its own process**, without isolation, so it can hand the real `dataset` and `eda_report` Python objects to `clean_dataframe`. This is the sharpest edge in the repository and is not flagged as such anywhere.
- There is no test suite. `test_agent.py` is not a test file: no pytest, no `assert`, no cases. It is the runtime validator the agent approves itself with, and it only measures two things (not empty, keeps ≥ 80 % of rows), so it would pass a cleaner that touches nothing and reject a legitimate one that removes many outliers by design.
- The EDA parser runs `json.loads` over the whole stdout, so any `print()` in the generated code breaks the parse, and what goes back to the model is `"Expecting value: line 1 column 1 (char 0)"` instead of the real cause.
- The `"python"` binary is invoked instead of `sys.executable`, so on a system without that alias it always fails and the error is blamed on the generated code. Temp files are created with `delete=False` and never removed, so each iteration leaves a `.py` with the generated code in `/tmp`.
- `metaprompt_eda.txt` promises the model the dataset schema (column names and sample rows) and `stem_core.py:37` sends a generic instruction with no schema. The script has to work out each column type on its own.
- No `retry` and no backoff: one rate limit takes the whole loop down. Failed attempts, costs and timings are not logged; only the winner persists. And nothing reads the `agent_state_<n>.json` afterwards.
- No license, no CI, no linter. The 68 MB dataset is committed to git.

## Status and next steps

The happy path is complete in the code — EDA, cleaning, validation and `freeze_agent` — but there is not a single `agent_state_*.json` in the repository or in git history, so no run was ever recorded. `MAX_MUTATIONS` grew commit by commit (5 → 10 → 20) and the large dataset arrived in the last commit, which means the loop has never been measured against the 22,000 real rows.

What a v0.2 would need:

- A `requirements.txt` or `pyproject.toml`, so dependencies install themselves.
- Move the `exec()` in `test_agent.py` out of this process and give execution real memory, CPU and network limits.
- A per-iteration log (code, error, tokens, seconds). Right now only the winner is saved, so there is no way to see how the loop behaves.
- Keep the failed attempts next to the winner, and give the frozen `specialized_system_prompt` a consumer — nothing reads it today.

## References

The metaprompts were written against these seven sources.

- Wei et al. (2022) — Chain-of-Thought Prompting Elicits Reasoning in LLMs. NeurIPS 2022. [arXiv:2201.11903](https://arxiv.org/abs/2201.11903).
- Suzgun et al. (2022) — Challenging BIG-Bench Tasks and Whether CoT Can Solve Them. [arXiv:2210.09261](https://arxiv.org/abs/2210.09261).
- Li et al. (2023) — Structured Chain-of-Thought Prompting for Code Generation. [arXiv:2305.06599](https://arxiv.org/abs/2305.06599).
- Kim et al. (2024) — Persona is a Double-edged Sword. [arXiv:2408.08631](https://arxiv.org/abs/2408.08631). The original README credited "Kong et al."; the arXiv record lists Kim et al.
- Shorten et al. (2024) — StructuredRAG: JSON Response Formatting with LLMs. [arXiv:2408.11061](https://arxiv.org/abs/2408.11061). The original README credited "Xu et al."; the arXiv record lists Shorten et al.
- dsdev.in (2025) — [Order of fields in structured output can hurt LLMs output](https://www.dsdev.in/order-of-fields-in-structured-output-can-hurt-llms-output).
- OpenAI (2024) — [Structured Outputs: Chain-of-Thought guide](https://developers.openai.com/api/docs/guides/structured-outputs/).
