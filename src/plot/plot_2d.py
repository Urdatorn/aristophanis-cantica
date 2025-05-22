import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def plot_dict_as_points(play_dict, syll_counts, y_start=0.8, y_end=0.84):
    x_vals = []
    y_vals = []
    labels = []
    color_keys = []

    for label, value in play_dict.items():
        if label in syll_counts:
            x_vals.append(syll_counts[label])
            y_vals.append(value)
            labels.append(label)
            color_keys.append(label[:-2])  # Group by label minus last two chars

    # Generate a color for each prefix group
    unique_keys = sorted(set(color_keys))
    color_map = cm.get_cmap('tab20', len(unique_keys))  # categorical colormap
    key_to_color = {key: color_map(i) for i, key in enumerate(unique_keys)}

    # Assign colors
    point_colors = [key_to_color[key] for key in color_keys]

    plt.figure(figsize=(10, 6))
    plt.scatter(x_vals, y_vals, color=point_colors, s=60)

    for x, y, label in zip(x_vals, y_vals, labels):
        plt.text(x, y + 0.001, label, ha='center', va='bottom', fontsize=9)

    plt.xlabel('Syllable Count', fontsize=12)
    plt.ylabel('Compatibility Metric', fontsize=12)
    plt.title('Compatibility vs Syllable Count', fontsize=14)
    plt.ylim(y_start, y_end)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()