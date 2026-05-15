# GTN Tutorial Format Specification

This document describes the format used by the
[Galaxy Training Network (GTN)](https://training.galaxyproject.org/) for
tutorials in the [training-material](https://github.com/galaxyproject/training-material)
repository. Use this as your reference when writing or converting tutorials.

---

## 1. File Structure

Each tutorial lives in a topic subdirectory:

```
topics/<topic>/tutorials/<tutorial-name>/
├── tutorial.md          # Main tutorial file
├── workflows/
│   └── my-workflow.ga   # Associated workflow
├── data-library.yaml    # Zenodo datasets
└── faqs/                # Optional FAQ snippets
```

---

## 2. YAML Front Matter

Every `tutorial.md` starts with YAML front matter between `---` delimiters:

```yaml
---
layout: tutorial_hands_on

title: "Variant Calling with FreeBayes"
zenodo_link: "https://zenodo.org/record/1234567"
questions:
  - "How do I call SNPs and indels from mapped reads?"
  - "What filters should I apply to variant calls?"
objectives:
  - "Run FreeBayes on a BAM file"
  - "Filter variants using VCFfilter"
  - "Understand QUAL and DP fields in VCF"
time_estimation: 1H
level: Introductory
key_points:
  - "FreeBayes is a Bayesian haplotype-based variant caller"
  - "QUAL > 20 is a common quality threshold"
contributors:
  - contributor-id-from-CONTRIBUTORS.yaml
subtopic: variant-analysis
---
```

Required fields: `layout`, `title`, `questions`, `objectives`, `time_estimation`,
`level`, `key_points`, `contributors`.

Optional: `zenodo_link`, `subtopic`, `tags`, `abbreviations`.

---

## 3. Tool References

Always reference Galaxy tools using the special Liquid tag:

```
{% tool [SAMtools sort](toolshed.g2.bx.psu.edu/repos/iuc/samtools_sort/samtools_sort/1.15.1+galaxy0) %}
```

Format: `{% tool [Display Name](toolshed_id) %}`

To find the correct ToolShed ID: go to a Galaxy instance, open the tool, and
copy the tool ID from the URL or the tool XML `id` attribute.

---

## 4. Hands-On Blocks

The core structure of GTN tutorials is the hands-on block:

```markdown
> <hands-on-title>Step 1: Sort the BAM file</hands-on-title>
>
> 1. {% tool [SAMtools sort](toolshed.g2.bx.psu.edu/repos/iuc/samtools_sort/samtools_sort/1.15.1+galaxy0) %}
>    - *"Alignment file"*: The BAM file you uploaded
>    - *"Sort by"*: `Coordinate`
>
> 2. Click **Run Tool**
{: .hands_on}
```

The `> ` prefix is Markdown blockquote syntax. The `{: .hands_on}` class
triggers the special rendering.

For tool parameters, use:
- `*"Parameter name"*:` for parameter labels (italic, in quotes)
- Backticks for values: `` `Coordinate` ``
- For datasets: refer to them as created in previous steps

---

## 5. Question and Solution Blocks

```markdown
> <question-title></question-title>
>
> 1. How many variants were called?
> 2. What does QUAL represent?
>
> > <solution-title></solution-title>
> >
> > 1. Run the **FastQC** tool and look at the *Sequence Counts* section.
> > 2. QUAL is the Phred-scaled probability that the variant call is wrong.
> {: .solution}
{: .question}
```

---

## 6. Comment, Warning, Tip, and Details Blocks

```markdown
> <comment-title>Note on reference genomes</comment-title>
>
> Use hg38 for human data unless your pipeline requires hg19.
{: .comment}

> <warning-title>Do not use raw reads</warning-title>
>
> This tool requires coordinate-sorted BAM files. Sort first with SAMtools.
{: .warning}

> <tip-title>Running faster with more threads</tip-title>
>
> Set the *Threads* parameter to match the number of cores available.
{: .tip}

> <details-title>What is a VCF file?</details-title>
>
> VCF (Variant Call Format) is a tab-delimited text format for storing
> sequence variation data.
{: .details}
```

---

## 7. Abbreviations

Define abbreviations in the YAML front matter:

```yaml
abbreviations:
  SNP: Single Nucleotide Polymorphism
  indel: insertion or deletion
```

Then use them in text as `SNP{: .abbreviation}` — GTN renders them with a tooltip.

---

## 8. Images and Figures

```markdown
![Description of the figure](../../images/variant_calling_workflow.png)
```

Place images in `topics/<topic>/images/`.

For screenshots from Galaxy: use `{% snippet faqs/galaxy/... %}` snippets
instead of static screenshots when possible — they stay updated with Galaxy UI changes.

---

## 9. data-library.yaml

```yaml
destination:
  type: library
  name: GTN - Material
  description: Galaxy Training Network Material
items:
  - name: Variant Calling Tutorial Data
    description: Test data for variant calling tutorial
    items:
      - url: https://zenodo.org/record/1234567/files/input.bam
        src: url
        ext: bam
        info: Aligned reads for variant calling
      - url: https://zenodo.org/record/1234567/files/reference.fasta
        src: url
        ext: fasta
        info: Reference genome (chrM only)
```

---

## 10. Writing Style Guidelines

- Write in second person: "You will run SAMtools…", "Click **Run Tool**".
- Introduce every tool before its hands-on block with a short paragraph
  explaining what it does and why it's needed at this point.
- After each step, interpret the output: what does the result mean biologically?
- Questions should test understanding, not just "did you click the button?".
- Key points summarise the take-home messages, not the steps.
- Avoid screenshots — use tool tags and parameter descriptions instead.
- Use `time_estimation` honestly — include time for tool run queue delays.

---

## 11. Snippet References

GTN has a library of reusable snippets for common UI operations. Use these
instead of writing your own instructions for Galaxy interface actions:

```markdown
{% snippet faqs/galaxy/histories_create_new.md %}
{% snippet faqs/galaxy/tools_upload_file.md %}
{% snippet faqs/galaxy/datasets_rename.md %}
```

Browse available snippets in `faqs/galaxy/` and `faqs/gtn/` in the training-material repo.
