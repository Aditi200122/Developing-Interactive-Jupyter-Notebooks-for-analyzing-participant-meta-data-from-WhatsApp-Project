"""Gini Analysis to see inequality in Communication
This notebook analyzes how unevenly messages are distributed among different contacts using the Gini coefficient and the Lorenz curve.
"""
#Imports datasets like messages and donations
from dataloader import * 
#Imports function add_save_and_note_controls  for saving figure and taking notes 
from functions.pic_notes_save import * 

#metric implementation
def calculate_gini(counts):
    #sorting the values in ascending order to assign rank lowest to highest
    values = sorted(list(counts.values()))
    #total number of contacts
    n = len(values) 
    #sum of all counts (total messages or words)
    total = sum(values) 
    #if no contacts or no messages/words
    if n == 0 or total == 0:
        #Gini is undefined, treat as perfectly equal
        return 0.0
    #Weighted sum: each value multiplied by its rank (i+1 because rank starts from 1)
    weighted_sum = sum((i + 1) * val for i, val in enumerate(values))
    return (2 * weighted_sum) / (n * total) - (n + 1) / n #This formula am using from dona research paper

#To show dashboard
def show_gini_dashboard():

    #finds list of all unique donors and sorts
    donor_ids = sorted(donations['donor_id'].unique())

    #widgets for text input
    donor_search = widgets.Text(
        placeholder="Type donor_id or select from dropdown...",
        description="Search:",
        layout=widgets.Layout(width="300px")
    )

    #for dropdown of donor lidt
    donor_dropdown = widgets.Dropdown(
        options=donor_ids,
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    #for metric selection either messages or words
    metric_select = widgets.RadioButtons(
        options=["Messages", "Words"],
        description="Metric:",
        layout=widgets.Layout(width="200px")
    )

    #outputs
    bar_output = widgets.Output()
    lorenz_output = widgets.Output()
    summary_output = widgets.Output()

    donor_data_cache = {}

    #for clearing the previous output and updates when anything change donor, metric
    def update_dashboard(change=None):
        bar_output.clear_output()
        lorenz_output.clear_output()
        summary_output.clear_output()

        donor = donor_dropdown.value
        metric = metric_select.value

        if donor not in donor_ids:
            with summary_output:
                display(HTML(f"<b style='color:red;'>Donor '{donor}' not found.</b>"))
            return

        #cache donor data stores already loaded donor messages (so switching doesn't reload data every time)
        if donor in donor_data_cache:
            donor_msgs = donor_data_cache[donor]
        else:
            donor_msgs = messages[messages['donation_id'].isin(
                donations[donations['donor_id'] == donor]['donation_id']
            )]
            donor_data_cache[donor] = donor_msgs

        #calculation for messages or words counts (based on messages sent by donor)
        if metric == "Messages":
            counts = donor_msgs[donor_msgs['sender_id'] == donor].groupby('conversation_id').size().to_dict()
        else:
            counts = donor_msgs[donor_msgs['sender_id'] == donor].groupby('conversation_id')['word_count'].sum().to_dict()

        gini = calculate_gini(counts)

        #always show bar chart
        with bar_output:
            counts_series = pd.Series(counts).sort_values(ascending=False)
            if counts_series.empty:
                display(HTML("<b style='color:orange;'>No data to plot.</b>"))
            else:
                short_labels = [str(x)[:8] + "..." if len(str(x)) > 8 else str(x) for x in counts_series.index]
                fig, ax = plt.subplots(figsize=(max(6, len(counts_series) * 0.6), 5))
                counts_series.plot(kind='bar', ax=ax)
                ax.set_title(f"{metric} Count per Contact")
                ax.set_xticks(range(len(short_labels)))
                ax.set_xticklabels(short_labels, rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                add_save_and_note_controls(fig, donor, "ALL", "gini", extra_tag="bar")
                plt.show()

        #always show lorenz curve
        with lorenz_output:
            values = np.array(sorted(counts.values())) if len(counts) > 0 else np.array([0])
            if values.sum() == 0:
                display(HTML("<b style='color:orange;'>Not enough data for Lorenz curve.</b>"))
            else:
                cumulative = np.cumsum(values) / values.sum()
                cumulative = np.insert(cumulative, 0, 0)
                contacts = np.linspace(0, 1, len(values) + 1)
                fig, ax = plt.subplots(figsize=(6, 5))
                ax.plot(contacts * 100, cumulative * 100, label='Lorenz Curve')
                ax.plot([0, 100], [0, 100], linestyle='--', color='gray', label='Perfect Equality')
                ax.fill_between(contacts * 100, contacts * 100, cumulative * 100, color='lightblue', alpha=0.3)
                ax.set_title(f"{metric} Distribution (Gini = {gini:.3f})")
                ax.set_xlabel("Cumulative % of Contacts")
                ax.set_ylabel("Cumulative % of Messages/Words")
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                add_save_and_note_controls(fig, donor, "ALL", "gini", extra_tag="lorenz")
                plt.show()

        #summary stays below
        with summary_output:
            display(HTML(
                f"<div style='background:#f5f5f5;padding:16px;border-radius:8px;width:260px;'>"
                f"<h4 style='margin-top:0;'>Summary</h4>"
                f"<p><b>Gini:</b> {gini:.3f}</p>"
                f"<p>{'High inequality (few contacts dominate)' if gini > 0.5 else 'Relatively balanced distribution'}.</p>"
                f"</div>"
            ))

    #Search filtering
    def filter_donors(change):
        query = donor_search.value.lower().strip()
        if query == "":
            donor_dropdown.options = donor_ids
        else:
            filtered = [d for d in donor_ids if query in str(d).lower()]
            donor_dropdown.options = filtered if filtered else ["No match"]

    donor_search.observe(filter_donors, names='value')

    #When pressing Enter in text box, auto-select donor
    def on_enter(change):
        value = donor_search.value.strip()
        if value in donor_ids:
            donor_dropdown.value = value
            update_dashboard()
        elif value:
            with summary_output:
                summary_output.clear_output()
                display(HTML(f"<b style='color:red;'>Donor '{value}' not found.</b>"))

    donor_search.on_submit(on_enter)

    donor_dropdown.observe(update_dashboard, names='value')
    metric_select.observe(update_dashboard, names='value')

    #layout
    display(widgets.VBox([
        widgets.HTML("<h2>WhatsApp Donation Dashboard (Interaction Heterogenity)</h2>"),
        widgets.HBox([donor_search, donor_dropdown, metric_select], layout=widgets.Layout(gap="12px")),
        widgets.HBox([bar_output, lorenz_output], layout=widgets.Layout(gap="20px", align_items='flex-start')),
        summary_output
    ]))
