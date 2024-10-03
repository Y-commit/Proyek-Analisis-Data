import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import matplotlib.image as mpimg
import seaborn as sns
import urllib


sns.set(style='dark')


git_main = "https://raw.githubusercontent.com/Y-commit/for-dicoding/dashboard/dasboard/main.csv"
git_geo = "https://raw.githubusercontent.com/Y-commit/for-dicoding/dashboard/dasboard/geo.csv"

data_url = "https://raw.githubusercontent.com/Y-commit/for-dicoding/dashboard/dasboard/main.csv"
data = pd.read_csv(data_url)


st.subheader("Data Preview")
st.write(data.head())


order = data[['order_id', 'customer_id', 'customer_state']]
payment = data[['order_id', 'payment_value']]
customer = data[['customer_id', 'customer_unique_id']]

pay_ord = order.merge(payment, on='order_id', how='outer').merge(customer, on='customer_id', how='outer')


customer_spent = pay_ord.groupby('customer_unique_id')['payment_value'].sum().sort_values(ascending=False)

customer_mean = customer_spent.mean()
customer_std = stats.sem(customer_spent)

confidence_interval = stats.t.interval(0.95, loc=customer_mean, scale=customer_std, df=len(customer_spent) - 1)


customer_regions = pay_ord.groupby('customer_state').agg({'payment_value': [np.mean, np.std], 'customer_unique_id': 'count'})
customer_regions.reset_index(inplace=True)


cis = stats.t.interval(
    0.95,
    loc=customer_regions['payment_value']['mean'],
    scale=customer_regions['payment_value']['std'] / np.sqrt(customer_regions['customer_unique_id']['count']),
    df=customer_regions['customer_unique_id']['count'] - 1
)

customer_regions['ci_low'] = cis[0]
customer_regions['ci_hi'] = cis[1]


class Plotter:
    def __init__(self, data):
        self.data = data

    def default_plot(self, ax, spines):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        ax.get_yaxis().set_tick_params(direction='out')
        ax.get_xaxis().set_tick_params(direction='out')

        for loc, spine in ax.spines.items():
            if loc in spines:
                spine.set_position(('outward', 10))

        if 'left' in spines:
            ax.yaxis.set_ticks_position('left')

        if 'right' in spines:
            ax.yaxis.set_ticks_position('right')

        if 'bottom' in spines:
            ax.xaxis.set_ticks_position('bottom')

        return ax

    def create_plot(self):
        sorted_data = self.data.sort_values(by=('payment_value', 'mean'))
        fig, ax = plt.subplots(figsize=(12, 4))
        ax = self.default_plot(ax, ['left', 'bottom'])
        plt.xticks(rotation=30)
        plt.xlabel('State')
        plt.ylabel('Mean Transaction (95% CI)')
        plt.xlim(-0.5, len(sorted_data) - 0.5)
        plt.ylim(sorted_data['payment_value']['mean'].min() - 10, sorted_data['payment_value']['mean'].max() + 10)

        ax.scatter(sorted_data['customer_state'], sorted_data['payment_value']['mean'], s=100, c=sorted_data['payment_value']['mean'], cmap='viridis')
        ax.vlines(sorted_data['customer_state'], sorted_data['ci_low'], sorted_data['ci_hi'], lw=.5)
        plt.tight_layout()

        return fig


plotter = Plotter(customer_regions)
fig = plotter.create_plot()


st.subheader("Mean Transaction Values with 95% Confidence Intervals by State")
st.pyplot(fig)


class DataAnalyzer:
    def __init__(self, df):
        self.df = df

    def create_daily_orders_df(self):
        daily_orders_df = self.df.resample(rule='D', on='order_approved_at').agg({
            "order_id": "nunique",
            "payment_value": "sum"
        })
        daily_orders_df = daily_orders_df.reset_index()
        daily_orders_df.rename(columns={
            "order_id": "order_count",
            "payment_value": "revenue"
        }, inplace=True)

        return daily_orders_df

    def create_sum_spend_df(self):
        sum_spend_df = self.df.resample(rule='D', on='order_approved_at').agg({
            "payment_value": "sum"
        })
        sum_spend_df = sum_spend_df.reset_index()
        sum_spend_df.rename(columns={
            "payment_value": "total_spend"
        }, inplace=True)

        return sum_spend_df

    def create_sum_order_items_df(self):
        sum_order_items_df = self.df.groupby("product_category_name_english")["product_id"].count().reset_index()
        sum_order_items_df.rename(columns={
            "product_id": "product_count"
        }, inplace=True)
        sum_order_items_df = sum_order_items_df.sort_values(by='product_count', ascending=False)

        return sum_order_items_df

    def review_score_df(self):
        review_scores = self.df['review_score'].value_counts().sort_values(ascending=False)
        most_common_score = review_scores.idxmax()

        return review_scores, most_common_score

    def create_bystate_df(self):
        bystate_df = self.df.groupby(by="customer_state").customer_id.nunique().reset_index()
        bystate_df.rename(columns={
            "customer_id": "customer_count"
        }, inplace=True)
        most_common_state = bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']
        bystate_df = bystate_df.sort_values(by='customer_count', ascending=False)

        return bystate_df, most_common_state

    def create_order_status(self):
        order_status_df = self.df["order_status"].value_counts().sort_values(ascending=False)
        most_common_status = order_status_df.idxmax()

        return order_status_df, most_common_status


class BrazilMapPlotter:
    def __init__(self, data, plt, mpimg, urllib, st):
        self.data = data
        self.plt = plt
        self.mpimg = mpimg
        self.urllib = urllib
        self.st = st

    def plot(self):
        brazil = self.mpimg.imread(self.urllib.request.urlopen('https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'), 'jpg')
        ax = self.data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", figsize=(10, 10), alpha=0.3, s=0.3, color='maroon')
        self.plt.axis('off')
        self.plt.imshow(brazil, extent=[-73.98283055, -33.8, -33.75116944, 5.4])
        self.st.pyplot()


datetime_cols = [
    "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
    "order_purchase_timestamp", "shipping_limit_date"
]
all_df = pd.read_csv(git_main)
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True)


geolocation = pd.read_csv(git_geo)
data = geolocation.drop_duplicates(subset='customer_unique_id')


for col in datetime_cols:
    all_df[col] = pd.to_datetime(all_df[col])


min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()


with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("https://i2.wp.com/genshinbuilds.aipurrjects.com/genshin/characters/ganyu/image.png?strip=all&quality=75&w=256", width=100)
    with col3:
        st.write(' ')
 

    start_date, end_date = st.date_input(
        label="Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )


main_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime(start_date)) & 
                 (all_df["order_approved_at"] <= pd.to_datetime(end_date))]

function = DataAnalyzer(main_df)

daily_orders_df = function.create_daily_orders_df()
sum_spend_df = function.create_sum_spend_df()
sum_order_items_df = function.create_sum_order_items_df()
review_scores, most_common_score = function.review_score_df()
bystate_df, most_common_state = function.create_bystate_df()
order_status_df, most_common_status = function.create_order_status()


st.subheader("Daily Orders and Revenue")
st.line_chart(daily_orders_df.set_index("order_approved_at"))

st.subheader("Total Spend Over Time")
st.line_chart(sum_spend_df.set_index("order_approved_at"))

st.subheader("Product Count by Category")
st.bar_chart(sum_order_items_df.set_index("product_category_name_english")["product_count"])

st.subheader("Review Score Distribution")
st.bar_chart(review_scores)

st.subheader("Customer Count by State")
st.bar_chart(bystate_df.set_index("customer_state")["customer_count"])

st.subheader("Order Status Distribution")
st.bar_chart(order_status_df)


brazil_map_plotter = BrazilMapPlotter(data, plt, mpimg, urllib, st)
brazil_map_plotter.plot()
