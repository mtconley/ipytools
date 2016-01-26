

import random, re, sys, time

import matplotlib.pyplot as plt
import mpld3

from contextlib import contextmanager
from datetime import datetime
from IPython.display import HTML, Image, display
from jinja2 import Template
from StringIO import StringIO

from ._presentation_tpl import _template

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
    def __init__(self, file_object=None, fd=1):
        if file_object:
            self.buffer = file_object
        else:
            self.buffer = self

        self.fd = 1

        StringIO.__init__(self)

    def __enter__(self):
        if self.fd in [1, 3]:
            self.tmp_stdout = sys.stdout
            sys.stdout = self.buffer

        if self.fd in [2, 3]:
            self.tmp_stderr = sys.stderr
            sys.stderr = self.buffer
        
        return self
    
    def __exit__(self, type, value, traceback):
        self._remove_newline()
        if self.fd in [1, 3]:
            sys.stdout = self.tmp_stdout

        if self.fd in [2, 3]:
            sys.stderr = self.tmp_stderr
        
        return self
    
    def _remove_newline(self):
        self.buffer.seek(self.len-1)
        last_char = self.buffer.read()
        if last_char == '\n':
            self.buffer.truncate(self.buffer.len-1)

    def __repr__(self):
        return self.buffer.getvalue()

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

    sentence = sentence.replace(' ', '&nbsp;')
    sentence = sentence.replace('\n', '<br>')

    html = """
        <div class="slide_container" style="width:840px;display:inline-block;">
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
def slide(layout=1, buf=None):
    """Instantiate slide with HTML layout
    
    Parameters
    ----------
    layout : int
        Layout id for SlideTemplate factory
        
    buf : filepath or buffer, optional
        Buffer like object for slide to print to, default is None.  
        None will invoke an HTMLbuffer object
    """
    
    try:
        if isinstance(buf, str):
            buf = open(buf, 'wb')
        elif buf is None:
            buf = HTMLBuffer()


        with SubSlideStack() as sub_slides:
            if sub_slides.depth > 2:
                raise ContextError("""Maximum allowable slide depth exceeded.  
                Slide with be ignored.""")
            else:
                with Suppress(buf) as s:
                    yield

        fig = plt.gcf()
        if fig.axes:
            image = mpld3.fig_to_html(fig) 
        else:
            image = ''
                    
        text = buf.getvalue()
        html = _slide_tag(image, text)
        
        sub_slides.push(html)

        plt.close()
        buf.close()
            
    except Exception as e:
        _print_error(e)

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


class Timer(object):
    """Context manager to time the runtime of a set of operations

    Example
    -------
    >>> with Timer() as t:
    ...     time.sleep(1)
    ...
    >>>
    >>> print t.show()
        0:0:1.002276
    >>>
    >>> print t.total_seconds()
        1.002276
    >>>
    >>> print t
        0 Days, 0 Hours, 0 Minutes, 1 Seconds, 2276 Microseconds

    """
    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._runtime = None
        
    def __enter__(self):
        self._start_time = time.time()
        return self
    
    def __exit__(self, type, value, traceback):
        self._end_time = time.time()
        self._runtime = round(self._end_time - self._start_time, 6)
        self._calculate()
        
    def _calculate(self):
        self.seconds = int(self._runtime)
        self.microseconds = int((self._runtime - self.seconds) * 1e6)
        
        self.minutes, self.seconds = divmod(self.seconds, 60)
        self.hours, self.minutes = divmod(self.minutes, 60)
        self.days, self.hours = divmod(self.hours, 24)
        
    def total_seconds(self):
        """return the runtime as a float value in seconds"""
        
        return self._runtime
    
    def show(self):
        """show the runtime in %H:%M%S.%f format"""
        
        timestr = '{hours}:{minutes}:{seconds}.{microseconds:0>6d}'.format(**self.__dict__)
        if self.days:
            timestr = '{days} Days, '.format(self.days) + timestr
        return timestr
    
    def __repr__(self):
        values = [
            '{} Days'.format(self.days),
            '{} Hours'.format(self.hours),
            '{} Minutes'.format(self.minutes),
            '{} Seconds'.format(self.seconds),
            '{} Microseconds'.format(self.microseconds)
        ]
        timestr = ', '.join(values)
        return timestr


class HTMLBuffer(StringIO):
    """Buffer adapter to parse python data to HTML"""
    def write(self, msg):
        msg = repr(msg)
        try:
            msg = eval(msg)
        except Exception as e:
            _print_error(e)
                
        if isinstance(msg, list):
            msg = self._list_to_ol(msg)
        elif isinstance(msg, set):
            msg = self._list_to_ul(msg)
        else:
            msg = msg.replace(' ', '&nbsp;')
            msg = msg.replace('\n', '<br>')
            msg = msg.replace('\t', '&nbsp;' * 4)

        StringIO.write(self, msg)
        
    def _list_to_list(self, msg, list_type):
        msg = """
              <{0}>
                  <li>{1}
                  </li>
              </{0}>
              """.format(
                list_type, '</li>\n<li>'.join(msg)
              )
        return msg
    
    def _list_to_ol(self, msg):
        msg = self._list_to_list(msg, 'ol')
        return msg
    
    def _list_to_ul(self, msg):
        msg = self._list_to_liiiist(msg, 'ul')
        return msg


class SlideStack(object):
    _shared_state = {}
    instance = False

    def __init__(self, *slides):
        if not self._shared_state:
            self.__class__.instance = True
            self.stack = []
            
        for slide_html in slides:
            self.stack.append(slide_html)
            
    def push(self, slide_html):
        self.stack.append(slide_html)
        
    def destroy(self):
        self.__class__.instance = False
        self._shared_state = {}
        self.__class__._shared_state = {}

    def __getattr__(self, name):
        if name == '_shared_state':
            return self._shared_state
        else:
            return self._shared_state.get(name, None)
        
    def __setattr__(self, name, value):
        if name == '_shared_state':
            return self._shared_state
        else:
            self._shared_state[name] = value
        
    def __len__(self):
        return len(self.stack)

    def __getitem__(self, item):
        return self.stack[item]
        
    def __repr__(self):
        return repr(self.stack)


class SubSlideStack(object):
    _shared_state = {}
    depth = 0

    def __init__(self, *slides):
        if not self._shared_state:
            self.stack = []
            
        for slide_html in slides:
            self.stack.append(slide_html)
            
    def push(self, slide_html):
        if self.depth:
            self.stack.append(slide_html)
        else:
            text = '{0}\n{1}'.format(slide_html, self.ravel())
            SlideStack(text)
        
    def destroy(self):
        self.__class__.depth = 0
        self._shared_state = {}
        self.__class__._shared_state = {}

    def ravel(self):
        if self.stack:
            html = '\n</section>\n<section>\n    '.join(self.stack)
            return '<section>\n    {}\n</section>\n'.format(html)
        else:
            return ''
        
    def __enter__(self):
        self.__class__.depth += 1
        return self
    
    def __exit__(self, type, value, traceback):
        self.__class__.depth -= 1
        

    def __getattr__(self, name):
        if name == '_shared_state':
            return self._shared_state
        else:
            return self._shared_state.get(name, None)
        
    def __setattr__(self, name, value):
        if name == '_shared_state':
            return self._shared_state
        else:
            self._shared_state[name] = value
        
    def __len__(self):
        return len(self.stack)

    def __getitem__(self, item):
        return self.stack[item]
        
    def __repr__(self):
        return repr(self.stack)
    



class ContextError(Exception):
    def __init__(self, message=None):
        
        err_str = 'Cannot create object within existing object context'
        if message:
            err_str = '{0}\n\n\t{1}'.format(err_str, message)
            
        Exception.__init__(self, err_str)


class Presentation(object):
    name = None
    html = None
    presentation = None
    cdn = 'https://cdn.jsdelivr.net/reveal.js'
    version = '2.6.2'
    
    def __init__(self, name=None, cdn=None, version=None):
        self._name_presentation(name)
        self.cdn = cdn or self.cdn
        self.version = version or self.version
        
    @staticmethod
    def _make_salt():
        chars = range(48, 58) + range(97, 97 + 26)
        salt_arr = [chr(random.choice(chars)) for _ in range(12)]
        salt = ''.join(salt_arr)
        return salt
    
    @staticmethod
    def _now():
        dt = datetime.now()
        now = dt.strftime('%Y%m%d%H%M%S')
        return now
    
    def _name_presentation(self, name):
        if name:
            self.name = name
        else:
            salt = self._make_salt()
            now = self._now()
            self.name = 'presentation_{}_{}.slides.html'.format(salt, now)
            
    def save(self):
        with open(self.name, 'wb') as f:
            f.write(self.html)

    def build_html(self):
        template = Template(_template)
        html = template.render(presentation=self.presentation, cdn=self.cdn, version=self.version)
        self.html = html
    
    def __enter__(self):
        if SlideStack.instance:
            msg = 'Presentation object already exists'
            raise ContextError(msg)

        self.presentation = SlideStack()
        return self
    
    def __exit__(self, type, value, traceback):
        self.build_html()
        self.save()
        self.presentation = self.presentation.stack
        SlideStack().destroy()

    def __len__(self):
        return len(self.presentation)

    def __getitem__(self, item):
        return self.presentation[item]

    def _repr_html_(self):
        for slide in self.presentation:
            display(HTML(slide))
