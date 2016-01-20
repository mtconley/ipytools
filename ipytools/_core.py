import matplotlib.pyplot as plt
import mpld3
from IPython.display import HTML, Image, display
from contextlib import contextmanager

from StringIO import StringIO
import sys
import re

def _print_error(e):
    """Traceback formatter for handled exceptions

    Parameters
    ----------
    e : Exception
        Exception caught in try/except clause

    Example
    -------
    try:
        raise Exception
    except Exception as e:
        _print_error(e)

    """
    string = '\n\t'.join([
            '{0}', # Exception Type
            'filename: {1}', # filename
            'lineno: {2}\n']) # lineno of error

    fname = sys.exc_info()[2].tb_frame.f_code.co_filename
    tb_lineno = sys.exc_info()[2].tb_lineno

    args = (repr(e), fname, tb_lineno)
    sys.stderr.write(string.format(*args))
    sys.stderr.flush()


def _is_notebook():
    try:
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.kernel.zmq.zmqshell import ZMQInteractiveShell as notebook
        from IPython.terminal.interactiveshell import TerminalInteractiveShell as shell
        if InteractiveShell.initialized():
            ip = get_ipython()
            if isinstance(ip, notebook):
                return True
            elif isinstance(ip, shell):
                return False
            else:
                raise Exception('Wrong Shell')
        else:
            return False
    except Exception as e:
        _print_error(e)
        return False

class Suppress(StringIO):
    """Context manager to suppress output (stdout and stderr)
    Output is written to buffer

    Example
    ------
    >>> with Suppress() as s:
            print 'ERROR'
    
    >>> s.getvalue()
        'ERROR'
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
        self.seek(self.len-1)
        last_char = self.read()
        if last_char == '\n':
            self.truncate(self.len-1)

class Redirect(object):
    tmp_console_out = sys.__stdout__
    tmp_console_err = sys.__stderr__
    tmp_notebook_out = sys.stdout
    tmp_notebook_err = sys.stderr
    tmp_file_out = None
    tmp_file_err = None
    tmp_buffer_out = None
    tmp_buffer_err = None
    
    streams = {
        'console': {'stderr': 'console_err', 'stdout': 'console_out'},
        'file': {'stderr': 'file_err', 'stdout': 'file_out'},
        'ipynb': {'stderr': 'notebook_err', 'stdout': 'notebook_out'},
        'buffer': {'stderr': 'buffer_err', 'stdout': 'buffer_out'}
    }
    
    def __init__(self, stream_name=None):
        """Context Manager for redirecting stdout and stderr
        
        Parameters
        ----------
        stream_name : str
            Stream to redirect to.  Must be chosen from 'console', 'file', 'buffer'
            'ipynb' is always assumed as primary stream reinstate
            'file' always outputs to stdout.log and stderr.log in the current
                working directory
            
            
            
        Example
        -------
        >>> with Redirect('file') as r:
                print 'Something to redirect'
                
        >>> open('stdout.log').read()
        ... 'Something to redirect'
        
        """

        if stream_name and stream_name in self.streams:
            self.stream_name = stream_name
            self.stream_out = None
            self.stream_err = None
        else:
            choices = '"\n\t"'.join(self.streams.keys())
            response = 'Choose one of the following streams:\n\t"{}"'
            response = response.format(choices)
            raise ValueError(response)
            
    def __enter__(self):
        self.new_stream = self.streams[self.stream_name]
        sys.stdout = eval('self.open_{}()'.format(self.new_stream['stdout']))
        sys.stderr = eval('self.open_{}()'.format(self.new_stream['stderr']))
        
        self.stream_out = sys.stdout
        self.stream_err = sys.stderr
        return self
            
    
    def __exit__(self, type, value, traceback):
        exec 'self.close_{}()'.format(self.new_stream['stdout'])
        exec 'self.close_{}()'.format(self.new_stream['stderr'])
        
        if not sys.stdout.closed:
            sys.stdout.flush()
            
        if not sys.stderr.closed:
            sys.stderr.flush()
        
        sys.stdout = self.tmp_notebook_out
        sys.stderr = self.tmp_notebook_err
        
        self.stream_out = None
        self.stream_err = None
    
    def open_console_out(self):
        return self.tmp_console_out
    
    def open_console_err(self):
        return self.tmp_console_err
    
    def open_notebook_out(self):
        return self.tmp_notebook_out
    
    def open_notebook_err(self):
        return self.tmp_notebook_err
    
    def open_file_out(self):
        self.tmp_file_out = open('stdout.log', 'wb')
        return self.tmp_file_out
    
    def open_file_err(self):
        self.tmp_file_err = open('stderr.log', 'wb')
        return self.tmp_file_err
    
    def open_buffer_out(self):
        self.tmp_buffer_out = StringIO()
        return self.tmp_buffer_out
    
    def open_buffer_err(self):
        self.tmp_buffer_err = StringIO()
        return self.tmp_buffer_err
    
    def close_console_out(self):
        pass
    
    def close_console_err(self):
        pass
    
    def close_notebook_out(self):
        pass
    
    def close_notebook_err(self):
        pass
    
    def close_file_out(self):
        self.tmp_file_out.close()
    
    def close_file_err(self):
        self.tmp_file_err.close()
    
    def close_buffer_out(self):
        # Leave buffer open to access later
        pass
        # self.tmp_buffer_out.close()
    
    def close_buffer_err(self):
        # Leave buffer open to access later
        pass
        # self.tmp_buffer_err.close()

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
    return html

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
    display(HTML(html))
    plt.close()

@contextmanager
def mplrc(rcParam, value):
    """
    Context Manager for matplotlib rcParams.  Parameter will be changed wihtin
    context, then returned to original value.

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



def get_classname(instance_object):
    """Return the class name of some instance object

    Parameters
    ----------
    instance_object : object
        the instance object to inspect

    Returns
    -------
    classname : str
        classname of instance_object

    Examples
    --------
    >>> from sklearn.ensemble import RandomForestClassifier
    >>> from sklearn.linear_model import LinearRegression
    >>> classifiers = [
    ...     RandomForestClassifier(), 
    ...     LinearRegression()
    ... ]
    >>> for clf in classifiers:
    ...     print get_classname(clf)
    ...
        RandomForestClassifier
        LinearRegression

    """
    pattern = "<class '(.*)'>"
    classname = re.findall(pattern, str(type(instance_object)))
    classname = classname[0] if len(classname) else ''
    classname = classname.split('.')[-1]
    return classname if len(classname) else None