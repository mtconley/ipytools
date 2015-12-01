import matplotlib.pyplot as plt
import mpld3
from IPython.display import HTML, Image, display
from contextlib import contextmanager

from StringIO import StringIO
import sys

class Suppress(StringIO):
    """Context manager to suppress output (stdout and stderr)
    Output is written to buffer

    Example
    ------
    >>> with Suppress() as s:
            print 'ERROR'
    
    >>> s.getvalue()
    """
    def __enter__(self):
        self.tmp_stdout = sys.stdout
        self.tmp_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self
    
    def __exit__(self, type, value, traceback):
        sys.stdout = self.tmp_stdout
        sys.stderr = self.tmp_stderr
        self._remove_newline()
        return self
    
    def _remove_newline(self):
        self.seek(s.len-1)
        last_char = self.read()
        if last_char == '\n':
            self.truncate(self.len-1)

def _slide_tag(image, sentence):
    """HTML formatter for two panel slide

    Parameters
    ---------
    image : unicode
        d3 object to display

    sentence : str
        Plot description and commentary
    """

    html = """
        <div class="slide_container" style="width:840px;">
            <div class="figure_box" style="display:inline-block; float:left;">
                {image}
            </div>
              
            <div class="description_box" style="font-size:18px;padding-top:60px;font-family:Century Gothic;">
                {sentence}
            </div>
        </div>
    """.format(image=image, sentence=sentence)
    display(HTML(html))

@contextmanager
def slide(sentence, ordered=False):
    """
    Instantiate slide with HTML layout.  
    Layout is two panels, left with plot, right with `sentence`

    Parameters
    ----------
    sentence : str, list
        Text to be placed in right panel.  If a list is entered, it will be 
        converted to an HTML list

    ordered : bool (defaul: False)
        If sentence is a list, the list will be ordered.  If `False`, list will
        be unordered

    Example
    -------
    >>> import pandas as pd
    >>> import numpy as np
    >>> data = pd.DataFrame(np.random.randint(0, 10, 100)).cumsum(0)

    >>> html_list = ['this is the first item', 
                   'this is the second item', 
                   'one more for good measure']
    >>> with slide(html_list, True):
            plt.plot(data)
    """
    yield
    image = mpld3.fig_to_html(plt.gcf())
    if isinstance(sentence, list):
        list_type = ['ul', 'ol'][ordered]
        sentence = '<{0}>\n<li>{1}</li>\n</{0}>'.format(
           list_type, '</li>\n<li>'.join(sentence)
        )
    else:
        sentence = '<p>{}</p>'.format(sentence)
    _slide_tag(image, sentence)
    plt.close()

@contextmanager
def mplrc(rcParam, value):
    """
    Context Manager for matplotlib rcParams.  Parameter will be changed wihtin
    context then returned to original value

    Parameters
    ---------
    rcParam : str
        rcParam to change.  Must be in list of plt.rcParams

    value : variant
        value to set rcParam within context

    Examples
    --------
    >>> with mplrc('figure.figsize', (15, 10)):
            plt.plot(data)
    >>>
    """
    if rcParam not in plt.rcParams:
        raise KeyError('rcParam must be in matplotlib.pyplot.rcParams')
    tmp_value = plt.rcParams[rcParam]
    plt.rcParams[rcParam] = value
    yield
    plt.rcParams[rcParam] = tmp_value

def _get_repr(obj):
    """return a formatted repr for a given object

    Parameters
    ----------
    obj : object
        Any object

    Returns
    -------
    string : str
        formatted repr string
    """
    if hasattr(obj, '_repr_html_'):
        return obj._repr_html_()
    else:
        if isinstance(obj, str):
            string = obj
        elif isinstance(obj, unicode):
            string = obj.encode('ascii', 'ignore')
        else:
            string = repr(obj)
        string = string.replace('\n', '<br>')
        string = string.replace(' ', '&nbsp;')
        string = '<p><font face="courier">{}</font></p>'.format(string)
        return string

def hdisplay(*args):
    """horizontal display to compare pandas DataFrames side by side
    
    Parameters
    ----------
    args : parameter list
        list of pandas DataFrames to display
            
    Returns
    -------
    None : `hdisplay` displays HTML

    """
    if args:
        args = list(args)
        opener = "<div style='display:inline-block; float:left; padding-right:10px;'>"
        closer = "</div>"
        arg = args[0]
        string = opener + _get_repr(arg) + closer
        for arg in args[1:]:
            string += opener + _get_repr(arg) + closer
        display(HTML(string))