"Measures how equally donor and contacts contribute to conversations"

#Imports datasets like messages and donations
from dataloader import *     
#Imports helper for saving figures and adding notes           
from functions.pic_notes_save import * 

def compute_interaction_balance(df, donor_id):
    #for each conversation calculates total words sent by donor and by contacts
    records = []
    for cid, group in df.groupby("conversation_id"):
        w_donor = group.loc[group["sender_id"] == donor_id, "word_count"].sum()
        w_contacts = group.loc[group["sender_id"] != donor_id, "word_count"].sum()
        total = w_donor + w_contacts
        #bias = 0.5 - (donor_words / total_words) ,if no words NaN
        bias = np.nan if total == 0 else 0.5 - (w_donor / total)
        #stores metrics for this conversation
        records.append({
            "conversation_id": cid,
            "words_sent_by_donor": int(w_donor),
            "words_sent_by_contacts": int(w_contacts),
            "bias": float(bias) if not np.isnan(bias) else np.nan
        })
    return pd.DataFrame(records)


def show_interaction_balance_dashboard():
    donor_ids = sorted(donations["donor_id"].unique())

    #Donor input text
    donor_input = widgets.Text(
        placeholder="Type donor ID",
        description="Donor:",
        layout=widgets.Layout(width="300px")
    )
    donor_dropdown = widgets.Dropdown(
        options=donor_ids,
        layout=widgets.Layout(width="250px")
    )

    #View selector
    view_radio = widgets.RadioButtons(
        options=[
            ("Bias Distribution + Summary", "bias_summary"),
            ("Per Chat Word Comparison", "per_chat")
        ],
        description="View:",
        layout=widgets.Layout(width="300px")
    )

    #outputs
    chart_output = widgets.Output()
    summary_output = widgets.Output()
    summary_output.layout.display = "block"
    donor_data_cache = {}

    #dynamically filters donor dropdown as user types
    def filter_dropdown(change):
        text = change["new"].strip().lower()
        if not text:
            donor_dropdown.options = donor_ids
        else:
            matches = [d for d in donor_ids if text in str(d).lower()]
            donor_dropdown.options = matches if matches else ["No match"]

    donor_input.observe(filter_dropdown, names="value")


    def compute_donor_data(donor):
        #extracts all messages linked to this donor id
        donor_msgs = messages[messages["donation_id"].isin(
            donations.loc[donations["donor_id"] == donor, "donation_id"]
        )].copy()

        if donor_msgs.empty:
            return None, "No messages for this donor."

        balance_df = compute_interaction_balance(donor_msgs, donor)
        balance_df = balance_df.dropna(subset=["bias"])
        if balance_df.empty:
            return None, "No valid bias data for this donor."

        return balance_df, None

    #draws chart depending on selected view
    def render_view(change=None):
        chart_output.clear_output(wait=True)

        donor = donor_input.value.strip() or donor_dropdown.value
        if donor not in donor_data_cache:
            summary_output.layout.display = "none"
            with chart_output:
                display(HTML("<b style='color:orange;'>Please load a donor first.</b>"))
            return

        balance_df = donor_data_cache[donor]
        view_choice = view_radio.value

        if view_choice == "bias_summary":
            summary_output.layout.display = "block"

            #view1 = Bias Distribution and Summary
            with chart_output:
                fig, ax = plt.subplots(figsize=(6, 5))
                ax.hist(balance_df["bias"], bins=20, color="skyblue", edgecolor="black")
                ax.axvline(0, color="red", linestyle="--", label="Perfectly Balanced (0)")
                ax.set_xlim(-0.5, 0.5)
                ax.set_title(f"Interaction Balance Distribution — Donor {donor}")
                ax.set_xlabel("Bias")
                ax.set_ylabel("Number of Chats")
                ax.legend()
                ax.grid(alpha=0.3)
                plt.tight_layout()
                add_save_and_note_controls(fig, donor, "ALL", "interactionbalance-bias")
                plt.show()

            with summary_output:
                summary_output.clear_output(wait=True)
                avg_bias = balance_df["bias"].mean()
                median_bias = balance_df["bias"].median()
                #classifies overall style based on average bias
                balance_summary = (
                    "Balanced" if abs(avg_bias) < 0.05
                    else "Donor Dominant" if avg_bias < 0
                    else "Contact Dominant"
                )

                display(HTML(f"""
                <div style='background:#f9f9f9;padding:12px;border-radius:8px;width:320px;'>
                    <h4>Interaction Balance Summary</h4>
                    <p><b>Average Bias:</b> {avg_bias:.3f}</p>
                    <p><b>Median Bias:</b> {median_bias:.3f}</p>
                    <p><b>Style:</b> {balance_summary}</p>
                    <p><small>Bias = 0 means Balanced<br>Bias < 0 means Donor sends more<br>Bias > 0 means Contacts send more</small></p>
                </div>
                """))

        elif view_choice == "per_chat":
            summary_output.layout.display = "none"

            #view2= per chat word comparison
            with chart_output:
                sorted_df = balance_df.sort_values("bias")
                fig, ax = plt.subplots(figsize=(max(8, len(sorted_df)*0.4), 5))
                #Two bars per chat, donor vs contacts
                x = np.arange(len(sorted_df))
                width = 0.4
                ax.bar(x - width/2, sorted_df["words_sent_by_donor"], width, label="Donor", color="mediumseagreen")
                ax.bar(x + width/2, sorted_df["words_sent_by_contacts"], width, label="Contacts", color="orange")
                #label chats on x-axis
                ax.set_xticks(x)
                short_labels = [str(cid)[:8] + "..." if len(str(cid)) > 8 else str(cid)
                                for cid in sorted_df["conversation_id"]]
                ax.set_xticklabels(short_labels, rotation=45, ha="right")
                #Axis titles and grid
                ax.set_ylabel("Total Words Sent")
                ax.set_title(f"Per-Chat Word Exchange — Donor {donor}")
                ax.legend()
                ax.grid(axis="y", alpha=0.3)
                plt.tight_layout()
                add_save_and_note_controls(fig, donor, "ALL", "interactionbalance-perchat")
                plt.show()

    #loads data for the selected donor and triggers rendering
    def load_donor(_=None):
        donor = donor_input.value.strip() or donor_dropdown.value
        chart_output.clear_output(wait=True)
        summary_output.clear_output(wait=True)

        if donor not in donor_ids:
            summary_output.layout.display = "none"
            with chart_output:
                display(HTML(f"<b style='color:red;'>Donor '{donor}' not found.</b>"))
            return

        balance_df, msg = compute_donor_data(donor)
        if msg:
            summary_output.layout.display = "none"
            with chart_output:
                display(HTML(f"<b style='color:orange;'>{msg}</b>"))
            return

        donor_data_cache[donor] = balance_df
        render_view()

    #Reactive Updates
    donor_input.on_submit(load_donor)
    donor_dropdown.observe(load_donor, names='value')
    view_radio.observe(render_view, names='value')

    #Layout
    display(widgets.VBox([
        widgets.HTML("<h2>Interaction Balance Dashboard</h2>"),
        widgets.HBox([donor_input, donor_dropdown], layout=widgets.Layout(gap="10px")),
        view_radio,
        widgets.HBox([chart_output, summary_output], layout=widgets.Layout(gap="20px", align_items="flex-start"))
    ]))
