"""This notebook help us visualize how many unique senders were active each day and daily words"""

#Imports datasets like messages and donations
from dataloader import *     
#Imports helper for saving figures and adding notes           
from functions.pic_notes_save import * 

def plot_active_chats_heatmap_colored(df, view="All"):
    """
    Heatmap showing chat activity by day.
    Sent = yellow, Received = cyan, Both = orange (for All view)
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    #extracts only the date portion from timestamp ignore hours and minutes
    df["date_only"] = df["dt"].dt.date
    #collect all unique chat ids and all unique dates in the period
    all_chats = sorted(df["conversation_id"].unique())
    all_dates = pd.date_range(df["date_only"].min(), df["date_only"].max(), freq='D')

    if view in ["Sent", "Received"]:
        #if user selected sent keep only donors messages
        if view == "Sent":
            df = df[df["sender_id"] == df["sender_id"].iloc[0]]
            color_map = ["black", "yellow"]
        else:
            #otherwise, show only messages from the contact
            df = df[df["sender_id"] != df["sender_id"].iloc[0]]
            color_map = ["black", "cyan"]
        #Group by date and conversation, count messages per cell    
        grid = df.groupby(["date_only", "conversation_id"]).size().unstack(fill_value=0)
        #convert to binary 1=active chat that day, 0=inactive
        grid = (grid > 0).astype(int)
        #reindex so all dates and chats are included, even with no activity
        grid = grid.reindex(index=all_dates, columns=all_chats, fill_value=0)
        cmap = LinearSegmentedColormap.from_list("custom_cmap", color_map)

    else:  #All messages combine both sent & received into one heatmap
        #Sent grid
        sent = (df[df["sender_id"]==df["sender_id"].iloc[0]]
                .groupby(["date_only","conversation_id"]).size().unstack(fill_value=0) > 0).astype(int)
        #Received grid
        rec = (df[df["sender_id"]!=df["sender_id"].iloc[0]]
               .groupby(["date_only","conversation_id"]).size().unstack(fill_value=0) > 0).astype(int)
        sent = sent.reindex(index=all_dates, columns=all_chats, fill_value=0)
        rec = rec.reindex(index=all_dates, columns=all_chats, fill_value=0)
        #0=none, 1=sent only, 2=received only, 3=both
        grid = np.zeros(sent.shape, dtype=int)
        grid[(sent==1) & (rec==0)] = 1
        grid[(sent==0) & (rec==1)] = 2
        grid[(sent==1) & (rec==1)] = 3
        cmap = LinearSegmentedColormap.from_list("all_msg_cmap", ["black", "yellow", "cyan", "orange"])

    fig, ax = plt.subplots(figsize=(14,6))
    ax.imshow(grid.T, origin='lower', aspect='auto', cmap=cmap, interpolation='nearest')
    #x-axis as dates 
    ax.set_xticks(np.arange(0, len(all_dates), max(1, len(all_dates)//10)))
    ax.set_xticklabels([all_dates[i].strftime("%Y-%m-%d") for i in ax.get_xticks()], rotation=45, ha='right')
    #y-axis as chat ids
    ax.set_yticks(np.arange(len(all_chats)))
    ax.set_yticklabels(all_chats)

    #labels and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Chat ID")
    ax.set_title(f"Active Chats Heatmap for Donor {df['sender_id'].iloc[0]} ({view} Messages)")
    plt.tight_layout()
    return fig

def show_active_chats_dashboard():
    #gets all unique donor ids from donations data
    donor_ids = sorted(donations["donor_id"].unique())
    
    #Donor text input
    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    #Donor Dropdown 
    donor_dropdown = widgets.Dropdown(
        options=donor_ids[:50],
        layout=widgets.Layout(width="300px")
    )

    #radio buttons to choose sent ,received or all
    view_selector = widgets.RadioButtons(
        options=["Sent", "Received", "All"],
        description="View:",
        layout=widgets.Layout(width="200px")
    )
    #date pickers to filter messages
    start_date = widgets.DatePicker(description="Start:", disabled=True)
    end_date   = widgets.DatePicker(description="End:", disabled=True)
    #output
    out_plot = widgets.Output()
    #holder for currently loaded donors data
    donor_df_holder = {"df": None}


    #triggered when donor is selected or entered  and loads all messages for that donor , enables date filters
    def load_donor(*args):
        out_plot.clear_output()
        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_ids:
            with out_plot:
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            return
        #find all messages for this donor
        df = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"]==donor, "donation_id"]
        )].copy()
        if df.empty:
            with out_plot:
                display(HTML("<b style='color:orange;'>No messages for this donor.</b>"))
            return
        #enable date filters
        start_date.disabled = False
        end_date.disabled = False
        start_date.value = df["dt"].min().date()
        end_date.value = df["dt"].max().date()
        donor_df_holder["df"] = df
        draw_plot()

    #filters donors messages between the selected start and end dates
    def filtered_df():
        df = donor_df_holder["df"]
        if df is None:
            return pd.DataFrame()
        df = df.copy()
        start_ts = pd.Timestamp(start_date.value)
        end_ts = pd.Timestamp(end_date.value) + pd.Timedelta(days=1)
        df = df[(df["dt"] >= start_ts) & (df["dt"] < end_ts)]
        return df
    #creates and displays the heatmap figure for the filtered data
    def draw_plot(_=None):
        out_plot.clear_output()
        df = filtered_df()
        view = view_selector.value
        with out_plot:
            fig = plot_active_chats_heatmap_colored(df, view)
            if fig is None:
                display(HTML("<b style='color:orange;'>No data to plot for selected range.</b>"))
            else:
                add_save_and_note_controls(fig, donor_input.value.strip() or donor_dropdown.value, "ALL", "active_chats")
                plt.show()

    #link widgets to functions
    donor_dropdown.observe(load_donor, names="value")
    donor_input.on_submit(load_donor)
    start_date.observe(draw_plot, names="value")
    end_date.observe(draw_plot, names="value")
    view_selector.observe(draw_plot, names="value")

    #layout
    display(widgets.VBox([
        widgets.HTML("<h2>Active Chats Heatmap Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown, view_selector], layout=widgets.Layout(gap="10px")),
        widgets.HBox([start_date, end_date], layout=widgets.Layout(gap="10px")),
        out_plot
    ]))

#time series plots 
def plot_time_series_by_date(df, value_col, ylabel, title, ma_window=20):
    """
    Plots a time series with optional moving average.
    
    df: DataFrame with 'date_only' column
    value_col: column to plot (e.g., 'word_count' or 'conversation_id')
    ylabel: y-axis label
    title: figure title
    ma_window: moving average window in days
    """
    if df is None or df.empty:
        return None

    df["date_only"] = df["dt"].dt.date
    all_dates = pd.date_range(df["date_only"].min(), df["date_only"].max())

    if value_col != "conversation_id":
        daily_values = df.groupby("date_only")[value_col].sum().reindex(all_dates, fill_value=0)
    else:
        daily_values = df.groupby("date_only")[value_col].nunique().reindex(all_dates, fill_value=0)

    ma = daily_values.rolling(ma_window, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(daily_values.index, daily_values.values, alpha=0.4, label=ylabel)
    ax.plot(ma.index, ma.values, linewidth=2.2, label=f"{ma_window}-day moving avg")
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()
    return fig


def show_daily_words_dashboard():
    donor_ids = sorted(donations["donor_id"].unique())

    #donor input 
    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    #donor dropdown
    donor_dropdown = widgets.Dropdown(
        options=donor_ids[:50],
        layout=widgets.Layout(width="300px")
    )

    chat_select = widgets.Dropdown(
        options=["Select donor first"],
        description="Chat:",
        layout=widgets.Layout(width="420px")
    )

    start_date = widgets.DatePicker(description="Start:", disabled=True)
    end_date   = widgets.DatePicker(description="End:", disabled=True)
    ma_slider = widgets.IntSlider(value=20, min=1, max=50, step=1, description="MA window")
    out_plot = widgets.Output()
    donor_df_holder = {"df": None}

    #update dropdown while typing
    def update_donor_dropdown(change):
        text = change["new"].strip()
        if not text:
            donor_dropdown.options = donor_ids[:50]
        else:
            matches = [d for d in donor_ids if text.lower() in str(d).lower()]
            donor_dropdown.options = matches[:100] if matches else ["No match"]

    donor_input.observe(update_donor_dropdown, names="value")

    #load donor automatically on selection
    def load_donor(*args):
        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_ids:
            chat_select.options = ["Invalid donor"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            return

        df = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"]==donor, "donation_id"]
        )].copy()

        if df.empty:
            chat_select.options = ["No messages"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML("<b style='color:orange;'>No messages for this donor.</b>"))
            return

        #Only donor sent messages for Daily Words
        df = df[df["sender_id"] == donor].copy()
        start_date.disabled = False
        end_date.disabled = False
        start_date.value = df["dt"].min().date()
        end_date.value = df["dt"].max().date()

        chats = df["conversation_id"].unique()
        options = [(f"Chat {c}", c) for c in chats]
        options.insert(0, ("All Chats", "ALL"))
        chat_select.options = options
        chat_select.value = options[0][1]

        donor_df_holder["df"] = df
        draw_plot()

    def filtered_df():
        df = donor_df_holder["df"]
        if df is None:
            return pd.DataFrame()
        df = df.copy()
        start_ts = pd.Timestamp(start_date.value)
        end_ts = pd.Timestamp(end_date.value) + pd.Timedelta(days=1)
        df = df[(df["dt"] >= start_ts) & (df["dt"] < end_ts)]
        if chat_select.value != "ALL":
            df = df[df["conversation_id"] == chat_select.value]
        return df

    def draw_plot(_=None):
        out_plot.clear_output()
        df = filtered_df()
        donor = donor_input.value.strip() or donor_dropdown.value
        with out_plot:
            fig = plot_time_series_by_date(df, "word_count", "Total words per day", f"Daily Words for Donor {donor}", ma_window=ma_slider.value)
            if fig is None:
                display(HTML("<b style='color:orange;'>No data to plot for selected range/chat.</b>"))
            else:
                add_save_and_note_controls(fig, donor, chat_select.value, "daily_words")
                plt.show()

    #event bindings
    donor_dropdown.observe(load_donor, names="value")
    donor_input.on_submit(load_donor)
    chat_select.observe(draw_plot, names="value")
    start_date.observe(draw_plot, names="value")
    end_date.observe(draw_plot, names="value")
    ma_slider.observe(draw_plot, names="value")

    display(widgets.VBox([
        widgets.HTML("<h2>Daily Words Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown, chat_select], layout=widgets.Layout(gap="10px")),
        widgets.HBox([start_date, end_date, ma_slider], layout=widgets.Layout(gap="10px")),
        out_plot
    ]))

def show_daily_active_contacts_time_series_dashboard():
    donor_ids = sorted(donations["donor_id"].unique())

    #donor input
    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    #donor dropdown
    donor_dropdown = widgets.Dropdown(
        options=donor_ids,
        layout=widgets.Layout(width="300px")
    )

    chat_select = widgets.Dropdown(
        options=["Select donor first"],
        description="Chat:",
        layout=widgets.Layout(width="420px")
    )

    start_date = widgets.DatePicker(description="Start:", disabled=True)
    end_date   = widgets.DatePicker(description="End:", disabled=True)
    ma_slider = widgets.IntSlider(value=20, min=1, max=50, step=1, description="MA window")
    out_plot = widgets.Output()
    donor_df_holder = {"df": None}

    #update dropdown while typing
    def update_donor_dropdown(change):
        text = change["new"].strip()
        if not text:
            donor_dropdown.options = donor_ids[:50]
        else:
            matches = [d for d in donor_ids if text.lower() in str(d).lower()]
            donor_dropdown.options = matches if matches else ["No match"]

    donor_input.observe(update_donor_dropdown, names="value")

    #load donor automatically
    def load_donor(*args):
        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_ids:
            chat_select.options = ["Invalid donor"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            return

        df = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"]==donor, "donation_id"]
        )].copy()

        if df.empty:
            chat_select.options = ["No messages"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML("<b style='color:orange;'>No messages for this donor.</b>"))
            return

        start_date.disabled = False
        end_date.disabled = False
        start_date.value = df["dt"].min().date()
        end_date.value = df["dt"].max().date()

        chats = df["conversation_id"].unique()
        options = [(f"Chat {c}", c) for c in chats]
        options.insert(0, ("All Chats", "ALL"))
        chat_select.options = options
        chat_select.value = options[0][1]

        donor_df_holder["df"] = df
        draw_plot()

    def filtered_df():
        df = donor_df_holder["df"]
        if df is None:
            return pd.DataFrame()
        df = df.copy()
        start_ts = pd.Timestamp(start_date.value)
        end_ts = pd.Timestamp(end_date.value) + pd.Timedelta(days=1)
        df = df[(df["dt"] >= start_ts) & (df["dt"] < end_ts)]
        if chat_select.value != "ALL":
            df = df[df["conversation_id"] == chat_select.value]
        return df

    def draw_plot(_=None):
        out_plot.clear_output()
        df = filtered_df()
        donor = donor_input.value.strip() or donor_dropdown.value
        with out_plot:
            fig = plot_time_series_by_date(df, "conversation_id", "Number of active chats", f"Daily Active Contacts for Donor {donor}", ma_window=ma_slider.value)
            if fig is None:
                display(HTML("<b style='color:orange;'>No data to plot for selected range/chat.</b>"))
            else:
                add_save_and_note_controls(fig, donor, chat_select.value, "daily_active_contacts")
                plt.show()

    #event bindings
    donor_dropdown.observe(load_donor, names="value")
    donor_input.on_submit(load_donor)
    chat_select.observe(draw_plot, names="value")
    start_date.observe(draw_plot, names="value")
    end_date.observe(draw_plot, names="value")
    ma_slider.observe(draw_plot, names="value")

    display(widgets.VBox([
        widgets.HTML("<h2>Daily Active Contacts Time Series Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown, chat_select], layout=widgets.Layout(gap="10px")),
        widgets.HBox([start_date, end_date, ma_slider], layout=widgets.Layout(gap="10px")),
        out_plot
    ]))


#heatmap for words dasboard 
def plot_daily_words_heatmap_words_axis(df, view="All"):
    """
    Heatmap of total words per day for selected donor/chat/view.
    Y-axis = total words (0-2000, readable ticks like time series)
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df["date_only"] = df["dt"].dt.date

    #filter by view
    if view == "Sent":
        df = df[df["sender_id"] == df["sender_id"].iloc[0]]
    elif view == "Received":
        df = df[df["sender_id"] != df["sender_id"].iloc[0]]

    #aggregate total words per day
    daily_words = df.groupby("date_only")["word_count"].sum()
    all_dates = pd.date_range(daily_words.index.min(), daily_words.index.max(), freq='D')
    daily_words = daily_words.reindex(all_dates, fill_value=0)

    #creates grid 1 row per word count bin
    max_words = 2000
    num_bins = 200 
    y_bins = np.linspace(0, max_words, num_bins)
    grid = np.zeros((num_bins, len(daily_words)))

    for i, val in enumerate(daily_words):
        idx = min(np.searchsorted(y_bins, val), num_bins-1)
        grid[:idx+1, i] = 1 

    cmap = LinearSegmentedColormap.from_list("words_cmap", ["black", "yellow"])

    fig, ax = plt.subplots(figsize=(14,6))
    ax.imshow(grid, origin='lower', aspect='auto', cmap=cmap, interpolation='nearest')

    #X-axis as dates
    ax.set_xticks(np.arange(0, len(all_dates), max(1, len(all_dates)//10)))
    ax.set_xticklabels([all_dates[i].strftime("%Y-%m-%d") for i in ax.get_xticks()], rotation=45, ha="right")

    #Y-axis ticks every 500 words
    ytick_values = np.arange(0, max_words+1, 500)
    ytick_indices = [np.searchsorted(y_bins, y) for y in ytick_values]
    ax.set_yticks(ytick_indices)
    ax.set_yticklabels(ytick_values)

    ax.set_xlabel("Date")
    ax.set_ylabel("Total Words")
    ax.set_title(f"Daily Words Heatmap for Donor {df['sender_id'].iloc[0]} ({view} Messages)")
    plt.tight_layout()
    return fig
    

def show_daily_words_heatmap_words_axis_dashboard():
    donor_ids = sorted(donations["donor_id"].unique())

    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    donor_dropdown = widgets.Dropdown(
        options=donor_ids[:50],
        layout=widgets.Layout(width="300px")
    )
    chat_select = widgets.Dropdown(
        options=["Select donor first"],
        description="Chat:",
        layout=widgets.Layout(width="420px")
    )
    view_selector = widgets.RadioButtons(
        options=["Sent", "Received", "All"],
        description="View:",
        layout=widgets.Layout(width="200px")
    )
    start_date = widgets.DatePicker(description="Start:", disabled=True)
    end_date   = widgets.DatePicker(description="End:", disabled=True)
    out_plot = widgets.Output()
    donor_df_holder = {"df": None}

    #update dropdown while typing
    def update_donor_dropdown(change):
        text = change["new"].strip()
        if not text:
            donor_dropdown.options = donor_ids[:50]
        else:
            matches = [d for d in donor_ids if text.lower() in str(d).lower()]
            donor_dropdown.options = matches[:100] if matches else ["No match"]

    donor_input.observe(update_donor_dropdown, names="value")

    #load donor messages
    def load_donor(*args):
        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_ids:
            chat_select.options = ["Invalid donor"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            return

        df = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"]==donor, "donation_id"]
        )].copy()

        if df.empty:
            chat_select.options = ["No messages"]
            start_date.disabled = True
            end_date.disabled = True
            with out_plot:
                out_plot.clear_output()
                display(HTML("<b style='color:orange;'>No messages for this donor.</b>"))
            return

        start_date.disabled = False
        end_date.disabled = False
        start_date.value = df["dt"].min().date()
        end_date.value = df["dt"].max().date()

        chats = df["conversation_id"].unique()
        options = [(f"Chat {c}", c) for c in chats]
        options.insert(0, ("All Chats", "ALL"))
        chat_select.options = options
        chat_select.value = options[0][1]

        donor_df_holder["df"] = df
        draw_plot()

    def filtered_df():
        df = donor_df_holder["df"]
        if df is None:
            return pd.DataFrame()
        df = df.copy()
        start_ts = pd.Timestamp(start_date.value)
        end_ts = pd.Timestamp(end_date.value) + pd.Timedelta(days=1)
        df = df[(df["dt"] >= start_ts) & (df["dt"] < end_ts)]
        if chat_select.value != "ALL":
            df = df[df["conversation_id"] == chat_select.value]
        return df

    def draw_plot(_=None):
        out_plot.clear_output()
        df = filtered_df()
        view = view_selector.value
        with out_plot:
            fig = plot_daily_words_heatmap_words_axis(df, view=view)
            if fig is None:
                display(HTML("<b style='color:orange;'>No data to plot for selected range/chat.</b>"))
            else:
                add_save_and_note_controls(
                    fig, donor_input.value.strip() or donor_dropdown.value,
                    chat_select.value, "daily_words_heatmap_words_axis"
                )
                plt.show()

    #event bindings
    donor_dropdown.observe(load_donor, names="value")
    donor_input.on_submit(load_donor)
    chat_select.observe(draw_plot, names="value")
    start_date.observe(draw_plot, names="value")
    end_date.observe(draw_plot, names="value")
    view_selector.observe(draw_plot, names="value")

    #layout
    display(widgets.VBox([
        widgets.HTML("<h2>Daily Words Heatmap Dashboard (Words Axis)</h2>"),
        widgets.HBox([donor_input, donor_dropdown, chat_select, view_selector], layout=widgets.Layout(gap="10px")),
        widgets.HBox([start_date, end_date], layout=widgets.Layout(gap="10px")),
        out_plot
    ]))
