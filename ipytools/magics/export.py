import os, sys

import json
import urllib2

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from IPython.lib import kernel
from IPython.html.notebookapp import list_running_servers

from IPython.display import display, Javascript

ipython = get_ipython()

def get_notebook_name():
    """
    Fetch current notebook's name through IPython

    Parameters
    ----------
    None

    Return
    ------
    notebook_name : string
        name of currently running notebook

    Notes
    -----
    The python in this function could be replaced with Javascript
    """
    def sess_open(url):
        try:
            urllib2.urlopen(url+'api/sessions')
            return True
        except:
            return False
    load = lambda url: json.loads(urllib2.urlopen(url+'api/sessions').fp.read())
    base = lambda path: os.path.basename(path)
    nbpath = lambda session: base(session['notebook']['path'])
    nbid = lambda session: session['kernel']['id']

    connection_file_path = kernel.get_connection_file()
    connection_file = base(connection_file_path)
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]

    sessions = [load(data['url']) for data in list_running_servers() if sess_open(data['url'])]
    sessions = reduce(list.__add__, sessions) if isinstance(sessions[0], list) else sessions

    notebook_name = [nbpath(sess) for sess in sessions if nbid(sess) == kernel_id]
    if notebook_name:
        return notebook_name[0]
    else:
        sys.stderr.write('No notebook name was found.  Export manually.')
        sys.stderr.flush()

def get_files(directory='~/.ipython/extensions/templates', ext='.tpl'):
    """
    Given a directory, fetch all the files of a certain type;
        present sorted lowest to highest
    Paramters
    --------
    directory : string
        local directory
    ext : string
        file extension to retrieve

    Return
    ------
    all_files : list
        list of all files in sub-directories with given file extension
    """
    all_files = []
    filepath = os.path.expanduser(directory) if directory[0]=='~' else directory
    for root, _dir, files in os.walk(filepath):
        for f in files:
            if f.endswith(ext):
                all_files.append(f)
    all_files.sort()
    return all_files

@magics_class
class ExportMagic(Magics):
    """Magic Class for `%export` magic.  Specifies arguments and argument handling"""
    @magic_arguments()
    @argument(
        'filename', default=get_notebook_name(),
            help='filename passed for export to html'
    )
    @argument(
        '--to', default='html', choices=['custom', 'html', 'latex', 'markdown', 
                                         'notebook', 'pdf', 'python', 'rst', 
                                         'script', 'slides'],
            help='Choose a filetype to convert to'
    )
    @argument(
        '-t', '--template', default=get_files()[0], choices=get_files(),
            help='Choose a .tpl file to format the .ipynb'
    )
    @line_magic
    def export(self, line):
        """`%export` packages and exports the current notebook session

        Running `%export` with no parameters will automatically convert the current
            notebook into html with lexigraphically lowest template in: 

                `~/.ipython/extensions/templates`

        Parameters
        ----------
            filename : str (optional)
                specify file to convert
            --to : str (optional, default='html', ('slides', 'html'))
                specify target file type for conversion
            --t, --template: str (optional)
                specify .tpl file to serve as template

        Examples
        --------
        >>> %export

        >>> %export --to slides --template my_slide_template.tpl

        Todo
        ----
            1 : Add handling for "directory does not exist"
            2 : Add handling for "no custom .tpl exists"
        """


        self._remove_last_cell()
        self._renumber_cells()
        self._save_notebook()
        self._nbconvert(line)


    def _nbconvert(self, line):

        args = self._parse_line(line)   
        command = self._build_command(args)
        filename = args['filename']
        self._rewrite_execution_order(filename)
        ipython.run_cell_magic('bash', line='', cell=command)


    def _build_command(self, args):
        command = 'ipython nbconvert --to {to} "{filename}" --template {template}'.format(**args)

        reveal_prefix = '--reveal-prefix "https://cdn.jsdelivr.net/reveal.js/2.6.2"'
        if args.get('to', False) and args['to'] == 'slides':
            command = ' '.join([command, reveal_prefix])

        return command


    def _format_filename(self, args):
        filename = args['filename']

        if isinstance(filename, list):
            filename = ' '.join([item.strip('"').strip("'") for item in filename])
        else:
            filename = filename.strip('"').strip("'")

        args['filename'] = filename

        if not args['filename'].endswith('.ipynb'): args['filename'] += '.ipynb'
        self.filename = args['filename']
        return args


    def _parse_line(self, line):
        if line in [None, '']:
            line = '"{0}"'.format(get_notebook_name())
        elif line.strip()[0] == '-':
            filename = '"{}"'.format(get_notebook_name())
            line = ' '.join([filename, line])

        args = parse_argstring(self.export, line).__dict__

        args = self._format_filename(args)

        return args


    def _remove_last_cell(self):
        display(Javascript("""
            var cells = $('div.cell'); 
            var nCell = cells.length;
            var last = cells[nCell - 1];
            last.remove()
            """))

    def _renumber_cells(self):
        display(Javascript("""
            var cells = $('div.cell.code_cell');
            var nCell = cells.length;

            for (var i=0; i<nCell; i++){
                var input_prompt = cells[i].getElementsByClassName('prompt input_prompt')
                var output_prompt = cells[i].getElementsByClassName('prompt output_prompt')
                
                input_prompt[0].innerHTML = 'In&nbsp;[' + (i + 1) + ']:'
                
                if (output_prompt.length > 0){
                    output_prompt[0].innerHTML = '' //Out[' + i + ']:
                }
            }
            """))

    def _rewrite_execution_order(self, title):
        data = json.load(open(title))
        count = 1
        for cell in data['cells']:
            if 'execution_count' in cell:
                cell['execution_count'] = count
                count += 1
        json.dump(data, open(title, 'wb'))

    def _save_notebook(self):
        display(Javascript("""
            IPython.notebook.save_checkpoint()
            """))

    @staticmethod
    def _object_to_class(obj):
        if isinstance(obj, type):
            return obj
        elif hasattr(obj, "__class__"):
            return obj.__class__
        else:
            raise ValueError(
                "Given object {0} is not a class or an instance".format(obj))

    @staticmethod
    def _class_name(cls, parts=0):
        """Given a class object, return a fully-qualified name.

        """
        module = cls.__module__
        if module == '__builtin__':
            fullname = cls.__name__
        else:
            fullname = '%s.%s' % (module, cls.__name__)
        if parts == 0:
            return fullname
        name_parts = fullname.split('.')
        return '.'.join(name_parts[-parts:])

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(ExportMagic)
        _loaded = True

_loaded = False