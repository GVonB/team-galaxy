# IWC Workflow Quality Checklist

This document describes the quality standards enforced by the
**Intergalactic Workflow Commission (IWC)** for Galaxy workflows submitted to
[iwc-workflows](https://github.com/iwc-workflows). Every workflow must satisfy
all items in this checklist before a PR can be merged.

---

## 1. Workflow File (`.ga`)

### Required metadata (inside the `.ga` JSON)

- [ ] `annotation` field is present and non-empty — a clear one-line description
  of what the workflow does.
- [ ] `license` field is set to a valid SPDX license identifier (e.g., `MIT`,
  `Apache-2.0`, `CC-BY-4.0`).
- [ ] `creator` is an array with at least one entry; each entry must have:
  - `class: "Person"` (or `"Organization"`)
  - `identifier`: ORCID URL, e.g., `"https://orcid.org/0000-0000-0000-0000"`
  - `name`: full name string
- [ ] All workflow steps have a non-empty `annotation` field.
- [ ] All output steps have a non-empty `label` (human-readable name for the output).
- [ ] The workflow has at least one formal `input` step with a non-empty `label`.
- [ ] No `subworkflow` steps reference external `.ga` files by local path — only
  Tool Shed or registered IWC workflows.

### planemo workflow_lint must pass with exit 0

Run: `planemo workflow_lint <workflow.ga>`

Common failures to fix:

| Warning/Error | Fix |
|---|---|
| `Missing workflow annotation` | Set `annotation` in the workflow JSON |
| `Missing license` | Set `license` to an SPDX identifier |
| `Missing creator` | Add `creator` array with ORCID and name |
| `Step annotation missing` | Add `annotation` to every step |
| `Output label missing` | Set `label` on every output step |

---

## 2. Test File (`*-tests.yml`)

Every workflow submission requires a companion test file named
`<workflow-name>-tests.yml` in the same directory.

```yaml
- doc: Test with paired-end input on hg38
  job:
    input_reads:
      class: File
      path: test-data/reads_1.fastq.gz
      filetype: fastqsanger.gz
    reference: hg38
  outputs:
    aligned_bam:
      asserts:
        has_size:
          min: 1000
```

Checklist:
- [ ] Test file exists: `<workflow-name>-tests.yml`
- [ ] At least one test case is defined.
- [ ] All workflow inputs are provided in the `job:` block.
- [ ] All workflow outputs are checked under `outputs:`.
- [ ] Test data files are committed to `test-data/` within the workflow directory.
- [ ] Test data is minimal (< 1 MB per file where possible).

---

## 3. CHANGELOG.md

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

```markdown
# Changelog

## [Unreleased]

## [0.1] 2024-01-15

### Added
- Initial workflow submission
```

Checklist:
- [ ] `CHANGELOG.md` exists in the workflow directory.
- [ ] The latest version entry matches the workflow's current version.
- [ ] All significant changes are documented under `Added`, `Changed`, `Fixed`,
  `Deprecated`, `Removed`, or `Security` headings.

---

## 4. `.dockstore.yml`

```yaml
version: 1.2
workflows:
  - subclass: Galaxy
    primaryDescriptorPath: /my-workflow.ga
    testParameterFiles:
      - /my-workflow-tests.yml
    topic: topic-0013
    name: my-workflow
    description: Short description for Dockstore.
```

Checklist:
- [ ] `.dockstore.yml` exists in the workflow directory.
- [ ] `primaryDescriptorPath` points to the `.ga` file.
- [ ] `testParameterFiles` lists the `*-tests.yml` file.
- [ ] `topic` is set to a valid EDAM topic term (e.g., `topic-0013` = Sequence analysis).

---

## 5. README.md

```markdown
# Workflow Name

Short description of what the workflow does and when to use it.

## Inputs

| Label | Description | Format |
|---|---|---|
| input_reads | Raw sequencing reads | fastqsanger.gz |

## Outputs

| Label | Description | Format |
|---|---|---|
| aligned_bam | Aligned reads | bam |

## Tools Used

- BWA-MEM2
- SAMtools

## Citation

If you use this workflow, please cite:
...
```

Checklist:
- [ ] `README.md` exists.
- [ ] Inputs and outputs are documented with labels, descriptions, and formats.
- [ ] Major tools used are listed.
- [ ] Citation or acknowledgment section is present.

---

## 6. Directory Structure

```
my-workflow/
├── my-workflow.ga            # The Galaxy workflow file
├── my-workflow-tests.yml     # Test file
├── CHANGELOG.md
├── README.md
├── .dockstore.yml
└── test-data/
    ├── input_reads.fastq.gz
    └── expected_output.bam
```

- [ ] All required files are present.
- [ ] Test data is in `test-data/` subdirectory.
- [ ] No binary files other than test data are committed.

---

## 7. Final submission checklist

- [ ] `planemo workflow_lint <workflow.ga>` exits 0
- [ ] All required files are present (`.ga`, `*-tests.yml`, `CHANGELOG.md`, `README.md`, `.dockstore.yml`)
- [ ] Workflow metadata complete (annotation, license, creator with ORCID, step annotations, output labels)
- [ ] Test file covers all inputs and outputs
- [ ] Test data committed to `test-data/`
- [ ] CHANGELOG updated
- [ ] README documents inputs and outputs
