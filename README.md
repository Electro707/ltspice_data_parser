# LTSpice Data Parser

A Python program, inspired/based off [https://github.com/aryadaroui/LTspice-Data-Export](https://github.com/aryadaroui/LTspice-Data-Export), that parses an LTSpice data file (which is not CSV friendly) and exports either a CSV file or plots the data directly with MatPlotLib.

## NOTE: WIP

As I'm starting from scratch, this is a work in progress. As of this commit here are some supported modes/features:

- File Type: Only an AC Analysis with frequency and phase are supported. 
- Plotting: Code exists for plotting either a single step or multiple steps (for a parameter step), but there is not argument to directly call it

Here are some figure goals/features that I would like to implement to this project, as well as their priority:

- [x] CRITICAL: Parse a non-parameter step file handling (should be simple)
- [ ] IMPORTANT: Parse AC analysis data with real/imaginary output instead of frequency/phase
- [x] IMPORTANT: Parse a transient output
- [x] IMPORTANT: Add arguments to the Python file in order to use some of the internal features (like plotting)
- [ ] IMPORTANT: Add CSV output capability
- [ ] FUTURE: Add parameter step variable input from CLI 
- [ ] FUTURE: Create an optional GUI wrapper
