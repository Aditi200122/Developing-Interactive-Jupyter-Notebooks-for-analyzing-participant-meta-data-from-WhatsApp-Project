"""This notebook investigates the temporary patterns of messaging activity to determine whether messages occur regularly or in bursts.
By analyzing inter-message intervals (the time between consecutive messages), we can compute burstiness measures (B1 and B2) that quantify how clustered or evenly spread communication events are.
"""
from dataloader import *                #Imports datasets like 'messages' and 'donations'
from functions.pic_notes_save import *  #Imports function 'add_save_and_note_controls' for saving figure and taking notes 

def compute_burstiness(days):
    #Sorts all message dates 
    days_sorted = sorted(days)
    #If less than 2 message days, burstiness can't be measured (no intervals)
    if len(days_sorted) < 2:
        return (np.nan, np.nan)
    #Compute time gaps
    inter_event = np.diff(pd.to_datetime(days_sorted)).astype("timedelta64[D]").astype(int)
    #mu = mean and sigma = standard deviation of intervals.
    mu = inter_event.mean()
    if mu == 0:
        return (np.nan, np.nan)
    sigma = inter_event.std(ddof=0)
    #r=Coefficient of variation tells us how variable the intervals are relative to the mean
    r = sigma / mu
    n = len(days_sorted)
    #B1 (classic burstiness index), 
    B1 = (r - 1) / (r + 1) if (r + 1) != 0 else np.nan
    if n > 1:
        num = (np.sqrt(n + 1) * r) - np.sqrt(n - 1)
        den = ((np.sqrt(n + 1) - 2) * r) + np.sqrt(n - 1)
        B2 = num / den if den != 0 else np.nan
    else:
        #B2 refines B1 to reduce bias when few events exist
        B2 = np.nan
    return (B1, B2)

#B1 < -0.2 is regular,B1 between -0.2 and +0.2 is random, B1 > +0.2 is highly bursty
def classify_b1(b1, lo=-0.2, hi=0.2):
    if pd.isna(b1):
        return "N/A"
    if b1 < lo:
        return "Regular"
    if b1 > hi:
        return "Bursty"
    return "Random"

def plot_raster(days, title, B1=None, B2=None, ax=None, color=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 2))
    ax.eventplot(pd.to_datetime(sorted(days)), orientation="horizontal", colors=color or "black", linewidths=1.5)
    extra = ""
    if B1 is not None and B2 is not None:
        extra = f"  (B1={B1:.2f}, B2={B2:.2f})"
    ax.set_title(title + extra)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlabel("Date")
    return ax


def show_raster_dashboard_overall():
    donor_ids = sorted(donations["donor_id"].unique())

    #Input text to write donor id 
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
    #Dropdown to select Chat(Overall aggregate,overall dominant, largest absolute b1 value or individual chats)
    chat_select = widgets.Dropdown(
        options=["Select donor first"],
        description="Chat:",
        layout=widgets.Layout(width="600px")
    )

    out_raster = widgets.Output()

    #Internal storage
    chat_select._burst_df = None
    chat_select._days_by_chat = None
    chat_select._donor_df = None
    #updates when new donor id selected
    def update_donor_dropdown(change):
        text = change["new"].strip()
        if not text:
            donor_dropdown.options = donor_ids
        else:
            matches = [d for d in donor_ids if text.lower() in str(d).lower()]
            donor_dropdown.options = matches if matches else ["No match"]

    donor_input.observe(update_donor_dropdown, names="value")

    #Load donor data
    def load_donor(*args):
        out_raster.clear_output()
        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_ids:
            with out_raster:
                display(HTML(f"<b style='color:red;'>Invalid donor ID: {donor}</b>"))
            chat_select.options = ["Invalid donor"]
            return
        #Filters messages sent by the selected donor
        donor_rows = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"] == donor, "donation_id"]
        )].copy()
        donor_rows = donor_rows[donor_rows["sender_id"] == donor].copy()

        if donor_rows.empty:
            chat_select.options = ["No messages from donor"]
            with out_raster:
                display(HTML("<b style='color:orange;'>This donor has no sent messages.</b>"))
            return
        #Compute burstiness per chat where each chat has list of message days and B1, B2 burstiness scores
        days_by_chat = donor_rows.groupby("conversation_id")["date_only"].apply(lambda s: sorted(set(s)))
        burst = days_by_chat.apply(lambda d: compute_burstiness(d))
        burst_df = pd.DataFrame(burst.tolist(), index=days_by_chat.index, columns=["B1","B2"]).dropna(how="all")

        chat_options = []
        for cid, row in burst_df.iterrows():
            b1 = row["B1"]
            label = classify_b1(b1)
            #adds chat labels like Chat 12 (Bursty, B1=0.65) also adds three overall views
            chat_options.append((f"Chat {cid} ({label}, B1={b1:.2f})", cid))
        
        """OVERALL_AGGREGATE show a raster that aggregates all donor's days across all chats into a single set of days and compute an aggregate B1. Useful to see the donor's overall pattern.
        OVERALL_DOMINANT finds classification counts across chats (how many Regular/Bursty/Random) and plots an example chat for the dominant class (or multiple if tie).
        OVERALL_EXTREME finds the chat with the largest absolute B1 (most extreme) and plots it."""

        chat_options.insert(0, ("Overall (Aggregate B1)", "OVERALL_AGGREGATE"))
        chat_options.insert(1, ("Overall (Dominant Behavior)", "OVERALL_DOMINANT"))
        chat_options.insert(2, ("Overall (Largest Absolute B1 Value)", "OVERALL_EXTREME"))

        chat_select.options = chat_options
        chat_select.value = chat_options[0][1]
        chat_select._burst_df = burst_df
        chat_select._days_by_chat = days_by_chat
        chat_select._donor_df = donor_rows
        draw_raster()

    def draw_raster(_=None):
        out_raster.clear_output()
        burst_df = chat_select._burst_df
        days_by_chat = chat_select._days_by_chat
        donor_df = chat_select._donor_df
        choice = chat_select.value
        donor = donor_input.value.strip() or donor_dropdown.value

        if burst_df is None or choice is None:
            return

        with out_raster:
            if choice == "OVERALL_AGGREGATE":
                all_days = sorted(set(donor_df["date_only"]))
                B1, B2 = compute_burstiness(all_days)
                label = classify_b1(B1)
                fig, ax = plt.subplots(figsize=(10, 2.5))
                plot_raster(all_days, f"Overall Donor Chats (Aggregate B1: {label})", B1, B2, ax=ax,
                            color=("green" if label == "Regular" else "red" if label == "Bursty" else "blue"))
                add_save_and_note_controls(fig, donor, choice, "burstiness", extra_tag="overall-aggregate")
                plt.show()

            elif choice == "OVERALL_DOMINANT":
                classifications = burst_df["B1"].apply(classify_b1)
                if classifications.empty:
                    display(HTML("<b style='color:orange;'>No chats to analyze.</b>"))
                    return
                counts = classifications.value_counts()
                max_count = counts.max()
                dominant_types = counts[counts == max_count].index.tolist()
                for i, dt in enumerate(dominant_types, start=1):
                    chat_id = classifications[classifications == dt].index[0]
                    row = burst_df.loc[chat_id]
                    days = days_by_chat[chat_id]
                    fig, ax = plt.subplots(figsize=(10, 2.5))
                    plot_raster(days, f"Example of {dt} chat", row["B1"], row["B2"], ax=ax,
                                color=("green" if dt == "Regular" else "red" if dt == "Bursty" else "blue"))
                    add_save_and_note_controls(fig, donor, chat_id, "burstiness", extra_tag=f"overall-dominant-tie{i}-{dt}")
                    plt.show()

            elif choice == "OVERALL_EXTREME":
                most_extreme_chat_id = burst_df["B1"].abs().idxmax()
                row = burst_df.loc[most_extreme_chat_id]
                days = days_by_chat[most_extreme_chat_id]
                label = classify_b1(row["B1"])
                fig, ax = plt.subplots(figsize=(10, 2.5))
                plot_raster(days, f"Largest Absolute B1 Value: {label}", row["B1"], row["B2"], ax=ax,
                            color=("green" if label == "Regular" else "red" if label == "Bursty" else "blue"))
                add_save_and_note_controls(fig, donor, most_extreme_chat_id, "burstiness", extra_tag="overall-extreme")
                plt.show()

            else:
                if choice in burst_df.index:
                    row = burst_df.loc[choice]
                    days = days_by_chat[choice]
                    label = classify_b1(row["B1"])
                    fig, ax = plt.subplots(figsize=(10, 2.5))
                    plot_raster(days, f"Chat {choice} ({label})", row["B1"], row["B2"], ax=ax,
                                color=("green" if label == "Regular" else "red" if label == "Bursty" else "blue"))
                    add_save_and_note_controls(fig, donor, choice, "burstiness")
                    plt.show()

    #dynamically reloads and redraws plots when donor or chat is changed
    donor_dropdown.observe(lambda ch: load_donor(), names="value")
    donor_input.on_submit(load_donor)
    chat_select.observe(draw_raster, names="value")

    display(widgets.VBox([
        widgets.HTML("<h2>Raster Plot Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown, chat_select], layout=widgets.Layout(gap="10px")),
        out_raster
    ]))
