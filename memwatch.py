import argparse
import linecache
import psutil
import sys

from collections import OrderedDict


# http://goo.gl/zeJZl
def human2bytes(s):
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
    1073741824
    """
    symbols = 'BKMGTPEZY'
    if unicode(s).isnumeric():
        return int(s)
    letter = s[-1:].strip().upper()
    num = float(s[:-1]) # raises ValueError if not valid
    assert letter in symbols
    i = symbols.index(letter)
    return int((1 << (i*10)) * num)

# http://goo.gl/zeJZl
def bytes2human(n, format="%(value)i%(symbol)s"):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)


class ConditionalException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class DieWhen(object):
    """
    Raises a ConditianalException when memory conditions occur
    such as rss > 1M

    :param maxrss:
    :param maxvms:
    """
    
    # exception conditions
    # name, func, error_message
    func_lookup=[
        ('maxrss', lambda dw: dw.p.memory_info().rss > dw.maxrss, 'RSS Exceeded {maxrss} bytes [{human_maxrss}]'),
        ('maxvms', lambda dw: dw.p.memory_info().vms > dw.maxvms, 'VMS Exceeded {maxvms} bytes [{human_maxvms}]'),
        ('maxpc',  lambda dw: dw.p.memory_percent() > dw.maxpc, None),
        ('minvm',  lambda dw: -1, None),
        ('minphy', lambda dw: -1, None),
    ]

    def __init__(self, **kwargs):
        self.kwargs=kwargs
        self.p = psutil.Process()
        self.killfuncs = []  # func, failure_message

        for name, die_func, msg in DieWhen.func_lookup:
            value=kwargs.get(name, 0)
            setattr(self, name, value)
            self.kwargs['human_%s' % name] = bytes2human(value)
            if value:
                die_func.__name__ = 'check_%s' % name
                msg = msg or '%s failed' % die_func.__name__
                self.killfuncs.append([die_func, msg])



    # http://pymotw.com/2/sys/tracing.html#sys-tracing
    # http://www.dalkescientific.com/writings/diary/archive/2005/04/20/tracing_python_code.html
    def trace(self, frame, event, arg):
        co = frame.f_code
        func_name = co.co_name
        if func_name == 'write':
            # Ignore write() calls from print statements
            return

        elif event == 'line' and self.kwargs.get('linetrace'):
            lineno = frame.f_lineno
            filename = frame.f_globals["__file__"]
            if filename == "<stdin>":
                filename = "traceit.py"
            if (filename.endswith(".pyc") or
                filename.endswith(".pyo")):
                filename = filename[:-1]
            name = frame.f_globals["__name__"]
            line = linecache.getline(filename, lineno)
            print("%s:%s: %s" % (name, lineno, line.rstrip()))

        for f, msg in self.killfuncs:
            if f(self):
                msg=msg.format(**self.kwargs)
                raise ConditionalException(msg)

        return self.trace

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--maxrss', action='store', default=0)
    parser.add_argument('-v', '--maxvms', action='store', default=0)
    parser.add_argument('-p', '--maxpc', action='store', default=0)
    parser.add_argument('-P', '--minphy', action='store', default=0)
    parser.add_argument('-V', '--minvm', action='store', default=0)
    parser.add_argument('-L', '--linetrace', action='store_true')

    args, script_args = parser.parse_known_args()
    arg_dict =vars(args)    
    if not any(arg_dict.values()):
        print parser.print_help()
    else:
        bytes_kwargs = { k: human2bytes(arg_dict.get(k)) for k in ['maxrss', 'maxvms', 'minphy', 'minvm'] }
        dw = DieWhen(
            maxpc=args.maxpc,
            linetrace=args.linetrace,
            **bytes_kwargs)

        if not script_args:
            print('Specify script')
            sys.exit(1)

        script=script_args[0]
        with open(script) as f:
            sys.argv = script_args
            sys.settrace(dw.trace)
            try:
                exec(f, None, None)
            except ConditionalException, e:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                linecache.checkcache(filename)
                line = linecache.getline(filename, lineno, f.f_globals)
                print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)


