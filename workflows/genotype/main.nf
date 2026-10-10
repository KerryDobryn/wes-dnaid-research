nextflow.enable.dsl=2
params.bam = null
params.reference = null
params.candidate_bed = null
params.alleles = null
params.bcftools = null
params.outdir = null
params.samtools = "samtools"
process CALL_CANDIDATES {
    cpus 2
    memory '3 GB'
    publishDir "${params.outdir}/genotyping", mode: 'copy'
    input:
    path bam
    path bai
    path candidate_bed
    path alleles
    output:
    path '*.vcf.gz'
    path '*.vcf.gz.csi'
    path '*.txt'
    script:
    """
    set -euo pipefail
    '${params.bcftools}' mpileup -I -Ou -f '${params.reference}' -R '${candidate_bed}' -q 30 -Q 20 -E -d 10000 --ns UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY -a FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR '${bam}' 2> full-pileup.txt | '${params.bcftools}' call -m -A -i -a GQ -C alleles -T '${alleles}' -Oz -o full.calls.vcf.gz 2> full-call.txt
    '${params.bcftools}' index full.calls.vcf.gz
    '${params.bcftools}' mpileup -I -Ou -f '${params.reference}' -R '${candidate_bed}' -q 30 -Q 20 -E -d 10000 --ns UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY -a FORMAT/DP,FORMAT/AD '${bam}' 2> unconstrained-pileup.txt | '${params.bcftools}' call -m -A -a GQ -Oz -o unconstrained.calls.vcf.gz 2> unconstrained-call.txt
    '${params.bcftools}' index unconstrained.calls.vcf.gz
    '${params.samtools}' view -b -L '${candidate_bed}' -o candidate.bam '${bam}'
    '${params.samtools}' view -b -s 31.5 -U halfB.bam -o halfA.bam candidate.bam
    '${params.samtools}' index halfA.bam
    '${params.samtools}' index halfB.bam
    for part in halfA halfB; do
        '${params.bcftools}' mpileup -I -Ou -f '${params.reference}' -R '${candidate_bed}' -q 30 -Q 20 -E -d 10000 --ns UNMAP,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY -a FORMAT/DP,FORMAT/AD "\${part}.bam" 2> "\${part}-pileup.txt" | '${params.bcftools}' call -m -A -i -a GQ -C alleles -T '${alleles}' -Oz -o "\${part}.calls.vcf.gz" 2> "\${part}-call.txt"
        '${params.bcftools}' index "\${part}.calls.vcf.gz"
    done
    '${params.bcftools}' --version > bcftools-version.txt
    """
}
workflow {
    if (!params.bam || !params.reference || !params.candidate_bed || !params.alleles || !params.bcftools || !params.outdir) error 'Missing required parameter'
    bam=Channel.value(file(params.bam,checkIfExists:true))
    bai=Channel.value(file(params.bam+'.bai',checkIfExists:true))
    CALL_CANDIDATES(bam,bai,Channel.value(file(params.candidate_bed,checkIfExists:true)),Channel.value(file(params.alleles,checkIfExists:true)))
}
