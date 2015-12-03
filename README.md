#ipytools
A suite of tools to extend IPython notebook

##Example
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from ipytools import mplrc, hdisplay

with mplrc('figure.figsize', (12, 4)):
    fig, axes = plt.subplots(1, 2)
    sns.distplot(np.random.beta(20, 600, 1000), bins=50, ax=axes[0])
    sns.heatmap(np.random.randn(25).reshape((5, 5)), ax=axes[1])
    plt.tight_layout()

data_1 = pd.DataFrame(np.random.randint(0, 10, 50).reshape((10, 5)))
data_2 = pd.DataFrame(np.random.randint(0, 10, 50).reshape((10, 5)))
data_3 = pd.DataFrame(np.random.randint(0, 10, 50).reshape((10, 5)))

hdisplay(data_1, data_2, data_3)
```
##Dependencies
This tool is designed for use with ipython notebook.  `IPython` must be installed.  `mpld3` must also be installed for full functionality.

##Installation
    git clone https://github.com/mtconley/ipytools.git
    python setup.py install

Installation will place files inside the local `.ipython` directory 