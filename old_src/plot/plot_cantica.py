import matplotlib.pyplot as plt
import numpy as np

from src.plot.style import PLOTTING_POETRY_HEX, apply_plotting_poetry_palette


def plot_dict(play_dict, y_start=0.8, y_end=0.84):
    apply_plotting_poetry_palette()

    # Extract keys and values
    plays = list(play_dict.keys())
    stats = list(play_dict.values())

    # Determine unique prefix groups
    prefixes = [key[:-2] for key in plays]
    unique_prefixes = sorted(set(prefixes))

    # Assign a unique color to each prefix group
    prefix_to_color = {
        prefix: PLOTTING_POETRY_HEX[i % len(PLOTTING_POETRY_HEX)]
        for i, prefix in enumerate(unique_prefixes)
    }

    # Map each play to its group color
    colors = [prefix_to_color[key[:-2]] for key in plays]

    # Create the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(plays, stats, color=colors)

    # Add labels and title
    plt.xlabel('Play (abbreviations)', fontsize=12)
    plt.ylabel('Compatibility Metrics', fontsize=12)
    plt.title('Compatibility Metric by Play', fontsize=14)
    plt.xticks(rotation=45)

    # Adjust y-axis limits
    plt.ylim(y_start, y_end)

    plt.tight_layout()
    plt.show()
