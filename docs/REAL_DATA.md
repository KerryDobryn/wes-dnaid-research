# 真实数据接入：研究者操作说明

此仓库是可运行的编码层和实验性分型层，尚非从 FASTQ 开始的一键应用。

## 初次登记

1. 本地验证 FASTQ 校验值、成对一致性和全量质量，使用已核实版本的参考完成比对和标记重复，保存 BAM/BAI 与工具版本。
2. 确认捕获 BED 与参考坐标一致，检查整个靶区覆盖。建立候选常见常染色体二等位 SNP，按实际 FASTA 验证 REF；记录来源、摘要、群体频率及区块信息。
3. 在分型前核查污染、样本来源与必要的独立样本核对。白细胞并不意味着可以忽略骨髓移植、嵌合或血液克隆等特殊情况。
4. 对候选运行下述分型流程，并审查边界距离、全量与子集证据。初次面板选择只能在登记时完成。捕获边缘距离、每来源块一个代表等面板设计约束由上游核实；编码 CLI 不负责它们。
5. 冻结 panel.tsv、policy.json、参考 SHA-256、源数据库与软件版本。使用示例 policy 结构，但填写真实参考摘要并保留 `qc_profile=bcftools-split-v1`。该 profile 代表代码中的固定质控规则，不会根据自定义 JSON 字段自动改变阈值。
6. 生成私密密钥，运行 encode，私密保存四份分型与审核证据。独立重测成功前只称研究指纹。

不能仅把普通变异 VCF 的“未列出位点”当成参考纯合。需要显式覆盖所有固定位点的调用结果；所有输入为单样本。

## 分型流程

预先安装 Nextflow、bcftools 1.24/HTSlib 1.24、samtools，提供坐标排序并标记重复的 BAM 和同名 `.bam.bai`，以及已索引的匹配参考 FASTA。参数路径与值不得含单引号、美元符号、换行或其他 shell 插值字符；当前实验性流程直接插入 shell 参数，只适合可信本地配置。

候选 BED 每行是 `chromosome start end`，每个 SNP 用 0-based 半开区间 `[position-1, position)`；alleles TSV 每行是 `chromosome position REF,ALT`（1-based）。它们应从同一固定面板生成，不能跨构建混用。

```sh
nextflow run workflows/genotype/main.nf \
  --bam /absolute/local/sample.marked.bam \
  --reference /absolute/local/reference.fa \
  --candidate_bed /absolute/local/panel.bed \
  --alleles /absolute/local/panel-alleles.tsv \
  --bcftools /absolute/local/bin/bcftools \
  --samtools /absolute/local/bin/samtools \
  --outdir /absolute/local/runs/genotyping
```

输出全量、非约束、halfA、halfB VCF.gz 及索引；encode 的 `--half-a` 对应 `halfA.calls.vcf.gz`。全量与非约束调用必须来自同一输入；互补子集由同一 BAM 的 read-name hash 分割。用户提供的四个文件仍需信任链，CLI 无法证明它们真的来自相同文库或互补划分，也无法仅凭 VCF 验证参考摘要。

质控：MAPQ≥30，BQ/BAQ≥20，忽略重复、次级、补充等标记；SNP-only、重新 BAQ。全量 DP 30–2000、PL 分离度≥40、可用 GQ≥30；AD/DP 0.95–1.05；杂合 ALT 比例 0.3–0.7、纯合目标比例≥0.95；实际存在的每个等位基因双链各至少 3 个支持。子集 DP≥10、PL 分离度≥20、杂合比例 0.2–0.8、纯合≥0.9；需与全量一致。PL 分离度不等于校准后的 GQ。FILTER 为 `.` 仅在这种受控、尚未设置过滤标记的调用输出中允许，不能解释为任意 VCF 都通过了上游质控。

## 重测

沿用相同参考、面板、调用规则、密钥和命名空间；逐位点检查质量及差异，再比较 ID。任何单个位点变化都会使完整 ID 改变。不要重新选择面板来获取匹配。不同面板所得 ID 不能直接比较来判断是否同一人。

没有实施污染估计、祖源校准碰撞概率、临床注释排除或同卵双胞胎区分。公开合成案例验证软件行为，不验证生物学稳定性。完整可信部署还需要真实独立重复、人口样本评估、软件与资源摘要核对及平台移植验证。
