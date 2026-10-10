"""Strict canonical encoding compatible with DNAID-CANON-1. No variant calling."""
import hashlib, hmac, re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_panel(data):
    text = data.decode("ascii")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError("Panel must use LF with a final newline")
    rows = text.splitlines()
    if not rows or rows[0] != "chromosome\tposition\tREF\tALT":
        raise ValueError("Invalid panel header")
    result, previous = [], (0, 0)
    for line in rows[1:]:
        chrom, pos, ref, alt = line.split("\t")
        if not re.fullmatch(r"chr(?:[1-9]|1[0-9]|2[0-2])", chrom):
            raise ValueError("Only canonical chr1..chr22 are supported")
        if not re.fullmatch(r"[1-9][0-9]*", pos):
            raise ValueError("Position must be canonical positive integer")
        order = (int(chrom[3:]), int(pos))
        if order <= previous:
            raise ValueError("Panel must be sorted and have unique positions")
        if ref not in "ACGT" or alt not in "ACGT" or len(ref) != 1 or len(alt) != 1 or ref == alt:
            raise ValueError("Only biallelic SNPs are supported")
        result.append((chrom, int(pos), ref, alt))
        previous = order
    if not result:
        raise ValueError("Empty panel")
    return result


def canonical(panel, policy, reference_sha256, genotypes):
    loci = read_panel(panel)
    if not re.fullmatch("[0-9a-f]{64}", reference_sha256):
        raise ValueError("Invalid reference digest")
    if len(genotypes) != len(loci) or not set(genotypes) <= set("012"):
        raise ValueError("Every frozen locus needs a validated diploid dosage")
    return ("DNAID-CANON-1\nreference_sha256=" + reference_sha256
            + "\npanel_sha256=" + digest(panel) + "\npolicy_sha256=" + digest(policy)
            + "\ngenotypes=" + genotypes + "\n").encode("ascii")


def identifier(payload, key, context):
    if len(key) != 32:
        raise ValueError("Key must contain exactly 32 random bytes")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", context):
        raise ValueError("Context must be a short ASCII namespace")
    prefix = ("DNAID-HMAC-1\ncontext=" + context + "\n").encode("ascii")
    return "DNAID-H1-" + hmac.new(key, prefix + payload, hashlib.sha256).hexdigest()
