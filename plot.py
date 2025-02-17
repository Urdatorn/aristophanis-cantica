import matplotlib.pyplot as plt

# Data
labels = ['Ach.', 'Eq.', 'V.', 'Nu.']
values = [27.4, 25.6, 24.2, 34.2]
x = range(len(labels))  # Numeric x-axis positions

# Plot
fig, ax = plt.subplots()
ax.plot(x, values, 'bo', label='Data Points')  # Plot points in blue
ax.plot(x, values, 'b--', linewidth=1)  # Dotted line connecting points

# Formatting
ax.set_ylabel('Accentresponsion', fontsize=12)
ax.set_ylim(0, 50)  # Limit y-axis to 30%
ax.set_xticks(x)
ax.set_xticklabels(labels, fontstyle='italic', fontsize=12)
ax.set_yticks(range(0, 41, 5))  # Ticks every 5%
ax.set_title('Accentresponsion per pjäs av Aristofanes', fontsize=14)

plt.savefig('plot.png', dpi=500)

