# WES DNA ID — research prototype

本项目把本地质控通过的固定 SNP 基因型转换成带私密密钥的 DNA 展示 ID。它冻结参考基因组摘要、位点文件、规则文件与编码格式，支持通过不同命名空间生成不同用途的标识。

**研究原型，版本 0.1.0。** 不承诺终身不变、全球唯一、匿名性或法医效力。它不是密码、本人认证系统，也不是完整的临床 WES 分析软件。公开仓库没有个人测序数据、真实身份 ID、个人选定位点、密钥或实际样本报告。

## 快速体验：完全合成的数据

需要 Python 3.10 或更高版本；编码工具仅使用标准库。以下命令在仓库根目录执行，无需联网、参考基因组或安装生信软件。

```sh
python3 -m unittest discover -s tests -v
mkdir -p private
python3 -m dnaid keygen private/demo.key
python3 -m dnaid encode \
  --panel examples/panel.tsv --policy examples/policy.json \
  --reference-sha256 0000000000000000000000000000000000000000000000000000000000000000 \
  --full examples/full.vcf --unconstrained examples/unconstrained.vcf \
  --half-a examples/half-a.vcf --half-b examples/half-b.vcf \
  --key private/demo.key --context synthetic-demo-v1
```

示例只有 3 个虚构位点和人为构造的 VCF 文本；零摘要代表不存在的示例参考。它用于检查编码与拒绝逻辑，不能评估个人区分能力。不要将示例用于真实身份登记。新生成密钥会使每个人的示例 ID 不同；保留同一密钥和所有输入才能重算同一个 ID。

也可用 `python3 -m pip install .` 安装 `dnaid` 命令。

## 项目提供什么

- 严格的二倍体常染色体 SNP 编码，以及完整 256 位 HMAC 输出。
- 对四份单样本调用结果执行分型质控：全量、非约束调用、互补读段子集 A/B。
- 全部固定位点必须通过；缺失、低质量或不一致时不发 ID。
- 可配置工具与参考路径的 Nextflow 候选位点分型流程。
- 合成数据测试、隐私边界、与已有项目的比较及公开前检查说明。

**不包含**从 FASTQ 开始的一键全流程、自动选择个人位点、参考/捕获数据下载、临床注释、污染估计或跨次测序稳定性验证。真实使用需先完成比对、标记重复、捕获区域覆盖检查与初始位点审核，详见 [真实数据使用边界](docs/REAL_DATA.md)。上游受许可约束的大型参考资源由使用者自行准备。

## 重算与版本管理

冻结的面板必须按 chr1 到 chr22、位置升序排列，只允许一个位置一行、单碱基 REF/ALT。基因型忽略相位，使用 REF/REF、REF/ALT、ALT/ALT 三种规范表示。计算绑定面板和规则文件的**原始字节摘要**；改缩进、换行或位点顺序也会改变 ID。

重测时应先比较同一面板的分型。任何位点失败应返回“无法重建”；不重新挑位点，不以参考型代替缺失，也不通过缩小面板强行匹配。互补子集一致性仅是同一测序文库的内部检查，不能代替独立重测。

公开 ID 能被复制及跨平台关联。密钥需私密备份；丢失后无法仅凭 DNA 恢复同一个带密钥 ID。详见 [隐私说明](docs/PRIVACY.md)。

## 相近项目

[Somalier](https://github.com/brentp/somalier)、[Picard](https://github.com/broadinstitute/picard)、[NCBI GRAF](https://github.com/ncbi/graf) 已实现不同形式的基因指纹、样本核对或亲缘推断。我们不主张首次提出 DNA 指纹；本项目的范围是可版本化的规范编码与带密钥的展示标识。详见 [项目比较](docs/RELATED_WORK.md)。

## 验证范围与许可证

本仓库的测试覆盖规范编码、密钥保护和关键质控拒绝情形。可移植 Nextflow 文件来自本地运行过的分型流程，经去除机器路径和个人覆盖常数后导出；**导出版本尚未在第二套真实数据及其他平台端到端验证**。CI 只运行合成 Python 测试。

代码使用 MIT 许可证。外部程序与参考数据库的许可独立于本项目；仓库没有重新分发它们。对研究贡献，请使用合成或明确可公开的数据，勿在 issue、PR 或日志里提交真实基因型。
