"""This notebook visualizes when messaging activity occurs across days and hours using a heatmap representation."""

#Imports datasets like messages and donations
from dataloader import *     
#Imports helper for saving figures and adding notes           
from functions.pic_notes_save import *  

def plot_words_heatmap_black_yellow_dates(df, threshold=1):
    if df is None or df.empty:
        return None

    df = df.copy()
    #extract hour and date only columns for grouping
    df["hour"] = df["dt"].dt.hour
    df["date_only"] = df["dt"].dt.date

    #Create a grid: rows = dates, columns = hours
    #Sum of word counts per day per hour
    grid = df.groupby(["date_only", "hour"])["word_count"].sum().unstack(fill_value=0)
    #grid covers all dates (even those without messages)
    all_dates = pd.date_range(df["date_only"].min(), df["date_only"].max(), freq='D')
    #ensures grid has all 24 hours
    all_hours = np.arange(0, 24)
    grid = grid.reindex(index=all_dates, columns=all_hours, fill_value=0)

    #Converts grid to binary 1 = activity above threshold, 0 = no or low activity
    binary_grid = (grid >= threshold).astype(int)
    #black= no activity to yellow= activity
    cmap = LinearSegmentedColormap.from_list("black_yellow", ["black", "yellow"])

    fig, ax = plt.subplots(figsize=(12, 6))
    #imshow() draws the 2D binary grid as a heatmap
    #.T transposes to show hours on Y-axis and dates on X-axis
    ax.imshow(binary_grid.T, origin='lower', aspect='auto', cmap=cmap, interpolation='nearest')

    #Set X-axis ticks as dates
    #To avoid messiness, shows roughly 10 evenly spaced date labels
    ax.set_xticks(np.arange(0, len(all_dates), max(1, len(all_dates)//10)))
    ax.set_xticklabels([all_dates[i].strftime("%Y-%m-%d") for i in ax.get_xticks()], rotation=45, ha='right')
    #Set Y-axis ticks as hours 0 to 23
    ax.set_yticks(np.arange(0, 24, 1))
    ax.set_yticklabels(np.arange(0, 24, 1))

    #label axes and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Hour of day")
    ax.set_title(f"Words Sent Heatmap (Threshold ≥ {threshold})")
    plt.tight_layout()
    return fig

def show_words_heatmap_dashboard_dates():
    donor_ids = sorted(donations["donor_id"].unique())

    #Donor input
    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    #Dropdown to select donor id 
    donor_dropdown = widgets.Dropdown(
        options=donor_ids,
        layout=widgets.Layout(width="300px")
    )
    #Dropdown to select specific chat or all chats 
    chat_select = widgets.Dropdown(
        options=["Select donor first"],
        description="Chat:",
        layout=widgets.Layout(width="420px")
    )

    #date pickers to limit the visualization range
    start_date = widgets.DatePicker(description="Start:", disabled=True)
    end_date   = widgets.DatePicker(description="End:", disabled=True)
    #Slider to change word count threshold minimum word count for marking activity (1 = at least 1 word sent)
    threshold_slider = widgets.IntSlider(value=5, min=1, max=100, step=1, description="Threshold N")
    out_plot = widgets.Output()

    chat_select._donor_df = None

    #Filter dropdown based on input
    def update_donor_dropdown(change):
        text = change["new"].strip()
        if not text:
            donor_dropdown.options = donor_ids
        else:
            matches = [d for d in donor_ids if text.lower() in str(d).lower()]
            donor_dropdown.options = matches if matches else ["No match"]

    donor_input.observe(update_donor_dropdown, names="value")

    #loads messages of the selected donor and updates available chats and dates
    def load_donor(*args):
        out_plot.clear_output()
        donor = donor_input.value.strip() or donor_dropdown.value
        #shows error if invalid donor
        if donor not in donor_ids:
            chat_select.options = ["Invalid donor"]
            with out_plot:
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            return
        #filter messages that belong to this donors donations
        donor_rows = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"]==donor, "donation_id"]
        )].copy()
        #Keep only messages sent by this donor not received
        donor_rows = donor_rows[donor_rows["sender_id"]==donor].copy()

        #If no messages show warning and exit
        if donor_rows.empty:
            chat_select.options = ["No messages"]
            with out_plot:
                display(HTML("<b style='color:orange;'>No messages for this donor.</b>"))
            return

        #enables date selection and set initial range to min or max dates of messages
        start_date.disabled = False
        end_date.disabled = False
        start_date.value = donor_rows["dt"].min().date()
        end_date.value = donor_rows["dt"].max().date()

        #showing individual chat
        chats = donor_rows["conversation_id"].unique()
        options = [(f"Chat {c}", c) for c in chats]
        #showing all chats together
        options.insert(0, ("All Chats", "ALL"))
        #update dropdown values
        chat_select.options = options
        chat_select.value = options[0][1]
        chat_select._donor_df = donor_rows
        draw_plot()

    #filter data based on chat and date
    def filtered_df():
        donor_df = chat_select._donor_df
        if donor_df is None:
            return pd.DataFrame()
        df = donor_df.copy()
        #Convert date pickers to timestamps and filter messages in range
        start_ts = pd.Timestamp(start_date.value)
        end_ts = pd.Timestamp(end_date.value) + pd.Timedelta(days=1)
        df = df[(df["dt"] >= start_ts) & (df["dt"] < end_ts)]
        if chat_select.value != "ALL":
            df = df[df["conversation_id"] == chat_select.value]
        return df

    #draws heatmap
    def draw_plot(_=None):
        out_plot.clear_output()
        df = filtered_df()
        donor = donor_input.value.strip() or donor_dropdown.value
        with out_plot:
            fig = plot_words_heatmap_black_yellow_dates(df, threshold=threshold_slider.value)
            #Handles empty data case
            if fig is None:
                display(HTML("<b style='color:orange;'>No data to plot for selected range/chat.</b>"))
            else:
                add_save_and_note_controls(fig, donor, chat_select.value, "heatmap")
                plt.show()

    #widget event bindings
    donor_dropdown.observe(lambda ch: load_donor(), names="value")
    donor_input.on_submit(load_donor)
    chat_select.observe(draw_plot, names="value")
    start_date.observe(draw_plot, names="value")
    end_date.observe(draw_plot, names="value")
    threshold_slider.observe(draw_plot, names="value")

    #layout
    display(widgets.VBox([
        widgets.HTML("<h2>Words Heatmap Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown, chat_select], layout=widgets.Layout(gap="10px")),
        widgets.HBox([start_date, end_date, threshold_slider], layout=widgets.Layout(gap="10px")),
        out_plot
    ]))
