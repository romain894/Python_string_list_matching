# Python string list matching

Python lib to match similar strings of a list. It relies on SequenceMatcher from difflib to compute the string matching ratios.

## How to use

You can use this matching library with only two lines: one to create the object with the object with the strings to compare, and the other one to run the comparaison and matching process:

```python
# string_names is the list of strings to match
string_names = ["string1", "string2", "..."]
matching = StringMatching(string_names)

# the ratio threshold must be between 0 and 1
# a higher ratio will link less string but with
# a higher similarity
link_ratio_threshold = 0.85
link_ratio_warning = 0 # not implemented for now
cache_ratio_array_path = "the/path/for/cache.npz"
use_cache = True
ratio_array_csv_path = None # not usefull
sort_linked_list_by_len = True
# linked_strings is a list of list of strings
# each sublist contains the strings matched
linked_strings = matching.link_strings(link_ratio_threshold,
                                       link_ratio_warning,
                                       cache_ratio_array_path,
                                       use_cache,
                                       ratio_array_csv_path,
                                       sort_linked_list_by_len)
```

## Optimizations

The program is multithreaded so it can run on different CPU cores to speed up the computation.

If a cache file is given, it allows the program to check if the ratios of the strings in the list was previously computed (it's the longest part). If so, it loads the array and skip this computation. To be usefull, the cache file must be different for each list of strings to match (in case there is).

Romain THOMAS 2023  
Stockholm Resilience Centre
