#ipytools
A suite of tools to extend IPython notebook

##Example
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from ipytools import slide, mplrc, hdisplay

with mplrc('figure.figsize', (12, 4)):
    fig, axes = plt.subplots(1, 2)
    sns.distplot(np.random.beta(20, 600, 1000), bins=50, ax=axes[0])
    sns.heatmap(np.random.randn(25).reshape((5, 5)), ax=axes[1])
    plt.tight_layout()
```
