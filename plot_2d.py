import matplotlib.pyplot as plt

def plot_dict_as_points(play_dict, y_start=0.8, y_end=0.84):
    # Extract values and indices
    values = list(play_dict.values())
    indices = list(range(len(play_dict)))
    
    # Create a scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(indices, values, color='darkred', s=60)

    # Annotate each point with the play abbreviation
    for i, (label, value) in enumerate(play_dict.items()):
        plt.text(i, value + 0.001, label, ha='center', va='bottom', fontsize=9)

    # Set labels and title
    plt.xlabel('Index in Ordered Dictionary', fontsize=12)
    plt.ylabel('Compatibility Metric', fontsize=12)
    plt.title('Compatibility Metric by Index', fontsize=14)

    # Adjust y-axis limits
    plt.ylim(y_start, y_end)
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()