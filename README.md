# Med-info-bot

A project to organize information about prescription and over the counter medications.

## Status

As of **2024-12-16** this is an early work in progress. This project includes a database of 1441 prescription and OTC medications with links to Wikipedia, the FDA's NDC products table, and DrugBank. The intention is to create a reference for medications, drug classes, and conditions treated.

Retrieval augmented generation over Wikipedia pages is implemented as a proof-of-concept. So far, retrieval is hurting more than helping. Similarity search over sections of Wikipedia pages often returns irrelevant information which then gets incorporated into the generation.

## Data sources

- [ClinCalc DrugStats Top 300][1]
- The U.S. Food and Drug Administration's [Drugs@FDA Data Files][7]
- [Pharmac Hospital Medications List][2] from New Zealand's pharmaceutical management agency.
- [New Zealand Formulary][4]
- [My Medicines NZ][5]
- Wikipedia
- [DrugBank][3]
- [MSD Manuals][6] - aka The Merck Manual


## Inspiration sources

- [RxReasoner][8]


[1]: https://clincalc.com/DrugStats/Top300Drugs.aspx
[2]: https://schedule.pharmac.govt.nz/pub/HML/archive/
[3]: https://go.drugbank.com/
[4]: https://nzformulary.org/
[5]: https://www.mymedicines.nz/
[6]: https://www.msdmanuals.com/
[7]: https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files
[8]: https://www.rxreasoner.com/
