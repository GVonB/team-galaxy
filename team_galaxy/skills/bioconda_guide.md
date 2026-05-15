# Bioconda Packaging Guide

This document describes the conventions and requirements for packaging Galaxy tool
dependencies in [Bioconda](https://bioconda.github.io/) and submitting recipes to
the [bioconda-recipes](https://github.com/bioconda/bioconda-recipes) repository.
Use this when a Galaxy tool wrapper requires a conda package that does not yet exist
or needs updating.

---

## 1. Recipe Structure

```
recipes/<package-name>/
├── meta.yaml      # Required: package metadata
├── build.sh       # Required for compiled packages
├── bld.bat        # Required for Windows (usually not needed in bioconda)
└── test/          # Optional: test scripts
```

---

## 2. meta.yaml Structure

```yaml
{% set version = "1.21" %}

package:
  name: samtools
  version: {{ version }}

source:
  url: https://github.com/samtools/samtools/releases/download/{{ version }}/samtools-{{ version }}.tar.bz2
  sha256: <sha256_hash_of_tarball>

build:
  number: 0
  run_exports:
    - {{ pin_subpackage("samtools", max_pin="x.x") }}

requirements:
  build:
    - {{ compiler('c') }}
    - make
  host:
    - zlib
    - bzip2
    - xz
    - curl
    - htslib {{ version }}
  run:
    - htslib {{ version }}

test:
  commands:
    - samtools --version
    - samtools view --help 2>&1 | grep -q "Usage"

about:
  home: https://www.htslib.org/
  license: MIT
  license_family: MIT
  license_file: LICENSE
  summary: "Tools for manipulating next-generation sequencing data"
  description: |
    SAMtools is a suite of programs for interacting with high-throughput
    sequencing data in SAM/BAM/CRAM format.
  doc_url: https://www.htslib.org/doc/samtools.html
  dev_url: https://github.com/samtools/samtools

extra:
  additional-platforms:
    - linux-aarch64
    - osx-arm64
  identifiers:
    - biotools:samtools
    - doi:10.1093/bioinformatics/btp352
```

---

## 3. Versioning Rules

- **`build.number`** starts at `0` for each new upstream version. Increment it
  when rebuilding with the same upstream version (e.g., to fix a packaging bug).
- **`run_exports`** should pin to `x.x` for libraries; omit for pure command-line tools.
- Never use `>=` in `host:` or `run:` sections — always pin exactly or use
  `{{ pin_compatible(...) }}`.

---

## 4. Checksums

Always provide a `sha256` checksum for source archives. Generate with:

```bash
curl -sL <url> | sha256sum
```

Never use `md5` — bioconda requires `sha256`.

---

## 5. Test Block

Every package must have a `test:` block that:
- Runs the main command with `--version` or `--help`
- Verifies a key subcommand works
- For Python packages: imports the main module

```yaml
test:
  imports:
    - bioblend
    - bioblend.galaxy
  commands:
    - python -c "import bioblend; print(bioblend.__version__)"
```

---

## 6. Python Packages

```yaml
package:
  name: bioblend
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/b/bioblend/bioblend-{{ version }}.tar.gz
  sha256: <sha256>

build:
  number: 0
  script: {{ PYTHON }} -m pip install . --no-deps --no-build-isolation -vvv

requirements:
  host:
    - python
    - pip
    - setuptools
  run:
    - python
    - requests >=2.20
    - tuspy

test:
  imports:
    - bioblend
```

---

## 7. Multi-Output Packages

When a package provides both a library and command-line tools, split into outputs:

```yaml
outputs:
  - name: samtools
    files:
      - bin/samtools
    test:
      commands:
        - samtools --version
  - name: libhts
    files:
      - lib/libhts*
      - include/htslib
```

---

## 8. Common Mistakes

| Mistake | Fix |
|---|---|
| Missing `sha256` | Add `sha256:` to `source:` |
| `license_file` missing | Point to the LICENSE file in the source tree |
| Test not checking the actual binary | Add `commands: - <tool> --version` |
| `run_exports` on a CLI tool | Remove it (only needed for libraries) |
| Hardcoded version in URLs | Use `{{ version }}` Jinja variable |
| No `extra.identifiers` | Add `biotools:` and `doi:` identifiers when available |

---

## 9. Updating an Existing Package

1. Update `version` at the top of `meta.yaml`.
2. Update `sha256` for the new source tarball.
3. Reset `build.number` to `0`.
4. Check if any `requirements` version pins need updating.
5. Run `bioconda-utils lint recipes/<package>` locally before opening a PR.

---

## 10. bioconda-utils lint checks

```bash
# Install bioconda-utils (in the bioconda-recipes conda env)
conda install bioconda-utils

# Lint your recipe
bioconda-utils lint recipes/<package-name> --packages <package-name>
```

Common lint errors:
- `uses_setuptools` — pin setuptools in `host:` requirements
- `missing_tests` — add a `test:` block
- `should_be_noarch_python` — add `noarch: python` to `build:` for pure Python packages
- `missing_license_file` — set `license_file:` in `about:`
