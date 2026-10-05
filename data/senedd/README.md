# Senedd Record of Proceedings: committee transcripts

Transcripts of Welsh Parliament (Senedd Cymru) committee meetings from the official Record of Proceedings, collated into a single CSV of spoken contributions. This is natural, topical speech with a free ground-truth label: which committee was talking. That makes it a good partner to the MoneyData transactions.

## At a glance

| | |
|---|---|
| File | `senedd.csv` |
| Rows | 3265 |
| Meetings | 30 |
| Committees | 12 |
| Date range | 2026-06-30 to 2026-10-01 |
| Language | English. Contributions spoken in Welsh appear as the English interpretation |
| Built by | `fetch.py` in this folder |

Rows per committee:
|||
|---|---|
| Rows | Committee |
| 595 | Health And Social Care Committee |
| 417 | Culture Communications Cymraeg And Sport Committee |
| 332 | Climate Change Environment Sustainability And Rural Affairs Committee |
| 329 | Public Accounts And Public Administration Committee |
| 315 | Finance Committee |
| 225 | Legislation Committee |
| 188 | Early Years Children Young People And Education Committee |
| 183 | Equality Human Rights And Social Justice Committee |
| 179 | Constitution Justice And External Affairs Committee |
| 178 | Local Government Housing And Planning Committee |
| 165 | Petitions Committee |
| 159 | Economy Energy And Connectivity Committee |

## Columns

| Column | Example | Notes |
|---|---|---|
| meeting_id | 16251 | Record of Proceedings meeting ID |
| date | 2026-09-17 | Meeting date |
| committee | Health And Social Care Committee | Derived from the XML element name. Our ground-truth label |
| agenda_item | 2. General scrutiny session with ... | The agenda item the contribution belongs to. A finer-grained label |
| contribution_id | 769884 | ID of the original contribution |
| contribution_order | 6 | Position within the meeting |
| speaker | (member's name) | As recorded. Kept for context, never embedded |
| spoken_in | En | `En` = spoken in English. `Cy` = spoken in Welsh, and the text is the interpretation |
| chunk | 0 | Long contributions are split into overlapping windows. 0 is the first |
| word_count | 142 | Words in this row's text |
| text | ... | Cleaned contribution text with the HTML stripped |

## How it was made

```
python data/senedd/fetch.py --max-meetings 30 --per-committee 3
```

The script:

1. Works backwards through Record of Proceedings meeting IDs and downloads the English transcript XML for each, one request per second. The XML is cached in `raw/`, which is not committed.
2. Skips IDs that aren't transcripts, Plenary sessions (unless `--include-plenary` is set), and committees that already have `--per-committee` meetings, so no single committee dominates.
3. Keeps spoken contributions only, dropping procedural notes and one-liners under 20 words ("Diolch.", "Yes, fine.").
4. Strips the HTML and splits contributions longer than 150 words into overlapping 150-word windows with a 30-word overlap. This keeps every row under the embedding model's limit of roughly 256 tokens.

Please don't re-run the scrape on the night, because the committed CSV is the point. If you extend it, keep the pause between requests.

## Things to know

- **Recent transcripts are drafts.** The Record marks them as draft versions, so wording may change slightly once finalised.
- **Welsh contributions are interpretations.** When `spoken_in` is `Cy`, the English text is a transcription of the simultaneous interpretation, not the speaker's own words.
- **Chunks share context.** Rows with the same `contribution_id` are windows of one contribution and overlap by 30 words. Group or deduplicate on `contribution_id` if that matters for your analysis.
- **Committee names are reconstructed.** They come from the XML element names, split on capital letters, so you get "Health And Social Care Committee".
- **Plenary is excluded by default.** A single Plenary session covers many unrelated topics, so it has no meaningful single label, and the transcripts are very long.
- **This is the public record, but it still contains people.** Witnesses and members of the public may be named or quoted. Keep analysis on topics rather than individuals, and keep it non-partisan.

## Quick look

```python
import pandas as pd

df = pd.read_csv("data/senedd/senedd.csv")
print(df.shape)
print(df["committee"].value_counts())
print(df["spoken_in"].value_counts())
print(df.groupby("committee")["meeting_id"].nunique())
```

## Using it with the workshop notebooks

In the CSV notebook:

```python
CSV_PATH = "../data/senedd/senedd.csv"
FIELDS = ["text"]
LABEL_FIELD = "committee"
FILTER = None
DEDUPE = False
OUTPUT_DIR = "../outputs/senedd"
```

Then open `03_explore.ipynb` with `DATASET_DIR = "../outputs/senedd"`, and set `N_CLUSTERS` to roughly the number of committees.

## Suggested tasks

### Starter

1. **Semantic search.** Try "hospital waiting lists", "bus services in rural areas", "school funding" and "flooding". Do the results come from the committees you'd expect?
2. **Rediscover the committees.** Set `N_CLUSTERS` to the number of committees and check the adjusted Rand index and the crosstab. Which committees overlap, and why?
3. **Topic labels.** Read the TF-IDF words for each cluster. Do they name the topic, or just the procedure ("chair", "minister", "thank")?

### Intermediate

4. **Procedure vs substance.** Much of a meeting is chairing and turn-taking. Can you find a "procedural" cluster? Re-run the script with a higher `--min-words` and see whether the clusters become more topical.
5. **Questions and answers.** A member's question and the minister's answer sit next to each other in `contribution_order`. Are they also neighbours in embedding space? How often is a question's nearest neighbour its own answer?
6. **Agenda items as finer labels.** Within one committee, use `agenda_item` as the `LABEL_FIELD`. Can embeddings separate sessions on different subjects?
7. **Chunk size.** Re-run with `--chunk-words 80`, then with `--chunk-words 0` (whole contributions, silently truncated by the model). How do the search results and clusters change?

### Stretch

8. **Interpretation vs original.** Compare `spoken_in = Cy` rows with `En` rows. Can a simple classifier on the embeddings tell them apart? If so, what is it picking up?
9. **Cross-lingual search.** Download the Bilingual transcripts for the same meetings (`xmlDownloadType=BilingualTranscript`) and pair the Welsh and English versions of each contribution where both exist. Then test a multilingual model: does an English query find the Welsh original?
10. **Change over time.** If your snapshot spans several months, does the centre of each committee's embeddings drift as its agenda changes?

### Discussion prompts

- What's lost when a 150-word window cuts through the middle of an argument?
- Is "which committee said this?" a question about topic or about style?
- When the text is an interpretation, whose words are we embedding?

## Source and licence

Source: Welsh Parliament (Senedd Cymru), Record of Proceedings XML export, https://record.senedd.wales/XMLExport

Contains public sector information licensed under the Open Government Licence v3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/

This CSV is a derived dataset. Contributions were filtered, cleaned of HTML and split into chunks as described above.
