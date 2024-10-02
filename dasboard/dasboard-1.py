import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import streamlit as st
import urllib

# Set seaborn style
sns.set(style='dark')

# Set github file csv
# split data for better management
git_main ="https://raw.githubusercontent.com/Y-commit/for-dicoding/dashboard/dasboard/main.csv"
git_geo  ="https://raw.githubusercontent.com/Y-commit/for-dicoding/dashboard/dasboard/geo.csv"


# Define the DataAnalyzer class
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

# Define the BrazilMapPlotter class for map plotting functionality
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

# Load datasets
datetime_cols = [
    "order_approved_at", "order_delivered_carrier_date", 
    "order_delivered_customer_date", "order_estimated_delivery_date", 
    "order_purchase_timestamp", "shipping_limit_date"
]
all_df = pd.read_csv(git_main)
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True)

# Geolocation Dataset
geolocation = pd.read_csv(git_geo)
data = geolocation.drop_duplicates(subset='customer_unique_id')

# Convert date columns to datetime
for col in datetime_cols:
    all_df[col] = pd.to_datetime(all_df[col])

# Get date range for filtering
min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()

# Sidebar for selecting date range
with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(' ')
    with col2:
        st.image("https://i2.wp.com/genshinbuilds.aipurrjects.com/genshin/characters/ganyu/image.png?strip=all&quality=75&w=256", width=100)
    with col3:
        st.write(' ')

    # Date Range
    start_date, end_date = st.date_input(
        label="Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

# Filter data by selected date range
main_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime(start_date)) & 
                 (all_df["order_approved_at"] <= pd.to_datetime(end_date))]

# Instantiate DataAnalyzer class and call its methods
function = DataAnalyzer(main_df)

daily_orders_df = function.create_daily_orders_df()
sum_spend_df = function.create_sum_spend_df()
sum_order_items_df = function.create_sum_order_items_df()
review_score, common_score = function.review_score_df()
state, most_common_state = function.create_bystate_df()
order_status, common_status = function.create_order_status()

# Instantiate BrazilMapPlotter for map plotting
map_plot = BrazilMapPlotter(data, plt, mpimg, urllib, st)

# Define Streamlit app UI
st.title("DICODING E-Commerce Public Data Analysis")
st.write("for ecomerce public data")

# Plot daily orders delivered
st.subheader("Order Daily Delivered")
col1, col2 = st.columns(2)

with col1:
    total_order = daily_orders_df["order_count"].sum()
    st.markdown(f"Order in total: **{total_order}**")

with col2:
    total_revenue = daily_orders_df["revenue"].sum()
    st.markdown(f"Revenue in total: **{total_revenue}**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(x=daily_orders_df["order_approved_at"], y=daily_orders_df["order_count"], marker="o", linewidth=2, color="#90CAF9")
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

# Plot customer spend money
st.subheader("Spend Money by Customer")
col1, col2 = st.columns(2)

with col1:
    total_spend = sum_spend_df["total_spend"].sum()
    st.markdown(f"Total Spend: **{total_spend}**")

with col2:
    avg_spend = sum_spend_df["total_spend"].mean()
    st.markdown(f"Average Spend: **{avg_spend:.2f}**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=sum_spend_df, x="order_approved_at", y="total_spend", marker="o", linewidth=2, color="#90CAF9")
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)

# Order items plot (updated section)
st.subheader("Order Items")
col1, col2 = st.columns(2)

with col1:
    total_items = sum_order_items_df["product_count"].sum()
    st.markdown(f"Total Items: **{total_items}**")

with col2:
    avg_items = sum_order_items_df["product_count"].mean()
    st.markdown(f"Average Items: **{avg_items:.2f}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(45, 25))

# Most sold products
sns.barplot(x="product_count", y="product_category_name_english", data=sum_order_items_df.head(5), palette="viridis", ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=80)
ax[0].set_title("Most Sold Products", loc="center", fontsize=90)
ax[0].tick_params(axis='y', labelsize=55)
ax[0].tick_params(axis='x', labelsize=50)

# Fewest products sold
sns.barplot(x="product_count", y="product_category_name_english", data=sum_order_items_df.sort_values(by="product_count", ascending=True).head(5), palette="viridis", ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=80)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].set_title("Fewest Sold Products", loc="center", fontsize=90)
ax[1].tick_params(axis='y', labelsize=55)
ax[1].tick_params(axis='x', labelsize=50)

st.pyplot(fig)

# Review scores plot
st.subheader("Review Score")
col1, col2 = st.columns(2)

with col1:
    avg_review_score = review_score.mean()
    st.markdown(f"Average Review Score: **{avg_review_score:.2f}**")

with col2:
    most_common_review_score = review_score.idxmax()
    st.markdown(f"Most Common Review Score: **{most_common_review_score}**")

fig, ax = plt.subplots(figsize=(12, 6))
colors = sns.color_palette("viridis", len(review_score))

sns.barplot(x=review_score.index,
            y=review_score.values,
            order=review_score.index,
            palette=colors)

plt.title("Customer Review Scores for Service", fontsize=15)
plt.xlabel("Rating")
plt.ylabel("Count")
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
st.pyplot(fig)

# Customer distribution by state plot
st.subheader("Customer Distribution by State")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=state["customer_state"], y=state["customer_count"], ax=ax, palette='magma')
ax.set_title("Customer Count by State", fontsize=20)
ax.set_xlabel("State", fontsize=14)
ax.set_ylabel("Customer Count", fontsize=14)
st.pyplot(fig)

# Order status plot
st.subheader("Order Status")
fig, ax = plt.subplots(figsize=(12, 6))
order_status.plot(kind="bar", ax=ax, color='green')
ax.set_title("Order Status Distribution", fontsize=20)
ax.set_xlabel("Order Status", fontsize=14)
ax.set_ylabel("Frequency", fontsize=14)
st.pyplot(fig)

# Plot Brazil map with customer geolocation
st.subheader("Customer Geolocation in Brazil")
map_plot.plot()
