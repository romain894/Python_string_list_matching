# Python string list matching

Python lib to match similar strings of a list. It relies on SequenceMatcher from difflib to compute the string matching ratios.

## Optimizations

The program is multithreaded so it can run on different CPU cores to speed up the computation.

If a cache file is given, it allows the program to check if the ratios of the strings in the list was previously computed (it's the longest part). If so, it loads the array and skip this computation. To be usefull, the cache file must be different for each list of strings to match (in case there is).

Romain THOMAS 2023  
Stockholm Resilience Centre
