# sml-tpcds-snowflake

An AtScale SML repository with a semantic model on the TPC-DS benchmark data in Snowflake: catalog `TPCDS-MM-Snowflake`, model `DemoModel`.

SML (Semantic Modeling Language) is the YAML format in which AtScale stores a semantic model as code. This repository models the TPC-DS retail benchmark at the 10 TB scale. The largest fact table, `store_sales`, has about 28.8 billion rows. The model shows three things in AtScale demos: aggregates that make queries on very large tables fast, reuse of shared objects from an SML package, and one governed model that Power BI, Sigma, and other BI tools query in the same way.

The main readers are AtScale modelers and BI developers who change, deploy, or present this model.

## Technologies

- SML version 1.5 (`catalog.yml`)
- AtScale 2026.9.2
- Snowflake, through the AtScale data warehouse connection named in `connections/Snowflake.yml`
- `sml-cli` 2025.12.0
- SML package `sml-tpcds-common`, pinned to a commit in `package.yml`
- CI/CD: the reusable workflows of `atscale-cicd-pipeline`, slug `tpcds-snowflake`

## Model contents

| Object | Count | Where |
|---|---|---|
| Datasets | 11 | `datasets/`: two facts (`store_sales`, `web_sales`) and nine dimension tables |
| Dimensions, local | 5 | `dimensions/`: Customer Demographics, Fulfilling Warehouse, Promotions, Ship Mode, Store Dimension |
| Dimensions, from the package | 3 | Customer Dimension, Date Dimension (role-played as Sold and Ship), Product Dimension |
| Metrics, local | 14 | `metrics/` |
| Metrics, from the package | 11 | Store and web net paid, net profit, quantity, and row count measures |
| Calculations, local | 5 | `calculations/` (MDX) |
| Calculations, from the package | 4 | Avg Store Unit Net Profit, Customer Count, Total Net Profit, Total Quantity Sold |
| Models | 1 | `models/DemoModel.yml`: 34 metrics and calculations, 14 relationships |
| User-defined aggregates | 1 | `customer sales` in `DemoModel.yml` |

## Set up and validate locally

1. Install Node.js 20 or later.
2. Clone this repository and open its folder.
3. Install the SML package: `npx -y sml-cli@2025.12.0 install .`
   Result: `sml-cli` downloads `sml-tpcds-common` at the commit in `package.yml`.
4. Validate the repository: `npx -y sml-cli@2025.12.0 validate .`
   Result: the output contains `Validation SUCCESSFUL`.

To deploy, the AtScale instance must have a Snowflake data warehouse connection with the name in `as_connection` of `connections/Snowflake.yml`. The database and schema are also in that file.

## Deploy a change

This repository is on the `atscale-cicd-pipeline` with the slug `tpcds-snowflake`. The three stubs in `.github/workflows/` call the pipeline.

1. Create a feature branch and change the SML files.
2. If you want to test on dev, trigger the Airflow DAG `deploy_dev__tpcds-snowflake` with the parameter `branch`.
   Result: the dev instance has the catalog `TPCDS-SF-<branch>`.
3. Open a pull request to `main`.
   Result: the `validate` check runs `sml-cli validate` and the pipeline's cross-reference check.
4. Merge the pull request when the check is green.
   Result: the QA instance has the catalog `TPCDS-MM-Snowflake_main`.
5. Tag the release commit, for example `git tag v1.3`.
6. Push the tag: `git push origin v1.3`.
   Result: the live instance has the new version of `TPCDS-MM-Snowflake_main`.

## Update the shared package

Shared dimensions, metrics, and calculations live in `sml-tpcds-common`. This repository uses one fixed commit of it.

1. Merge the change in `sml-tpcds-common` to `main`.
2. Copy the full commit SHA of that merge.
3. In `package.yml` of this repository, set `version: commit:<sha>`.
4. Run `npx -y sml-cli@2025.12.0 install .`
5. Run `npx -y sml-cli@2025.12.0 validate .`
   Result: the output contains `Validation SUCCESSFUL`.
6. Open a pull request and follow [Deploy a change](#deploy-a-change).

## Reports

- `Reports/Power BI/`: a Power BI project (PBIP) with a live connection to `DemoModel`. `generate_tpcds_overview.py` builds the `TPCDS Overview` report from the `Seed` project. Run it from the `Reports/Power BI` folder: `python3 generate_tpcds_overview.py`. Add `--full` to rebuild the whole project, not only the pages.
- `Reports/sigma-reports/`: Sigma workbook and paginated report, built from code. See [Reports/sigma-reports/README.md](Reports/sigma-reports/README.md).

## Known limits

- `Web Sales` (`m_web_sales_sum`) is `WS_EXT_SALES_PRICE * WS_QUANTITY`. It is about 1000 times larger than the comparable store figure. `Store Sales Price` (`m_store_sales_price`) sums the unit price. Neither is revenue. To compare channels, use `m_ss_net_paid_sum` and `m_ws_net_paid_sum`, or the two Purchased Amount measures.
- `Customer Count` adds two row counts. It is not a distinct count of customers.
- `Web Sales Increase` uses `ParallelPeriod` on the month-of-year attribute. It does not work on the main date hierarchy.
- Net profit is negative in the TPC-DS data.
- Cold queries that read `store_sales` without a matching aggregate take 2.5 to 5 minutes. Run the demo queries once before a presentation.

## License

MIT. See [LICENSE](LICENSE).
