# Finance RAG — Quarterly Results Q&A (Infosys)

A Retrieval-Augmented-Generation app that lets an analyst ask plain-English
questions about a company's quarterly results PDFs and get an answer with
the exact source page cited.

## Company & data

**Company:** Infosys Ltd. (NSE, BSE, NYSE: INFY)

Four consecutive quarters, IFRS USD press releases, downloaded from Infosys'
Investor Relations site:

| Quarter | Period ended | Source |
|---|---|---|
| Q2 FY25-26 | 30 Sep 2025 | https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q2/documents/ifrs-usd-press-release.pdf |
| Q3 FY25-26 | 31 Dec 2025 | https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q3/documents/ifrs-usd-press-release.pdf |
| Q4 FY25-26 | 31 Mar 2026 | https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q4/documents/ifrs-usd-press-release.pdf |
| Q1 FY26-27 | 30 Jun 2026 | https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q1/documents/ifrs-usd-press-release.pdf |

Saved locally as `data/Q1 FY26-27.pdf`, `data/Q2 FY25-26.pdf`,
`data/Q3 FY25-26.pdf`, `data/Q4 FY25-26.pdf`.

## Setup

```bash
git clone https://github.com/YOUR-USERNAME/finance-rag.git
cd finance-rag
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env            # then edit .env and paste your OPENAI_API_KEY
```

## Run

```bash
streamlit run app.py
```

Open the local URL Streamlit prints, upload the 4 PDFs from `data/`, click
**Index uploaded files**, then ask questions.

## Design choices

- **Chunk size 1100 / overlap 150 characters** — large enough to usually
  keep a full financial highlights table in one chunk, small enough to stay
  focused for retrieval. Within the assignment's recommended 800–1200 /
  100–200 range.
- **Per-file retrieval (`retrieve_across_files`)** — instead of one global
  top-k similarity search, the app queries each indexed file separately
  (3 chunks per file) for every question. This was a deliberate fix after
  testing showed plain global top-k search could let one file's chunks
  dominate the results, starving out other quarters on comparison
  questions. Explicit per-file querying guarantees every quarter gets a
  chance to contribute.
- **Chroma persisted to `chroma_db/`** — survives app restarts. Re-indexing
  a file first deletes its old chunks before re-adding, so re-indexing
  doesn't create duplicates.

## Test questions & answers

| # | Question | App's answer |
|---|---|---|
| 1 | What was total revenue in the most recent quarter you loaded? | The total revenue in the most recent quarter, which is Q1 FY26-27, was $5,082 million (source: Q1 FY26-27.pdf, page 1). |
| 2 | Compare net profit across all the quarters you loaded. Which was highest? | The highest net profit (after non-controlling interests) across all the quarters provided was in Q4 FY25-26, with a net profit of $919 million (source: Q4 FY25-26.pdf, page 7). |
| 3 | How did revenue in the latest quarter compare with the same quarter of the previous year? | In the latest quarter ended June 30, 2026, reported revenues were $5,082 million, a growth of 2.8% compared to the same quarter of the previous year, where revenues were $4,941 million (source: Q1 FY26-27.pdf, page 7). |
| 4 | What did management say about the demand outlook or business environment? | Management expressed a positive outlook on the business environment, emphasizing commitment to accelerating investments in AI, talent, and platforms to drive future growth, with a focus on productivity, operating leverage, and financial flexibility (source: Q1 FY26-27.pdf, page 1). |
| 5 | Which business segment or geography grew fastest, and by how much? | The information is not available in the uploaded documents. (These press releases report consolidated figures only, without a segment/geography breakdown table.) |
| 6 | What was the operating margin in each quarter, and is the trend rising or falling? | Q2 FY25-26: 21.0% · Q3 FY25-26: 18.4% reported (21.2% adjusted) · Q4 FY25-26: 20.9% · Q1 FY26-27: 21.1%. Trend is relatively stable with minor fluctuations, dipping in Q3 (one-off Labour Codes adjustment) then recovering. |
| 7 | Was any dividend declared? State the amount per share and the record date. | The Board proposed a final dividend of ₹25 per share for FY26. The record date was not specified in the provided documents (source: Q4 FY25-26.pdf, page 2). |
| 8 | What risks, headwinds, or challenges are mentioned in the documents? | Business strategy execution risk, competition for talent, wage inflation/reskilling costs, hybrid work model challenges, economic/geopolitical uncertainty, AI-driven disruption, evolving regulation, cybersecurity, pending litigation/US govt investigation, tariffs, and US H-1B visa program changes — each cited across all 4 quarters. |
| 9 | Give me a three-line summary of the latest quarter for a client email. | In Q1 FY26-27, Infosys reported revenues of $5,082 million, marking 2.8% YoY growth and 0.8% QoQ growth. The company achieved a resilient operating margin of 21.1% and generated free cash flow of $955 million. Large deal wins totaled $3.6 billion, with 61% net new business (source: Q1 FY26-27.pdf, page 1). |
| 10 | (Trap) What is Infosys's stock price today? | The information is not available in the uploaded documents. Correctly refused. |

## Hand-verified numbers

Cross-checked directly against the PDFs (not just trusted from the app):
- Q1 FY26-27 revenue: $5,082 million ✅ (page 1)
- Q4 FY25-26 net profit: $919 million ✅ (page 7)
- Q3 FY25-26 net profit: $747/748 million ✅ (page 7)

## What didn't work well (and how it was fixed)

- **Metadata bug:** early in ingestion, `load_pdf_pages` had hardcoded a
  literal filename instead of using its `file_path` parameter, so every
  chunk in the database got labeled with the same file regardless of which
  PDF it actually came from. Found by noticing a comparison question only
  ever cited one file, then confirming with a debug script that checked
  distinct filenames in the stored metadata.
- **Retrieval imbalance:** even after fixing metadata, global top-k
  similarity search sometimes pulled several near-duplicate chunks from one
  file (e.g. multiple mentions of "net profit" in Q1) and never reached the
  other 3 files, causing false refusals on comparison questions. Fixed by
  switching to per-file querying (`retrieve_across_files`).
- **Overly strict refusals:** with the initial system prompt, GPT-4o
  refused to answer qualitative questions (e.g. "what did management say
  about demand outlook") even when the relevant CFO/CEO quote was present
  in the retrieved context, apparently treating any synthesis as "guessing."
  Fixed by explicitly permitting summarization/paraphrasing of the given
  context in the system prompt, while still banning invented numbers.
- **Segment/geography question (#5):** the app correctly refuses this, since
  these particular press releases report only consolidated (whole-company)
  figures, with no segment or geography breakdown table.

## Screenshots

_(add screenshots here: upload+index confirmation, an answered question
with sources, the trap question refusal, and the persistence proof —
app restarted with no re-upload, still answering correctly)_