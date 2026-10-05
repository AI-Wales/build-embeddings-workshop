# MoneyData: anonymised UK bank transactions (2015-2022)

Seven years of real, anonymised transactions from a single UK current account, published by Firat, Vytla, Vasudeva Singh, Jiang and Laramee for research on financial data visualisation. We use it in the embeddings workshop because it has exactly what synthetic data lacks: genuinely messy, truncated, inconsistent merchant strings, plus a category label we can hold out as ground truth.

With thanks to Robert S. Laramee and co-authors for making this data openly available.

## At a glance

| | |
|---|---|
| Rows | 6,567 transactions |
| Period | 27 July 2015 to 25 July 2022 |
| Accounts | One UK current account |
| Currency | GBP (foreign purchases are converted, with separate fee rows) |
| Columns | 10 |
| Transaction types | 13 bank codes, plus blank for interest |
| Categories | Around 25 main values, plus a few one-offs |
| File | `moneydata.csv` |

## Sample rows

```
Transaction Number,Transaction Date,Transaction Type,Transaction Description,Debit Amount,Credit Amount,Balance,Category,Location City,Location Country
1,25/07/2022,BP,SAVE THE CHANGE,3.11,,541.43,Savings,Nottingham,UK
2,25/07/2022,DEB,LIDL GB  NOTTINGHA,15.02,,544.54,Groceries,Nottingham,UK
10,22/07/2022,DEB,Amazon.co.uk*VK6IN,13.51,,659.79,Amazon,Nottingham,UK
22,18/07/2022,DD,VIRGIN MEDIA PYMTS,56.25,,755.3,Bills,Nottingham,UK
25,18/07/2022,CPT,LNK COOPERATIVE PL,40,,831.9,Cash,Plymouth,UK
109,21/06/2022,DEB,ROMA TERMINI SELF,2.32,,777.24,Travel,Roma,Italy
```

## Columns

| Column | Example | Notes |
|---|---|---|
| Transaction Number | 2 | Row identifier. 1 is the most recent transaction |
| Transaction Date | 25/07/2022 | DD/MM/YYYY. Parse with `dayfirst=True` |
| Transaction Type | DEB | Bank-assigned code, see below |
| Transaction Description | LIDL GB  NOTTINGHA | Merchant or payee. Usually truncated by the bank at 18 characters |
| Debit Amount | 15.02 | Money out, GBP. Blank for credits |
| Credit Amount | | Money in, GBP. Blank for debits |
| Balance | 544.54 | Running balance after the transaction |
| Category | Groceries | Spending category supplied with the dataset. Our ground truth |
| Location City | Nottingham | Often the account holder's base rather than the merchant's location |
| Location Country | UK | Occasionally blank or inconsistent |

## Transaction types

These are standard UK bank codes. The meanings are our reading of them, not part of the published data description.

| Code | Meaning | What you'll find |
|---|---|---|
| DEB | Debit card payment | Shops, cafes, online retailers. The richest merchant text |
| DD | Direct debit | Bills, mortgage, insurance, utilities |
| SO | Standing order | Regular transfers, including to savings |
| BP | Bill payment | Mostly SAVE THE CHANGE round-ups |
| CPT | Cash withdrawal | "LNK ..." is the LINK cash machine network |
| FPO | Faster payment out | Includes person-to-person transfers |
| FPI | Faster payment in | Includes person-to-person transfers |
| BGC | Bank giro credit | Incoming payments, such as salary |
| TFR | Transfer | Between accounts |
| DEP | Deposit | Includes monthly fee waivers |
| PAY | Payment | Monthly account fee |
| FEE | Account fee | |
| CHQ | Cheque | |
| (blank) | Interest | INTEREST (GROSS) or INTEREST (NET) |

## Quick look

```python
import pandas as pd

df = pd.read_csv("data/moneydata/moneydata.csv")
df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], dayfirst=True)
df["Amount"] = df["Credit Amount"].fillna(0) - df["Debit Amount"].fillna(0)

print(df.shape)
print(df["Transaction Type"].value_counts())
print(df["Category"].str.strip().value_counts())
print(df["Transaction Description"].nunique(), "unique descriptions")
```

## Things worth noticing

- **The same merchant under many names.** Amazon alone appears as `AMZNMktplace`, `Amazon UK Marketpl`, `AMAZON SVCS EU-UK`, `AMZN Mktp US*1363Y`, `AMAZON EU AMAZON.C`, `Amazon Prime*2X250` and many more. Sainsbury's appears as `SAINSBURYS S/MKTS`, `SAINSBURY'S S/MKT`, `SAINSBURY S S/MKTS` and others. Keyword search struggles badly here.
- **Truncation.** Descriptions are cut at 18 characters, so `ARRIVA TRAINS WALE` and `ORIENTAL MART HYDR` are the norm, not the exception.
- **Lexical traps.** `UBER   *TRIP` is Travel, but `UBER   *EATS` is Dine Out. Same word, different meaning.
- **Things no model can know.** `JS ONLINE GROCERY` is almost certainly Sainsbury's online shop. A general-purpose model has no way to know that, and that's an honest limit of embeddings.
- **Welsh content.** `DWR CYMRU W WATER` (Welsh Water), `TFW RAIL SERVICES` (Transport for Wales), `ARRIVA TRAINS WALE` and plenty of Welsh cafes and restaurants.
- **Terminology drift.** Foreign-transaction fees are labelled `NON-STG PURCH FEE` and `NON-STG TRANS FEE` until late 2018, then `NON-GBP ...` afterwards.
- **One dominant string.** `SAVE THE CHANGE` round-ups are among the most frequent rows. They will dominate plots and slow down graph methods unless you deduplicate.

## Known data quality issues

- **Whitespace and case.** Values such as `Groceries ` vs `Groceries`, and `nottingham` vs `Nottingham `. Strip and normalise before grouping.
- **Typos and oddities in locations.** Examples include `Sheffild`, `Mansfiled`, `Huston` and `Plymouth/Newcatle`, at least one city/country mismatch, and some blank countries.
- **Encoding damage.** At least one accented character has been lost (`Almer?a`).
- **Split amounts.** Debit and credit are separate columns. Combine them into one signed amount for most analysis.
- **Location is not merchant location.** Online retailers, for example, are tagged with the account holder's base.
- **Label noise.** A small number of categories are clearly wrong. Finding them is one of the suggested tasks below, and the answers are in the spoiler section at the end.

## Privacy and ethics

This is one real person's anonymised current account. The anonymisation handles the obvious identifiers, but seven years of transactions still carry a lot of context.

- Please don't try to re-identify the account holder, and don't publish analyses aimed at doing so.
- The default workshop configuration keeps only card payments (DEB) and direct debits (DD). That excludes salary credits and most person-to-person transfers.
- It is still a good discussion prompt: what does "anonymised" actually guarantee?

## Using it with the workshop notebooks

In `02_embed_bank_csv.ipynb`:

```python
CSV_PATH = "../data/moneydata/moneydata.csv"
FIELDS = ["Transaction Description"]           # what gets embedded
LABEL_FIELD = "Category"                       # held out - never embed the answer
FILTER = ("Transaction Type", {"DEB", "DD"})   # card payments + direct debits
DEDUPE = True                                  # embed each unique description once
OUTPUT_DIR = "../outputs/moneydata"
```

Then open `03_explore.ipynb` with `DATASET_DIR = "../outputs/moneydata"`.

Never put `Category` in `FIELDS`. If the label is embedded, the clusters will "rediscover" it trivially and the evaluation means nothing.

## Suggested tasks

### Starter (config changes only)

1. **Keyword vs meaning.** Search for "coffee", "train travel", "takeaway food" and "online shopping". Compare the results with a plain `df["Transaction Description"].str.contains("coffee", case=False)`.
2. **Rediscover the categories.** Set `N_CLUSTERS` to around 20 and look at the adjusted Rand index and the crosstab. Which categories come out cleanly, and which don't? Why might "Others" or "Services" be hard?
3. **PCA vs t-SNE.** Compare the two projections side by side, then change `PERPLEXITY` (try 5, 15 and 50). Which structure is real, and which is an artefact of the method?

### Intermediate

4. **One merchant, many names.** Do the Amazon variants land in one cluster or several? Write a small normaliser that strips order references such as `*VK6IN`, then re-run. Does cleaning help or hurt? (Good first PR.)
5. **Lexical traps.** Where do `UBER   *EATS` and `UBER   *TRIP` land? Does the model follow the shared word or the meaning?
6. **Limits of knowledge.** Where does `JS ONLINE GROCERY` land relative to the Sainsbury's variants? What would it take to fix this?
7. **Wales vs England.** Is `DWR CYMRU W WATER` near `SEVERN TRENT WATER`? Is `TFW RAIL SERVICES` near `EAST MIDS RAILWAY` and `GWR WEBSALES`?
8. **Terminology drift.** Do `NON-STG` and `NON-GBP` fee rows end up together? How would you detect renamed descriptions automatically?
9. **Threshold sweep.** Vary `SIMILARITY_THRESHOLD` in the community detection cell. How do the number and size of communities change?

### Stretch

10. **Find the mislabelled rows.** Set `DEDUPE = False`. For each row, take the majority category among its nearest neighbours and flag rows where it disagrees with the row's own label. Read the flagged rows: which are real errors and which are legitimate exceptions?
11. **From embeddings to insight.** Assign every transaction to its discovered cluster, then chart monthly spend per cluster with pandas. Does it tell the same story as the provided categories?
12. **Swap the model.** Try `all-mpnet-base-v2` or a multilingual model. Does the adjusted Rand index improve? How much slower is it on your laptop? (Good first PR.)
13. **Bring your own data (locally only).** Export your own bank CSV and run the same notebooks on it. Monzo exports include a `Category` column, so you can compare against Monzo's own categorisation. Never commit your own data.

### Discussion prompts

- Amounts don't embed meaningfully as text. How would you combine the description embedding with numeric features such as amount or day of week?
- Who decides what a category means? Is a mobile phone bill really "Other Shopping"?
- What does "anonymised" guarantee, and what doesn't it?

## Citation

If you use this dataset, please cite the paper and the dataset:

> Firat, E. E., Vytla, D., Vasudeva Singh, N., Jiang, Z. and Laramee, R. S. (2023). MoneyVis: Open Bank Transaction Data for Visualization and Beyond. *EuroVis 2023 - Short Papers*, pp. 109-113. The Eurographics Association. https://doi.org/10.2312/evs.20231052

> Laramee, R. (2026). Bank Transactions Dataset. Mendeley Data, V1. https://doi.org/10.17632/dnxtg6n4rv.1

```bibtex
@inproceedings{firat2023moneyvis,
  author    = {Firat, Elif E. and Vytla, Dharmateja and Vasudeva Singh, Navya and Jiang, Zhuoqun and Laramee, Robert S.},
  title     = {MoneyVis: Open Bank Transaction Data for Visualization and Beyond},
  booktitle = {EuroVis 2023 - Short Papers},
  publisher = {The Eurographics Association},
  pages     = {109--113},
  year      = {2023},
  doi       = {10.2312/evs.20231052}
}

@misc{laramee2026bankdata,
  author       = {Laramee, Robert},
  title        = {Bank Transactions Dataset},
  howpublished = {Mendeley Data, V1},
  year         = {2026},
  doi          = {10.17632/dnxtg6n4rv.1}
}
```

**Licence:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The copy in this folder is unmodified from the version published on Mendeley Data.

<details>
<summary>Facilitator notes: known labelling errors (spoilers for task 10)</summary>

Row references are Transaction Numbers.

- **A recurring swap around the monthly `CLUB LLOYDS WAIVED` deposits.** The WAIVED row and the transaction two rows below it exchange categories. Examples:
  - 156 and 158: `AMZNMktplace` tagged Supplementary Income.
  - 3780 and 3782: `Brontosaurus Vegan` tagged Supplementary Income.
  - 4156 and 4158: `INTEREST (GROSS)` tagged Supplementary Income.
- **Other swaps:**
  - 1330 and 1342: `TRADING212UK` tagged Bills, `VIRGIN MEDIA PYMTS` tagged Investment.
  - 1535 and 1537: `TRADING212UK` tagged Savings, `SAVE THE CHANGE` tagged Investment.
- **One-offs:** 5499, `Amazon *Mktplce EU` tagged Cash.
- **Not errors:** refunds on card transactions are legitimately tagged Supplementary Income. The giveaway for a real error is a *debit* amount with an income category.
- **Debatable rather than wrong:** O2, a mobile phone bill, tagged Other Shopping.

With the default DEB/DD filter, rows such as 158, 1342, 3782 and 5499 are still in play.

</details>
