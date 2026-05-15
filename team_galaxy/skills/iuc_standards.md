# IUC Galaxy Tool XML Authoring Standards

This document describes the standards enforced by the **Intergalactic Utilities
Commission (IUC)** for tool XML files submitted to the
[tools-iuc](https://github.com/galaxyproject/tools-iuc) repository.
Use this as your primary reference when writing or reviewing Galaxy tool wrappers.

---

## 1. File Structure

A compliant Galaxy tool XML file must have this top-level structure:

```xml
<tool id="tool_id" name="Human Readable Name" version="@TOOL_VERSION@+galaxy@VERSION_SUFFIX@" profile="23.0">
    <description>Short one-line description</description>
    <macros>
        <import>macros.xml</import>
    </macros>
    <expand macro="biotools_requirement"/>
    <expand macro="requirements"/>
    <expand macro="stdio"/>
    <command detect_errors="exit_code"><![CDATA[
        ... Cheetah template ...
    ]]></command>
    <inputs>
        ...
    </inputs>
    <outputs>
        ...
    </outputs>
    <tests>
        <test expect_num_outputs="N">
            ...
        </test>
    </tests>
    <help><![CDATA[
        ... reStructuredText help text ...
    ]]></help>
    <citations>
        <citation type="doi">10.xxxx/xxxx</citation>
    </citations>
</tool>
```

---

## 2. Versioning

- **Tool version format**: `<upstream_version>+galaxy<suffix>` where suffix is an
  integer starting at 0. Example: `2.0.4+galaxy0`.
- Always define `@TOOL_VERSION@` and `@VERSION_SUFFIX@` tokens in `macros.xml`.
- Use `profile="23.0"` (or the current release) — older profiles lack important defaults.
- Version must be updated whenever the wrapper changes, even if the upstream tool version
  is the same (increment the `+galaxy` suffix).

---

## 3. Requirements

Define tool dependencies in `macros.xml` using conda packages:

```xml
<xml name="requirements">
    <requirements>
        <requirement type="package" version="@TOOL_VERSION@">samtools</requirement>
    </requirements>
</xml>
```

- **Always pin exact versions** — never use `>=` version specifiers.
- Prefer packages from [bioconda](https://bioconda.github.io/) and
  [conda-forge](https://conda-forge.org/).
- Use the `@TOOL_VERSION@` token — never hardcode the version in two places.

---

## 4. Command Block

```xml
<command detect_errors="exit_code"><![CDATA[
    samtools sort
        -@ \${GALAXY_SLOTS:-4}
        -m \${GALAXY_MEMORY_MB_PER_SLOT:-768}M
        -o '$output'
        '$input'
]]></command>
```

- Always use `detect_errors="exit_code"`.
- Use `\${GALAXY_SLOTS:-4}` for parallelism (backslash escapes the `$`).
- Use `\${GALAXY_MEMORY_MB_PER_SLOT:-768}` for per-slot memory.
- Quote all parameter references: `'$param'`.
- Use `CDATA` blocks to avoid XML entity issues.
- Never use `&&` at the top level — use `<command>` pipes or explicit exit code checks.

---

## 5. Inputs

```xml
<inputs>
    <param name="input" type="data" format="bam,sam,cram" label="Alignment file"/>
    <param name="sort_mode" type="select" label="Sort by">
        <option value="coordinate" selected="true">Coordinate</option>
        <option value="queryname">Query name</option>
    </param>
    <param name="threads" type="integer" value="4" min="1" max="64" label="Threads"/>
    <section name="advanced" title="Advanced Options" expanded="false">
        <param name="memory" type="integer" value="768" label="Memory per thread (MB)"/>
    </section>
</inputs>
```

- Every `<param>` must have a `label`.
- Use `help=""` attribute for additional context (not required but strongly recommended).
- Group optional/advanced parameters in a `<section>`.
- Prefer `type="select"` with explicit options over `type="text"` for controlled vocabularies.
- Use `optional="true"` for truly optional parameters.

---

## 6. Outputs

```xml
<outputs>
    <data name="output_bam" format="bam" label="${tool.name} on ${on_string}"/>
    <data name="stats" format="tabular" label="${tool.name} statistics on ${on_string}">
        <filter>generate_stats</filter>
    </data>
    <collection name="split_output" type="list" label="Split output on ${on_string}"/>
</outputs>
```

- Every `<data>` output must have a `label` using `${tool.name}` and `${on_string}`.
- Use `<filter>` to conditionally produce outputs.
- Set `format` precisely — avoid `format="txt"` when a more specific type exists.

---

## 7. Tests

Tests are **mandatory** and are the most important element of a tool wrapper.

```xml
<tests>
    <test expect_num_outputs="1">
        <param name="input" value="test.bam"/>
        <param name="sort_mode" value="coordinate"/>
        <output name="output_bam" file="expected_sorted.bam" ftype="bam" compare="sim_size"/>
    </test>
    <test expect_num_outputs="1">
        <param name="input" value="test.bam"/>
        <param name="sort_mode" value="queryname"/>
        <output name="output_bam">
            <assert_contents>
                <has_n_lines n="100"/>
            </assert_contents>
        </output>
    </test>
</tests>
```

- Each test must supply test input files in `test-data/`.
- Use `compare="sim_size"` for binary formats (BAM, CRAM, BCF) to allow minor size variation.
- Use `<assert_contents>` for text-based outputs instead of exact file comparison when possible.
- Test at least the most common parameter combinations.
- Every output declared in `<outputs>` should be tested at least once.
- `expect_num_outputs` must match the actual outputs produced in that test case.

---

## 8. Help Section

```xml
<help><![CDATA[
**What it does**

SAMtools sort sorts alignments by leftmost coordinates, or by read name when
the ``-n`` option is set.

**Input**

- ``input``: SAM/BAM/CRAM alignment file

**Output**

- ``output_bam``: Sorted BAM file

**Usage notes**

Use coordinate sort before variant calling; use queryname sort before duplicate marking.

@HELP_FOOTER@
]]></help>
```

- Use reStructuredText formatting (bold with `**`, code with `` `` ``).
- Always document inputs and outputs.
- Include a `@HELP_FOOTER@` macro that links to the tool's homepage and citation.

---

## 9. Citations

```xml
<citations>
    <citation type="doi">10.1093/bioinformatics/btp352</citation>
    <citation type="bibtex">
        @article{...}
    </citation>
</citations>
```

- Always include a citation.
- Prefer `type="doi"` over bibtex.
- If the tool has no paper, include the GitHub/website URL as a bibtex url citation.

---

## 10. macros.xml conventions

```xml
<macros>
    <token name="@TOOL_VERSION@">1.21</token>
    <token name="@VERSION_SUFFIX@">0</token>
    <token name="@PROFILE@">23.0</token>

    <xml name="requirements">
        <requirements>
            <requirement type="package" version="@TOOL_VERSION@">samtools</requirement>
        </requirements>
    </xml>

    <xml name="stdio">
        <stdio>
            <exit_code range="1:" level="fatal"/>
        </stdio>
    </xml>

    <xml name="biotools_requirement">
        <xrefs>
            <xref type="bio.tools">samtools</xref>
        </xrefs>
    </xml>
</macros>
```

- All tools in a suite must share a `macros.xml`.
- Single-tool repositories still benefit from macros for `@TOOL_VERSION@`.

---

## 11. Common planemo lint checks to fix

| Error | Fix |
|---|---|
| `Tool does not define a version` | Add `version` attribute to `<tool>` |
| `Tool version is not in the recommended format` | Use `X.Y.Z+galaxyN` format |
| `No tests found` | Add `<tests>` block with at least one `<test>` |
| `Test does not check any output` | Add `<output>` or `<assert_contents>` to each test |
| `Tool does not specify a profile` | Add `profile="23.0"` to `<tool>` |
| `No help section found` | Add `<help>` block |
| `No citations found` | Add `<citations>` block |
| `Param input has no label` | Add `label` attribute to each `<param>` |
| `Stderr detected` | Add `detect_errors="exit_code"` or handle stderr properly |
