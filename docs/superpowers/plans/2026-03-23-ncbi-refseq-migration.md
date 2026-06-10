# NCBI/RefSeq Migration & Cell Culture Rename Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update IsoAPA to work with the new NCBI/RefSeq data format, fix ETL for the new folder structure (tissue/cell_culture), add transcript_biotype to the transcript detail page, and replace "cell line" with "cell culture" throughout.

**Architecture:** The data files already use the new format (10-column TSV with NCBI accessions), so changes are code-only. Backend ETL, database schema, API schemas, and routes need updates. Frontend views need text/link updates.

**Tech Stack:** Python/FastAPI/SQLAlchemy (backend), Vue 3/Vuetify 3 (frontend)

---

## File Structure

### Files to Modify:
- `backend/app/services/etl.py` — Fix folder traversal, read transcript_biotype, set sample_type
- `backend/app/models/database.py` — Already has transcript_biotype (verified) and sample_type default change
- `backend/app/schemas/schemas.py` — Rename cell_lines→samples, add transcript_biotype to SearchResult
- `backend/app/api/routes.py` — Fix FASTA path lookup (.fna), rename cell_lines→samples in response, return transcript_biotype
- `backend/app/services/pas_annotator.py` — Fix chromosome matching for NCBI accessions (NC_*)
- `backend/reannotate_pas.py` — Update hardcoded Ensembl FASTA filenames
- `frontend/src/views/LocusDetail.vue` — Add transcript_biotype to header card, update Ensembl link
- `frontend/src/views/GeneDetail.vue` — Update MyGene.info query for NCBI gene IDs, update Ensembl link logic
- `frontend/src/views/Search.vue` — Rename item.cell_lines→item.samples
- `frontend/src/views/Home.vue` — Update "cell line" text references
- `frontend/src/views/Help.vue` — Update "cell line" and Ensembl text
- `frontend/src/views/Download.vue` — Update schema descriptions from Ensembl to NCBI/RefSeq
- `frontend/src/components/SplicingApaCouplingPanel.vue` — Replace "cell line" text
- `frontend/src/components/IsoformFingerprintPanel.vue` — Update shortId() for NM_ prefix
- `README.md` — Update example IDs and data format docs

---

## Chunk 1: Backend — ETL & Database & Schema

### Task 1: Fix ETL `get_fasta_path()` to find .fna files

**Files:**
- Modify: `backend/app/services/etl.py:32-40`

- [ ] **Step 1: Add .fna extension to get_fasta_path()**

In `etl.py` line 38, change:
```python
if f.endswith('.fa') or f.endswith('.fasta'):
```
to:
```python
if f.endswith('.fa') or f.endswith('.fasta') or f.endswith('.fna'):
```

- [ ] **Step 2: Also fix get_species_ref_path() in routes.py**

In `routes.py` line 78, change:
```python
elif file_type == 'fasta' and (f.endswith('.fa') or f.endswith('.fasta')):
```
to:
```python
elif file_type == 'fasta' and (f.endswith('.fa') or f.endswith('.fasta') or f.endswith('.fna')):
```

### Task 2: Fix ETL `get_apa_files()` for new folder structure

**Files:**
- Modify: `backend/app/services/etl.py:43-61`

- [ ] **Step 1: Rewrite get_apa_files() to traverse tissue/cell_culture subdirectories**

Replace the entire `get_apa_files` function (lines 43-61) with:
```python
def get_apa_files(species_folder: str) -> list:
    """Get all APA data files for a species.

    Supports nested layout: species_dir / {tissue,cell_culture} / sample_name / *.txt|tsv
    Also supports flat layout: species_dir / sample_name / *.txt|tsv  (legacy)
    """
    species_dir = os.path.join(DATA_DIR, species_folder)
    apa_files = []

    if not os.path.exists(species_dir):
        return apa_files

    for item in os.listdir(species_dir):
        item_path = os.path.join(species_dir, item)
        if not os.path.isdir(item_path) or item == 'reference':
            continue

        # Check if this is a category folder (tissue / cell_culture)
        if item in ('tissue', 'cell_culture'):
            sample_type = item  # 'tissue' or 'cell_culture'
            for sample_name in os.listdir(item_path):
                sample_path = os.path.join(item_path, sample_name)
                if not os.path.isdir(sample_path):
                    continue
                for f in os.listdir(sample_path):
                    if f.endswith('.txt') or f.endswith('.tsv'):
                        apa_files.append({
                            'sample_name': sample_name,
                            'sample_type': sample_type,
                            'file_path': os.path.join(sample_path, f)
                        })
        else:
            # Legacy flat layout: species_dir / sample_name / *.txt
            for f in os.listdir(item_path):
                if f.endswith('.txt') or f.endswith('.tsv'):
                    apa_files.append({
                        'sample_name': item,
                        'sample_type': 'cell_culture',  # default for legacy
                        'file_path': os.path.join(item_path, f)
                    })

    return apa_files
```

### Task 3: Fix ETL `ingest_data()` to read transcript_biotype and set sample_type

**Files:**
- Modify: `backend/app/services/etl.py:114-172`

- [ ] **Step 1: Pass sample_type when creating Sample records**

Change line 124 from:
```python
sample = Sample(name=sample_name, species_id=species_id)
```
to:
```python
sample_type = apa_file_info.get('sample_type', 'cell_culture')
sample = Sample(name=sample_name, species_id=species_id, sample_type=sample_type)
```

- [ ] **Step 2: Read transcript_biotype from TSV and store it**

After line 146 (`site_abundance = float(row['site_abundance'])`), add:
```python
transcript_biotype = row.get('transcript_biotype', None)
```

Then change the Transcript creation block (lines 162-172) from:
```python
if transcript_id not in transcript_map:
    transcript = db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    if not transcript:
        transcript = Transcript(
            transcript_id=transcript_id,
            gene_id=gene_map[gene_id]
        )
        db.add(transcript)
        db.flush()
    transcript_map[transcript_id] = transcript.id
    transcript_count += 1
```
to:
```python
if transcript_id not in transcript_map:
    transcript = db.query(Transcript).filter(Transcript.transcript_id == transcript_id).first()
    if not transcript:
        transcript = Transcript(
            transcript_id=transcript_id,
            gene_id=gene_map[gene_id],
            transcript_biotype=transcript_biotype
        )
        db.add(transcript)
        db.flush()
    elif transcript_biotype and not transcript.transcript_biotype:
        transcript.transcript_biotype = transcript_biotype
    transcript_map[transcript_id] = transcript.id
    transcript_count += 1
```

### Task 4: Update database.py default sample_type

**Files:**
- Modify: `backend/app/models/database.py:34`

- [ ] **Step 1: Change default sample_type from "cell_line" to "cell_culture"**

Change:
```python
sample_type = Column(String(50), nullable=False, default="cell_line")
```
to:
```python
sample_type = Column(String(50), nullable=False, default="cell_culture")
```

### Task 5: Update Pydantic schemas — rename cell_lines → samples

**Files:**
- Modify: `backend/app/schemas/schemas.py:19-30, 106-128`

- [ ] **Step 1: Rename CellLineBase/CellLine to SampleBase/SampleSchema**

Replace lines 19-30 with:
```python
class SampleBase(BaseModel):
    name: str
    species_id: int
    sample_type: str = "cell_culture"


class SampleSchema(SampleBase):
    id: int
    species: Optional[Species] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Update SearchResult — rename cell_lines to samples**

Change line 113:
```python
cell_lines: List[str]
```
to:
```python
samples: List[str]
```

- [ ] **Step 3: Update DashboardStats — rename cell_line fields to sample**

Change lines 124, 127:
```python
total_cell_lines: int
...
apa_sites_by_cell_line: List[dict]
```
to:
```python
total_samples: int
...
apa_sites_by_sample: List[dict]
```

### Task 6: Update routes.py — rename cell_line references

**Files:**
- Modify: `backend/app/api/routes.py:103-112, 173-184`

- [ ] **Step 1: Update get_dashboard_stats response**

Change lines 107, 110:
```python
total_cell_lines=total_samples,
...
apa_sites_by_cell_line=[],
```
to:
```python
total_samples=total_samples,
...
apa_sites_by_sample=[],
```

- [ ] **Step 2: Update search_transcripts response**

Change line 180:
```python
cell_lines=list(sample_names),
```
to:
```python
samples=list(sample_names),
```

- [ ] **Step 3: Commit backend changes**

```bash
git add backend/
git commit -m "feat: update ETL for new folder structure, add transcript_biotype, rename cell_line→sample"
```

---

## Chunk 2: Backend — PAS Annotator & FASTA/Reference Updates

### Task 7: Fix PAS annotator chromosome matching for NCBI accessions

**Files:**
- Modify: `backend/app/services/pas_annotator.py:100-137, 226, 285, 336`

- [ ] **Step 1: Update _load_chromosome() to handle NCBI accession headers**

The current code strips 'chr' prefix and matches against FASTA headers. NCBI FASTA headers are like `>NC_000012.12 Homo sapiens chromosome 12, GRCh38.p14...`

Replace lines 100-137 (`_load_chromosome` method) with:
```python
def _load_chromosome(self, chrom: str) -> Optional[str]:
    """Load (and cache) a chromosome sequence from the FASTA file."""
    if chrom in self._sequences:
        return self._sequences[chrom]

    if not self.fasta_path.exists():
        return None

    try:
        sequence: List[str] = []
        # Support both Ensembl (e.g. '1', 'chr1') and NCBI (e.g. 'NC_000001.11') headers
        target_variants = set()
        target_variants.add(chrom)
        target_variants.add(chrom.replace('chr', ''))
        target_variants.add('chr' + chrom.replace('chr', ''))
        current: Optional[str] = None
        matched = False

        with open(self.fasta_path, 'r') as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('>'):
                    if sequence and matched:
                        break
                    # Header format varies:
                    # Ensembl: >1 dna:chromosome chromosome:GRCh38:1:...
                    # NCBI:    >NC_000012.12 Homo sapiens chromosome 12, ...
                    header_id = line[1:].split()[0]
                    matched = header_id in target_variants
                    if matched:
                        sequence = []
                elif matched:
                    sequence.append(line.upper())

        if sequence:
            seq_str = ''.join(sequence)
            self._sequences[chrom] = seq_str
            logger.info(f"Loaded chromosome {chrom}: {len(seq_str):,} bp")
            return seq_str

        logger.warning(f"Chromosome {chrom} not found in FASTA")
        return None

    except Exception as exc:
        logger.error(f"Error loading chromosome {chrom}: {exc}")
        return None
```

- [ ] **Step 2: Remove chr prefix stripping from find_pas_hexamer and find_auxiliary_motifs**

In `find_pas_hexamer` (line 226), change:
```python
chrom = chrom.replace('chr', '')
```
to:
```python
# Keep chrom as-is — _load_chromosome handles all formats
```
(Remove the line entirely)

In `find_auxiliary_motifs` (line 285), similarly remove:
```python
chrom = chrom.replace('chr', '')
```

In `annotate_site` (line 336), change:
```python
chrom_norm = chrom.replace('chr', '')
seq = self._load_chromosome(chrom_norm)
```
to:
```python
seq = self._load_chromosome(chrom)
```

### Task 8: Update reannotate_pas.py for new FASTA filenames

**Files:**
- Modify: `backend/reannotate_pas.py`

- [ ] **Step 1: Update hardcoded FASTA filename references**

Check if reannotate_pas.py hardcodes Ensembl filenames and update to use the same `get_fasta_path()` helper that now supports `.fna`.

### Task 9: Update routes.py FASTA sequence retrieval

**Files:**
- Modify: `backend/app/api/routes.py:756-783`

- [ ] **Step 1: Update _fetch_fasta_seq to handle NCBI chromosome accessions**

The current `_fetch_fasta_seq` function tries `chrom`, `chrom.lstrip('chr')`, and `'chr' + chrom`. For NCBI accessions like `NC_000012.12`, this is already fine since it first tries the exact chrom. No change needed here if the FASTA index uses the same accession format.

- [ ] **Step 2: Commit PAS annotator changes**

```bash
git add backend/
git commit -m "fix: update PAS annotator chromosome matching for NCBI accessions"
```

---

## Chunk 3: Frontend — Cell Culture Rename & NCBI Links

### Task 10: Update LocusDetail.vue — add transcript_biotype to header card

**Files:**
- Modify: `frontend/src/views/LocusDetail.vue:26-65, 818-822`

- [ ] **Step 1: Add transcript_biotype field to gene-header-card**

After the "PA Sites" meta item (around line 55), add a new meta item:
```html
<div class="gene-meta-item" v-if="locusData.transcript.transcript_biotype">
  <span class="gene-meta-label">Biotype</span>
  <span class="gene-meta-value">
    <v-chip size="small" variant="tonal" color="info">{{ locusData.transcript.transcript_biotype }}</v-chip>
  </span>
</div>
```

- [ ] **Step 2: Update Ensembl browser link to NCBI**

Change the `ensemblBrowserLink` computed (lines 818-822) from:
```javascript
const ensemblBrowserLink = computed(() => {
  if (!locusData.value) return ''
  const gene = locusData.value.gene
  return `https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${gene.gene_id}`
})
```
to:
```javascript
const ncbiBrowserLink = computed(() => {
  if (!locusData.value) return ''
  const gene = locusData.value.gene
  return `https://www.ncbi.nlm.nih.gov/gene/${gene.gene_id}`
})
```

### Task 11: Update GeneDetail.vue — fix MyGene.info query for NCBI gene IDs

**Files:**
- Modify: `frontend/src/views/GeneDetail.vue:120-122, 365-369`

- [ ] **Step 1: Update See related links — remove Ensembl conditional on gene_id prefix**

Change line 120:
```html
<span v-if="geneSummaryData.ensemblGene || geneData.gene_id?.startsWith('ENS')" class="gs-id-entry">
```
to:
```html
<span v-if="geneSummaryData.ensemblGene" class="gs-id-entry">
```

- [ ] **Step 2: Add NCBI Gene link using numeric gene_id**

After the Ensembl entry block and before the RefSeq block, add:
```html
<span v-if="geneData.gene_id && !geneData.gene_id.startsWith('ENS')" class="gs-id-entry">
  <span class="gs-id-source">NCBI Gene</span>
  <a :href="`https://www.ncbi.nlm.nih.gov/gene/${geneData.gene_id}`" target="_blank" class="gs-id-code gs-id-href">{{ geneData.gene_id }}</a>
</span>
```

- [ ] **Step 3: Update MyGene.info query to use NCBI gene ID**

Change line 369:
```javascript
const url = `https://mygene.info/v3/query?q=ensembl.gene:${ensemblGeneId}&fields=name,summary,pathway.kegg,uniprot,entrezgene,HGNC,symbol,alias,type_of_gene,refseq,ensembl&species=human,mouse&size=1`
```
to:
```javascript
const url = `https://mygene.info/v3/query?q=${geneId}&fields=name,summary,pathway.kegg,uniprot,entrezgene,HGNC,symbol,alias,type_of_gene,refseq,ensembl&species=human,mouse&size=1`
```

And update the function signature and caller to pass gene_id instead of ensemblGeneId.

### Task 12: Update Search.vue — rename cell_lines to samples

**Files:**
- Modify: `frontend/src/views/Search.vue:121-132, 280-289, 345-351`

- [ ] **Step 1: Change item.cell_lines references to item.samples**

In the template (lines 123, 130), change:
```html
v-for="sample in item.cell_lines.slice(0, 3)"
...
<span v-if="item.cell_lines.length > 3" class="text-caption">
  +{{ item.cell_lines.length - 3 }} more
```
to:
```html
v-for="sample in item.samples.slice(0, 3)"
...
<span v-if="item.samples.length > 3" class="text-caption">
  +{{ item.samples.length - 3 }} more
```

- [ ] **Step 2: Update CSV export**

In line 289, change:
```javascript
item.cell_lines.join('; ')
```
to:
```javascript
item.samples.join('; ')
```

- [ ] **Step 3: Remove duplicate watch with cell_line reference**

Remove the second watch block (lines 345-351) that references `newQuery.cell_line`.

### Task 13: Update Home.vue — replace "cell line" text

**Files:**
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: Replace "cell line" / "cell lines" text with "cell culture" / "cell cultures"**

Search for "cell line" in Home.vue and replace with "cell culture" (or "sample" where contextually appropriate).

### Task 14: Update Help.vue — replace cell line and Ensembl text

**Files:**
- Modify: `frontend/src/views/Help.vue`

- [ ] **Step 1: Replace "cell line" with "cell culture" throughout**
- [ ] **Step 2: Replace Ensembl example IDs with NCBI/RefSeq examples**

Change examples like `ENST00000000233` to `NM_021104.2` and `ENSG00000004059` to numeric gene IDs.

### Task 15: Update Download.vue — update schema descriptions

**Files:**
- Modify: `frontend/src/views/Download.vue`

- [ ] **Step 1: Replace "Ensembl Gene ID" / "Ensembl Transcript ID" with "NCBI Gene ID" / "RefSeq Transcript ID"**

### Task 16: Update SplicingApaCouplingPanel.vue — replace cell line text

**Files:**
- Modify: `frontend/src/components/SplicingApaCouplingPanel.vue`

- [ ] **Step 1: Replace all "cell line" / "Cell Line" text with "cell culture" / "Cell Culture"**

### Task 17: Update IsoformFingerprintPanel.vue — fix shortId()

**Files:**
- Modify: `frontend/src/components/IsoformFingerprintPanel.vue`

- [ ] **Step 1: Update shortId() to handle NM_ prefix**

The current function strips 'ENST' prefix. Update to also handle NM_/NR_/XM_ prefixes.

### Task 18: Commit frontend changes

- [ ] **Step 1: Commit all frontend changes**

```bash
git add frontend/ README.md
git commit -m "feat: rename cell line → cell culture, update Ensembl → NCBI/RefSeq links, add transcript_biotype"
```

---

## Chunk 4: README & Final Verification

### Task 19: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update data folder structure documentation**

Replace the old flat structure with:
```
data/
└── homo_sapiens/
    ├── reference/
    │   ├── GCF_000001405.40_GRCh38.p14_genomic.gtf
    │   └── GCF_000001405.40_GRCh38.p14_genomic.fna
    ├── tissue/
    │   ├── Brain/Brain.apa_sites.txt
    │   └── Lung/Lung.apa_sites.txt
    └── cell_culture/
        ├── HeLa-S3/HeLa-S3.apa_sites.txt
        └── SH-SY5Y/SH-SY5Y.apa_sites.txt
```

- [ ] **Step 2: Update column format documentation**

Add `transcript_biotype` as the 10th column.

- [ ] **Step 3: Update example IDs**

Replace Ensembl IDs in search examples and API endpoint examples with NCBI/RefSeq IDs.

### Task 20: Verify and test

- [ ] **Step 1: Run lsp_diagnostics on all changed Python files**
- [ ] **Step 2: Run lsp_diagnostics on all changed Vue files**
- [ ] **Step 3: Delete existing database and re-run ETL to test**

```bash
cd backend
rm -f isoapa.db
python -m app.services.etl
```

- [ ] **Step 4: Start backend and verify API responses**
- [ ] **Step 5: Start frontend and verify pages render correctly**
