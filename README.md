# memwatch
Trace and kill a python app if memory usage exceeds some amount.

Use in conjunction with ulimit to find memory leaks.

Example
-------
```python -mmemwatch -r40M eat_128mb.py```

Runs the script with 40MB of RSS memory available.

If you are working with a leaky program it is best to use 'ulimit' on Linux or OSX to stop the process in case memwatch cannot catch it:


```bash
ulimit -v`calc 1024*1024`
python -mmemwatch -r40M eat_128mb.py
```

In the example above ulimit is set to 1GB in case something goes really wrong, memwatch is still set to 40mb.


Usage
-----

```
usage: memwatch.py [-h] [-r MAXRSS] [-v MAXVMS] [-p MAXPC] [-P MINPHY]
                   [-V MINVM] [-L]

optional arguments:
  -h, --help            show this help message and exit
  -r MAXRSS, --maxrss MAXRSS
  -v MAXVMS, --maxvms MAXVMS
  -p MAXPC, --maxpc MAXPC
  -P MINPHY, --minphy MINPHY
  -V MINVM, --minvm MINVM
  -L, --linetrace
  ```
  
memwatch accepts G, M, K suffixes for memory sizes, while ulimit works with Kilobytes.
  
  
Thanks
------
  
Information was used from various stack overflow posts, PyMOTW and dalkescientific - see code for links to sources.
