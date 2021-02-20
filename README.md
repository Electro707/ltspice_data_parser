# LTSpice Data Parser

A Python program, inspired/based off [https://github.com/aryadaroui/LTspice-Data-Export](https://github.com/aryadaroui/LTspice-Data-Export), that parses an LTSpice data file (which is not CSV friendly) and exports either a CSV file or plots the data directly with MatPlotLib.

## NOTE: WIP

As I'm starting from scratch, this is a work in progress. As of this commit here are some supported modes/features:

- File Type (Gets auto-detected): 
    - AC Analysis with frequency and phase
    - Transient Response
    - All above with a single paramatric step/sweep.
    - All above with multiple probing points
- Plotting:
    - Plot everything
    - Plot with a single probe point (as an index from 0 to x)
    - Plot with a single parameter step point

## TODO:
- IMPORTANT: Parse AC analysis data with real/imaginary output instead of frequency/phase
- IMPORTANT: Add CSV output capability
- FUTURE: Create an optional GUI wrapper
