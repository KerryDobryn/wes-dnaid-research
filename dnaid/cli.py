import argparse, json, os
from pathlib import Path
from .core import canonical, digest, identifier, read_panel
from .quality import read_vcf, validated_dosages


def main():
    parser = argparse.ArgumentParser(description="Research DNA ID from a frozen panel and locally validated calls")
    sub = parser.add_subparsers(dest="command", required=True)
    key = sub.add_parser("keygen")
    key.add_argument("path", type=Path)
    encode = sub.add_parser("encode")
    for name in ("panel", "policy", "full", "unconstrained", "half-a", "half-b", "key"):
        encode.add_argument("--" + name, type=Path, required=True)
    encode.add_argument("--reference-sha256", required=True)
    encode.add_argument("--context", required=True)
    args = parser.parse_args()
    try:
        if args.command == "keygen":
            fd = os.open(args.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(os.urandom(32))
            print("Secret key created; back it up privately. Existing keys are never overwritten.")
            return
        panel, policy = args.panel.read_bytes(), args.policy.read_bytes()
        spec = json.loads(policy)
        if spec.get("encoding") != "DNAID-CANON-1" or spec.get("qc_profile") != "bcftools-split-v1":
            raise ValueError("Unsupported policy profile")
        if spec.get("reference_sha256") != args.reference_sha256:
            raise ValueError("Policy/reference digest mismatch")
        loci = read_panel(panel)
        digits = validated_dosages(loci, *[read_vcf(p) for p in (args.full, args.unconstrained, args.half_a, args.half_b)])
        payload = canonical(panel, policy, args.reference_sha256, digits)
        print(json.dumps({"id": identifier(payload, args.key.read_bytes(), args.context),
                          "loci":len(loci), "panel_sha256":digest(panel), "policy_sha256":digest(policy),
                          "context":args.context, "status":"research-only; independent repeat unvalidated"}))
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(2, "Cannot issue ID: " + str(exc) + "\n")
