import matplotlib.pyplot as plt
import matplotlib.font_manager
import numpy as np
import seaborn as sns


fontsize = 9

# Hack needed because it somehow doesn't index all my fonts otherwise
_all_fonts = matplotlib.font_manager.findSystemFonts()
for font in _all_fonts:
	try:
		matplotlib.font_manager.fontManager.addfont(font)
	except:
		pass

font = {"font.size" : 9,
        "font.family" : "Linux Libertine",
		"legend.title_fontsize" : 9}

titlefont = {"fontsize": 10, 
             "fontweight": "bold"}

bar_label_styles = {"fontsize": 8,
					"color": (0,0,0,0.6)}

boxplot_styles = {
	"whiskerprops" : {"linewidth":.5}, 
	"boxprops"  : {"linewidth":.5},
	"capprops" : {"linewidth":.5}, 
	"medianprops" : {"linewidth":.5, "color":(0,0,0)},
	"whis" : (0,100), 
}

figwidth = 3.3333

legend =  {"loc": "upper right", 
           "fontsize": fontsize, 
           "handletextpad": .3, 
           "borderpad": 0.3, 
           "columnspacing": 0.6, 
           "labelspacing": 0.3, 
           "handlelength": 1.25}

palette = "terrain"

def setup():
	plt.rcParams.update({"pdf.fonttype": 42})
	plt.rcParams.update(font)

	fig, ax = plt.subplots()
	fig.set_figwidth(figwidth)

	sns.set_theme(palette=palette)
	colors = sns.color_palette(palette=palette)
	sns.set_style("whitegrid")

	# Choosing the theme above seems to overwrite some font properties again,
	# so we need to set it a second time here.
	plt.rcParams.update(font)

	return fig, ax, colors


def mean(x):
	return np.mean(np.array(x, dtype='float'))

def stddev(x):
	return np.std(np.array(x, dtype='float')) 

def stddev_perc(x):
	return stddev(x)*100 / mean(x)
