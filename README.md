#A few tools to help me with my astronomy

This package introduces a few odds and adds to simplify stuff. Contributions and suggestion our welcome.

##Listing

1. `amdanlyze.py`      - Class for dealing analyzing Absorption Measure Distributions. It accept a fit result output from the `fitter`, and the output of `genXstarGrid` for ionic fraction modeling in a thin shell model.
2. `appdata`           - Directory containing physics for apps, like oscillator strength s and cross sections.
3. `binpeak`           - Utility function for creating and anlyzing histograms generated.
4. `ccf`               - Use executeable `iccf.py` inside. Utility for calculating and analyzing cross correlations.
5. `crossSections.py`  - Not really done as I moved to `Chianti`. Class for dealing with cross sections.
6. `fitshandler.py`    - Handler for common X-rays FITS files. Tested only with Chandra and XMM FITS files, though should work with any compliant FITS files.
7. `fitter`            - Package for fitting data, plotting, error calculation and so forth. Currently needs mainly parallelaztion. Currently support XSPEC basically through the Python interface (if you have both), but that needs work as well for faster integration.
8. `fitterGui`         - A graphical suite for interacting with the fitter, so can use XSPEC and any other model. Run with `fitter_gui.py`.
9. `genXstarGrid`      - Generate a Xi grid of thin shell models with XSTAR, to use for ionic fraction calculations in plasma.
10. `interpolations.py`- Implements a Curve class (vector of points that automatically extends to infinity) and, surprisingly, interpolations to make extensions and add missing data to vectors. Currently only Linear.
11. `lc.py'            - Class for representing and analyzing a lightcurve.
12. `models'           - models for the `fitter`. Currently supports single tables (not a model), analytical functions, XSPEC integration, and an ion based absorption model.
13. `plotInt.py'       - Suite for plotting, auto-annotating, draggeable legend and so forth. Annotation placement needs work.
14. `randomizers.py`   - Just some wrappers to make creating various random vactors easy.
15. `staterr.py`       - Implementation of a confidence interval search (given a measure, and delta goodness). Could parallelize this as well.
16. `utils.py`         - Stuff like Roman numeral conversion, n-wsie iteration, finding closest in a list etc...
