"""Research QC for bcftools 1.24 single-sample SNP calls; not generic VCF QC."""
import gzip, math


def read_vcf(path):
    records = {}
    opener = gzip.open if str(path).endswith(".gz") else open
    header = False
    with opener(path, "rt") as handle:
        for line in handle:
            if line.startswith("#CHROM"):
                if len(line.rstrip().split("\t")) != 10:
                    raise ValueError("Exactly one VCF sample is required")
                header = True
            if line.startswith("#"):
                continue
            v = line.rstrip("\n").split("\t")
            if not header or len(v) != 10:
                raise ValueError("Invalid single-sample VCF")
            key = (v[0], int(v[1]))
            if key in records:
                raise ValueError("Duplicate VCF position")
            records[key] = {"ref":v[3], "alts":v[4].split(",") if v[4]!="." else [],
                            "filter":v[6], "format":dict(zip(v[8].split(":"),v[9].split(":")))}
    if not header:
        raise ValueError("Missing VCF header")
    return records


def bases(record):
    if not record:
        return None
    bits = record["format"].get("GT", ".").replace("|", "/").split("/")
    if len(bits) != 2 or any(x not in ("0", "1") for x in bits):
        return None
    alleles = [record["ref"]] + record["alts"]
    try:
        return tuple(sorted(alleles[int(x)] for x in bits))
    except IndexError:
        return None


def quality(v,min_dp,min_gap,balance,purity):
 if not v:return False,'missing_record',{}
 f=v['format'];g=f.get('GT','.').replace('|','/');bits=g.split('/')
 if len(bits)!=2 or any(x not in ('0','1') for x in bits):return False,'missing_or_non_biallelic_gt',{}
 dosage=sum(map(int,bits));index=dosage
 try:
  dp=int(f['DP']);ad=list(map(int,f['AD'].split(',')));pl=list(map(int,f['PL'].split(',')))
 except (KeyError,ValueError):return False,'missing_depth_or_likelihood',{}
 if len(ad)!=2 or len(pl)!=3 or any(x<0 for x in ad+pl) or dp<=0 or sum(ad)==0:return False,'unexpected_ad_or_pl_shape',{}
 chosen=pl[index];gap=min(x for i,x in enumerate(pl) if i!=index)-chosen
 stats={'DP':dp,'AD':ad,'PLgap':gap,'dosage':dosage,'GQ':f.get('GQ')}
 if dp<min_dp or dp>2000:return False,'depth_outside_policy',stats
 if not .95<=sum(ad)/dp<=1.05:return False,'allele_depth_denominator_inconsistent',stats
 if gap<min_gap:return False,'insufficient_PLgap',stats
 if f.get('GQ') not in (None,'.') and (not math.isfinite(float(f['GQ'])) or float(f['GQ'])<30):return False,'low_GQ',stats
 af=ad[1]/sum(ad);stats['alt_fraction']=af
 if dosage==1 and not balance[0]<=af<=balance[1]:return False,'heterozygote_imbalance',stats
 if dosage==0 and ad[0]/sum(ad)<purity:return False,'reference_purity',stats
 if dosage==2 and af<purity:return False,'alternate_purity',stats
 return True,'PASS',stats


def validated_dosages(panel, full, unconstrained, half_a, half_b):
    digits = []
    for chrom, pos, ref, alt in panel:
        key = (chrom, pos)
        v = full.get(key)
        ok, reason, stats = quality(v, 30, 40, (.3, .7), .95)
        if not ok:
            raise ValueError(f"Locus {chrom}:{pos} failed: {reason}")
        if v["ref"] != ref or v["alts"] != [alt] or v["filter"] not in ("PASS", "."):
            raise ValueError("Full-call allele/filter mismatch")
        u = unconstrained.get(key)
        if not u or u["filter"] not in ("PASS", ".") or bases(u) != bases(v):
            raise ValueError("Unconstrained call disagrees")
        try:
            forward = list(map(int, v["format"]["ADF"].split(",")))
            reverse = list(map(int, v["format"]["ADR"].split(",")))
        except (KeyError, ValueError):
            raise ValueError("Missing strand support") from None
        present = [0, 1] if stats["dosage"] == 1 else [stats["dosage"] // 2]
        if len(forward) != 2 or len(reverse) != 2 or any(x < 0 for x in forward + reverse) or any(forward[i] < 3 or reverse[i] < 3 for i in present):
            raise ValueError("Insufficient strand support")
        for half in (half_a, half_b):
            h = half.get(key)
            passed, _, _ = quality(h, 10, 20, (.2, .8), .9)
            if not passed or h["ref"] != ref or h["alts"] != [alt] or h["filter"] not in ("PASS", ".") or bases(h) != bases(v):
                raise ValueError("Half-library validation failed")
        digits.append(str(stats["dosage"]))
    return "".join(digits)
