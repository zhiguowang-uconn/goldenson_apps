import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import io
import base64

def load_questions():
    """
    Load questions and options from sriQuestions.csv using pandas.
    Returns a list of dicts, each with 'factor' and 'options'.
    """

    # Build path relative to this file
    data_file = Path(__file__).parent / "data" / "sriQuestions.csv"

    # Read the CSV
    df = pd.read_csv(data_file)

    questions = []
    for _, row in df.iterrows():
        question = {
            "label": row["label"],
            "key": row["keys"],  # name/id for input
            "options": [
                row["Option1"],
                row["Option2"],
                row["Option3"],
                row["Option4"],
                row["Option5"]
            ],
            "weights": row["Weights"]
        }
        questions.append(question)

    return questions


def in_thousands(x, pos):
    return "{:.0f}".format(x / 1000)

def create_spending_chart(bm_data, mix_data, labels):
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plot lines
    ax.plot(labels, bm_data, marker='o', label='Benchmark')
    ax.plot(labels, mix_data, marker='o', label='Integrated')
    
    # X-axis
    ax.set_xlabel('Certainty Level (%)')
    ax.invert_xaxis()  # optional for descending certainty
    
    # Y-axis formatter: show in thousands
    def in_thousands(x, pos):
        return "{:.0f}".format(x / 1000)
    
    ax.yaxis.set_major_formatter(FuncFormatter(in_thousands))
    ax.set_ylabel('Spending ($1,000)')
    
    # Legend and layout
    ax.legend()
    plt.tight_layout()
    
    # Save figure to a PNG in memory
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64