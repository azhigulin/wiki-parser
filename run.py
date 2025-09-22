import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import requests
import sys
from datetime import datetime
from tqdm import tqdm

API_BASE_URL = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/top'
API_START_DATE = datetime(2015, 7, 1)
PROJECT = 'en.wikipedia.org'
ACCESS_MODE = 'all-access'  # Allowed: all-access ┃ desktop ┃ mobile-app ┃ mobile-web
TOP_ARTICLES_COUNT = 20
MAX_DAYS_RANGE = 365


def validate_dates(start_str, end_str):
    """Validate date parameters and return error message if any."""
    try:
        start_dt = datetime.strptime(start_str, '%Y%m%d').date()
        end_dt = datetime.strptime(end_str, '%Y%m%d').date()
    except ValueError:
        return 'Error: Invalid date format. Use YYYYMMDD'

    current_date = datetime.now().date()

    if start_dt >= current_date or end_dt >= current_date:
        return f'Error: Dates must be strictly before {current_date} (no today or future dates)'
    if end_dt <= start_dt:
        return 'Error: End date must be > start date'
    if start_dt < API_START_DATE.date():
        return f'Error: Dates must be >= {API_START_DATE.date()}'
    if (end_dt - start_dt).days > MAX_DAYS_RANGE:
        return f'Error: Date range must be <= {MAX_DAYS_RANGE} days'

    return None


def fetch_daily_articles(date):
    """Fetch top articles for a specific date."""
    url = f'{API_BASE_URL}/{PROJECT}/{ACCESS_MODE}/{date:%Y/%m/%d}'
    try:
        response = requests.get(url, headers={'User-Agent': 'wiki_parser'}, timeout=10)

        if response.status_code == 404:
            # No data for a specific date is ok
            return []

        response.raise_for_status()
        data = response.json()
        return data['items'][0]['articles']

    except requests.exceptions.Timeout:
        print(f"Warning: Timeout for date {date}", file=sys.stderr)
        return []
    except requests.exceptions.ConnectionError:
        print(f"Warning: Connection error for date {date}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Unexpected error for date {date}: {e}", file=sys.stderr)
        return []


def process_data(start_date, end_date):
    """Process data by fetching articles and creating DataFrame."""
    dates = pd.date_range(start_date, end_date, freq='D').normalize()
    articles = []

    # Create progress bar for date processing
    for date in tqdm(dates, desc="Fetching data", unit="day"):
        for article in fetch_daily_articles(date):
            article['date'] = date
            articles.append(article)

    if not articles:
        return None, (None, None, None)

    df = pd.DataFrame(articles)
    df['date'] = pd.to_datetime(df['date'])

    metrics = (
        df['views'].max(),
        df.groupby('date')['views'].sum().mean(),
        df['article'].nunique()
    )

    top_articles = df.groupby('article')['views'].sum().nlargest(TOP_ARTICLES_COUNT).index
    df_top = df[df['article'].isin(top_articles)]

    return df_top, metrics


def human_format(num):
    magnitude = 0
    units = ['', 'K', 'M', 'B', 'T']
    while abs(num) >= 1000 and magnitude < len(units)-1:
        magnitude += 1
        num /= 1000.0
    return f'{num:.2f}{units[magnitude]}'


def create_visualization(df_top, metrics):
    """Create and save visualization of top articles using relplot."""
    min_date = df_top['date'].min()
    max_date = df_top['date'].max()
    period_str = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
    max_views, mean_views, unique_articles = metrics

    # Sort by the maximum value precisely (not total sum), to make graphs on the x scale ordered
    article_views = df_top.groupby('article')['views'].max().sort_values(ascending=False)
    sorted_articles = article_views.index.tolist()
    n_articles = len(sorted_articles)
    n_cols = min(5, n_articles)  # Maximum 5 columns

    # Create the relplot with custom size and sorted articles
    # (markers are included because some articles have only a single data point)
    g = sns.relplot(
        data=df_top, kind="line", x='date', y='views', hue='article', style="article", col="article",
        col_order=sorted_articles, col_wrap=n_cols, height=3, aspect=1.2, linewidth=2.5, legend=False,
        markers=True, markersize=5, estimator=None, facet_kws={'sharey': False, 'sharex': True})

    # Set Y-axis to start from 0 for all subplots
    for ax in g.axes.flat:
        ax.set_ylim(bottom=0)
        # Get current y limits and set nice upper limit
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(0, y_max * 1.05)  # Add 5% padding at top

    # Set main title
    g.fig.suptitle(
        f'Top Wikipedia Articles ({period_str})\n'
        f'Mean Daily Views: {human_format(mean_views)} | '
        f'Max Article Views: {human_format(max_views)} | '
        f'Unique Articles: {unique_articles}',
        fontsize=12, y=0.98)

    # Set common Y-axis label
    g.set_ylabels('Views', fontsize=12)

    # Format x-axis for all subplots with improved date formatting
    n_days = (max_date - min_date).days + 1

    if n_days <= 7:
        date_format = '%m/%d'
        interval = 1
        locator = mdates.DayLocator(interval=interval)
    elif n_days <= 30:
        date_format = '%m/%d'
        interval = 5
        locator = mdates.DayLocator(interval=interval)
    elif n_days <= 90:
        date_format = '%b %d'
        interval = 14
        locator = mdates.DayLocator(interval=interval)
    else:
        date_format = '%b %Y'
        interval = max(1, n_days // 30 // 4)
        locator = mdates.MonthLocator(interval=interval)

    # Apply formatting to all subplots
    for ax in g.axes.flat:
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)  # Reduced font size

    # Adjust layout with more space for titles and labels
    g.fig.tight_layout()
    g.fig.subplots_adjust(top=0.92)  # Make room for suptitle

    # Save with higher DPI for better quality
    g.fig.savefig('top_articles.png', dpi=200, bbox_inches='tight')
    plt.close(g.fig)
    print('Visualization saved to top_articles.png')


def main():
    parser = argparse.ArgumentParser(description='Analyze Wikipedia top articles')
    parser.add_argument('start', help='Start date in YYYYMMDD format')
    parser.add_argument('end', help='End date in YYYYMMDD format')
    args = parser.parse_args()

    if error_msg := validate_dates(args.start, args.end):
        print(error_msg)
        return

    df_top, metrics = process_data(args.start, args.end)

    if df_top is None:
        print('No data found for the specified date range')
        return

    create_visualization(df_top, metrics)


if __name__ == '__main__':
    main()
