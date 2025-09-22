# Wikipedia Top Articles Visualizer

A simple, reliable Python script that fetches top-1000 daily pageview statistics from the Wikimedia REST API for English Wikipedia and produces a visual report of the most popular articles over a date range.

The project emphasizes simplicity and robustness: input validation, graceful handling of missing days or network issues, progress reporting, and a multi-facet visualization (one facet per top article).  
At the same time, the visualization routine was carefully refined to produce aesthetic and clear plots, balancing simplicity with visual clarity — this improvement was motivated by a desire for an elegant, interpretable output, rather than unnecessary complexity.
---

## Features

* Fetches daily “top” articles from the Wikimedia Pageviews REST API.
* Selects the top N articles across the requested date range (default 20).
* Produces a multi-facet line plot (`top_articles.png`) with one subplot per article.
* Handles common network errors and missing days gracefully.
* Validates dates and enforces sensible limits to avoid accidental large queries.

---

## Requirements

- **Python:** tested with **Python 3.13.7** (earlier versions ≥3.8 should generally work, but 3.13.7 is recommended for **compatibility and reproducibility**).
- **Dependencies:** installable via `requirements.txt`:

```bash
pandas==2.3.2
matplotlib==3.10.6
seaborn==0.13.2
requests==2.32.5
tqdm==4.67.1
```

Install all dependencies with:

```bash
pip install -r requirements.txt
```



## Quick Usage

Assuming the script file is named `run.py`, run:

```bash
python run.py <START_DATE> <END_DATE>
```

Dates must be provided **without** dashes in `YYYYMMDD` format, for example:

```bash
python run.py 20231210 20231231
```

On success, the script writes a visualization to `top_articles.png` in the current directory and prints progress to the console.

---

## Important Validation Rules

The script enforces several safeguards to keep requests reasonable and avoid hitting API gaps:

* Dates must be in `YYYYMMDD` format.
* Both `start` and `end` must be strictly **before** the current date (no today / no future).
* `end` must be strictly greater than `start`.
* The earliest supported date is `2015-07-01` (Wikimedia pageviews data availability enforced by the script).
* The maximum permitted date range is `365` days (to keep runtime and API usage reasonable).

If any rule is violated, the script prints a clear error message and exits.

---

## Output

* top_articles.png — a multi-facet PNG image. Each subplot shows daily views for one of the top articles chosen by total views over the period.
* The figure title contains a compact summary: the period, mean daily views (human-formatted), the maximum article views observed, and the number of unique articles present.


---

## Notes on Simplicity

This script was intentionally kept **simple and reliable**, following the task requirements.  
Certain features were deliberately **not implemented** to avoid unnecessary complexity, including (to maintain simplicity and reliability):

- **Multiprocessing / multithreading:** requests are made sequentially to keep execution deterministic and easier to debug.
- **Persistent HTTP sessions:** each request is independent to avoid hidden connection state issues.
- **Retry with backoff:** failed requests are skipped rather than retried, keeping the logic simple.
- **Disk caching:** data is fetched fresh for each run to avoid stale or inconsistent results.
- **Complex interpolation of missing data:** missing days are simply absent from the visualization.
- **External configuration files:** configuration is done via simple constants and command-line arguments.

At the same time, the visualization function was carefully enhanced to produce clear, aesthetically pleasing plots with readable axes, facet ordering, and adaptive date formatting. This refinement is a deliberate design choice: it improves interpretability and the user experience without compromising the overall simplicity of the script's logic.

This design prioritizes **clarity, maintainability, and robustness** over raw performance.  
It should work reliably for small to medium date ranges (up to 365 days) without additional setup.

---

## Behavior & Robustness

* Network and API issues are handled gracefully:

  * `404` responses for specific dates are treated as missing data (no crash).
  * Timeout and connection errors print warnings and skip that date.
* The script uses a User-Agent header when calling the Wikimedia API.
* Progress is shown with `tqdm` so you can monitor long runs.
* The plotting routine uses Seaborn `relplot` with facets and automatically formats date ticks to remain readable for various period lengths.

---

## Tips & Troubleshooting

* If the script returns no data for your range, double-check the date format and that the range is within bounds.
* For long ranges near the 365-day limit, expect more API calls and a longer runtime. Consider splitting the range into smaller chunks if needed.
* If you see many network warnings, check your internet connection and try again later — Wikimedia may also occasionally rate-limit or have gaps.
* To reduce chance of timeouts on slow networks, run the script on a machine with a stable connection or increase any timeouts if you modify the code locally.

---

## Customization (notes for developers)

* Default constants are defined near the top of the script:

  * `API_BASE_URL`
  * `PROJECT` (set to `en.wikipedia.org`)
  * `ACCESS_MODE` (`all-access`, `desktop`, `mobile-web`, `mobile-app` are valid options)
  * `TOP_ARTICLES_COUNT` — how many top articles to plot (default: 20)
  * `MAX_DAYS_RANGE` — maximum allowed number of days in the request range (default: 365)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
