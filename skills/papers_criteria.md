
## Journal Ranking and Quartile Verification

### Objective

Identify and verify journal quartiles for papers retrieved
from any academic literature source or research database.

### Approved ranking sources

Use the ranking source specified by the user.

1. Clarivate Journal Citation Reports (JCR)
   - Official website: https://jcr.clarivate.com/
   - Record the Journal Impact Factor (JIF) quartile or
     Journal Citation Indicator (JCI) quartile, as specified.

2. Scopus Sources
   - Official website: https://www.scopus.com/sources
   - Record the CiteScore quartile and corresponding
     subject category.

3. SCImago Journal & Country Rank (SJR)
   - Official website: https://www.scimagojr.com/
   - Record the SJR quartile and corresponding
     subject category.

Do not treat quartiles from these sources as equivalent.
Do not combine them into a single quartile value.

### Verification requirements

For each journal, record:

- Journal title
- ISSN or eISSN, when available
- Ranking source
- Ranking metric
- Subject category
- Quartile (Q1, Q2, Q3, or Q4)
- Ranking year
- Verification date
- Official journal-ranking URL
- Verification status

Use the journal's ISSN whenever possible to distinguish
journals with similar names.

### Ranking year

When available, use the ranking year corresponding to
the paper's publication year.

If the requested historical ranking is unavailable,
record the latest available ranking separately. Never
present a current ranking as the historical ranking for
an older paper.

If the ranking for a recent publication year has not
yet been released, mark it as unavailable and state
which alternative year, if any, was checked.

### Verification status

Use one of these statuses:

- Verified: confirmed against the selected ranking source.
- Partially verified: journal identified, but one or more
  ranking details remain unconfirmed.
- Unverified: no authoritative ranking record confirmed.
- Not indexed: confirmed absent from the specified source,
  after checking the correct journal identity.
- Not applicable: the publication is not a journal article
  or the ranking criterion does not apply.

Do not use "Not indexed" when a search simply fails.
Do not infer a quartile from impact factor, citations,
publisher reputation, or journal title.

### Multiple subject categories

If a journal has different quartiles across categories,
record each relevant category and its quartile.

Do not automatically select the highest quartile.
If the user specifies a research field, prioritize the
most relevant category and explain the selection.

### Paper selection

When the user requests Q1-only papers:

1. Retrieve relevant literature first.
2. Identify the journal and verify its identity.
3. Verify the requested ranking source, metric, category,
   and year.
4. Retain only papers meeting the specified Q1 criterion.
5. Keep unverified papers separate from verified Q1 papers.
6. If fewer than the requested number qualify, return
   fewer papers rather than relaxing the criterion silently.

### Reporting

Every reported quartile must be traceable to its source.

Use this format:

Journal: [journal title]
ISSN: [ISSN]
Source: [JCR / Scopus Sources / SCImago]
Metric: [JIF / JCI / CiteScore / SJR]
Category: [subject category]
Quartile: [Q1 / Q2 / Q3 / Q4]
Ranking year: [year]
Verified on: [date]
Source URL: [official ranking record]
Status: [verification status]

Journal quartile is a journal-level indicator and must not
be presented as proof of the quality of an individual paper.
Assess the paper's methods, data, validation, and findings
independently.
