from dataloader import *

def add_save_and_note_controls(fig, donor_id, chat_id, analysis_type, extra_tag=""):
    save_btn = widgets.Button(description="Save Figure", button_style="success")
    note_text = widgets.Text(placeholder="Write a note...")
    note_btn = widgets.Button(description="Add Note", button_style="info")
    output = widgets.Output()

    #Chat prefix (first part of chat_id or 'ALL')
    chat_prefix = str(chat_id)[:8] if chat_id not in ["ALL", None] else str(chat_id)

    #Generates filename (based on analysis type)
    def get_filename():
        if analysis_type.lower() == "gini":
            return f"{donor_id}-{chat_prefix}-gini{('-' + extra_tag) if extra_tag else ''}.png"
        elif analysis_type.lower() == "burstiness":
            if extra_tag:  # for raster-overall types
                return f"{donor_id}-{chat_prefix}-burstiness-raster-{extra_tag}.png"
            else:  # single chat
                return f"{donor_id}-{chat_prefix}-burstiness.png"
        elif analysis_type.lower() == "heatmap":
            return f"{donor_id}-{chat_prefix}-heatmap.png"
        elif analysis_type.lower() == "activecontacts":
            return f"{donor_id}-{chat_prefix}-activecontacts.png"
        elif analysis_type.lower() == "dailywords":
            return f"{donor_id}-{chat_prefix}-dailywords.png"
        else:
            return f"{donor_id}-{chat_prefix}-{analysis_type}.png"

    #single global notes file for all donors and analyses
    NOTES_FILE = OUTPUT_DIR / "analysis_notes.txt"

    #Saves figure
    def save_fig(_):
        filepath = OUTPUT_DIR / get_filename()
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        with output:
            output.clear_output()
            display(HTML(f"<b style='color:green;'>Saved figure as {filepath.resolve()}</b>"))

    #Appends notes
    def add_note(_):
        text = note_text.value.strip()
        if text:
            try:
                with NOTES_FILE.open("a", encoding="utf-8") as f:
                    f.write(f"[{donor_id}][{analysis_type}][{chat_id}]{f'-{extra_tag}' if extra_tag else ''} {text}\n")
                with output:
                    output.clear_output()
                    display(HTML(f"<b style='color:blue;'>Added note to {NOTES_FILE.resolve()}</b>"))
                note_text.value = ""
            except Exception as e:
                with output:
                    output.clear_output()
                    display(HTML(f"<b style='color:red;'>Error writing note: {e}</b>"))

    save_btn.on_click(save_fig)
    note_btn.on_click(add_note)

    display(widgets.HBox([save_btn, note_text, note_btn], layout=widgets.Layout(gap="8px")))
    display(output)
