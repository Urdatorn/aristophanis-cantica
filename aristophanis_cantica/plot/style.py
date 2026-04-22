from cycler import cycler
import matplotlib.pyplot as plt


PLOTTING_POETRY_HEX = [
    "#4c72b0",
    "#dd8452",
    "#55a868",
    "#c44e52",
    "#8172b3",
    "#937860",
    "#da8bc3",
    "#8c8c8c",
    "#ccb974",
    "#64b5cd",
]


PLOTTING_POETRY_RGB = [
    (76 / 255, 114 / 255, 176 / 255),
    (221 / 255, 132 / 255, 82 / 255),
    (85 / 255, 168 / 255, 104 / 255),
    (196 / 255, 78 / 255, 82 / 255),
    (129 / 255, 114 / 255, 179 / 255),
    (147 / 255, 120 / 255, 96 / 255),
    (218 / 255, 139 / 255, 195 / 255),
    (140 / 255, 140 / 255, 140 / 255),
    (204 / 255, 185 / 255, 116 / 255),
    (100 / 255, 181 / 255, 205 / 255),
]


def apply_plotting_poetry_palette():
    """Apply the Plotting Poetry Proceedings palette and font defaults."""
    plt.style.use("default")
    plt.rcParams["axes.prop_cycle"] = cycler(color=PLOTTING_POETRY_HEX)
    plt.rcParams["figure.dpi"] = 600
    plt.rcParams["savefig.dpi"] = 600
    plt.rcParams["font.size"] = 18
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = [
        "cmr10",
        "Computer Modern Roman",
        "CMU Serif",
        "DejaVu Serif",
    ]
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["mathtext.rm"] = "cmr10"
    plt.rcParams["mathtext.it"] = "cmmi10"
    plt.rcParams["mathtext.bf"] = "cmb10"
    plt.rcParams["axes.formatter.use_mathtext"] = True
    return PLOTTING_POETRY_HEX
