# 已有项目与本项目的位置

检索日期：2026-10-10。这是定向检索结果，不能据此认定没有其他相同方案或主张算法新颖性。

| 项目 | 已有能力 | 与这里的区别 |
| --- | --- | --- |
| [Somalier](https://github.com/brentp/somalier/blob/master/README.md) | 从 BAM/CRAM/VCF 提取基因型摘要，进行样本匹配和亲缘检查 | 适合上游独立核对；这里处理固定面板的规范编码与 HMAC 展示标识 |
| [Picard CrosscheckFingerprints](https://gatk.broadinstitute.org/hc/en-us/articles/4418062821531-CrosscheckFingerprints-Picard) | 用 SNP 与单倍型块指纹，对文件来源是否同一人进行统计比较 | 容许不确定分型的证据比较；精确摘要匹配不具备这种容错能力 |
| [NCBI GRAF](https://github.com/ncbi/graf) | 基于预选指纹 SNP 的遗传关系和祖源分析 | 目的包括亲缘与祖源推断；本仓库没有实现这类推断 |

[HMAC 标准](https://www.rfc-editor.org/rfc/rfc2104.html) 本身是已有密码学构造，安全性不依赖隐藏公式。基因指纹和 HMAC 的组合不自动提供生物学唯一性、跨次重测稳定性或匿名性。

后续适合增加 Somalier 或 Picard 作为独立样本核对层，并用独立测序重复验证固定面板。当前未实现这些集成，不能把上游项目的验证结论当成本项目已经验证的能力。
