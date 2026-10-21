"""Turn run.yml's apmx-delivery artifact into a pull-request commit.

usage: deliver.py DELIVERY_DIR WORKSPACE   (run from the repository root)

Patch outputs (Git diffs the factory exported, such as changes.diff) are
applied to this checkout with `git apply`; no fuzz, so a patch that does not
apply to main fails here. The reports (plan.md, review.md, ...) stay in the
receipt. A delivery without patches commits its outputs at their paths. The receipt is copied to WORKSPACE/.apm/.../receipt. Nothing
else changes; `apmx audit` in the pull request checks exactly that.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath


def main(delivery: Path, workspace: str) -> None:
    root = delivery / PurePosixPath(workspace)
    (index_path,) = root.glob(".apm/*/*/receipt/index.json")
    receipt = index_path.parent
    index = json.loads(index_path.read_bytes())
    outputs = {}
    for attempt in index["attempts"]:
        if attempt["selected"]:
            prefix = f"attempts/{attempt['runId']}/artifacts/"
            for name in index["files"]:
                if name.startswith(prefix):
                    outputs[name[len(prefix) :]] = (receipt / name).read_bytes()
    target = Path.cwd() / PurePosixPath(workspace)
    patches = {
        name: data
        for name, data in outputs.items()
        if name.endswith(".diff") and data.startswith(b"diff --git ")
    }
    applied, written = [], []
    for name, data in sorted(patches.items()):
        args = ["git", "apply", "--index", "--verbose"]
        if workspace not in ("", "."):
            args.append(f"--directory={PurePosixPath(workspace).as_posix()}")
        subprocess.run([*args, "-"], input=data, check=True)
        applied.append(name)
    if not patches:
        # No code change to apply: the outputs themselves are the delivery.
        for name, data in sorted(outputs.items()):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            written.append(name)
    relative = receipt.relative_to(root)
    shutil.copytree(receipt, target / relative)
    run_id = relative.parts[2]
    definition = index["definition"]["digest"]["sha256"]
    env = os.environ
    mode = env.get("MODE", "live")
    if mode == "live":
        title = f"Factory delivery: free delivery from $50 ({run_id})"
    else:
        title = f"Hermetic rehearsal (no model): run.yml fixture package ({run_id})"
    lines = [
        title,
        "",
        "Delivered by the factory workflow and signed by apmx's run.yml. Accept it by",
        "proof: the `apmx audit` check binds this change to the signed receipt.",
        "",
        f"- Run: {env.get('RUN_URL', '(local)')}",
        f"- Factory definition: `sha256:{definition}`",
        f"- Receipt: `{(PurePosixPath(workspace) / relative).as_posix()}`"
        f" (index.json `sha256:{env.get('RECEIPT', '') or 'unsigned'}`)",
        f"- Attestation: {env.get('ATTESTATION', '') or 'none'}",
        f"- Patches applied: {', '.join(applied) or 'none'}",
        f"- Outputs committed: {', '.join(written) or 'none (reports stay in the receipt)'}",
    ]
    if mode != "live":
        lines += [
            "",
            "**Hermetic rehearsal:** apmx's protocol fixture stood in for the agent. No model",
            "ran. The signing, check job and audit gate are real.",
        ]
    text = "\n".join(lines) + "\n"
    temp = Path(env.get("RUNNER_TEMP", "."))
    (temp / "commit.txt").write_text(text)
    (temp / "pr.md").write_text("\n".join(lines[2:]) + "\n")
    print(text)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
