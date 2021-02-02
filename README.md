# MonteCarloRetirement
Performs a configurable number of Monte Carlo experiments to determine success/failure rates for various investment scenarios.

Variables that are modeled statistically:
    Asset classes
    Asset Mixes (a portfolio of asset classes)
    Inflation
    Social Security cost of living adjustments (a.k.a. COLA)
    Spend decay (how much less a person will spend in retirement. American Experss estimates a 2%/yr reduction

All asset classes and inflation are modeled using covariance (with each other)

The typical user flow is:
  1) Create a new scenario and fill out the form
  2) Save and run the scenario
  
Definition of terms:
The tool assumes that a typical user will work a full time, career job. After leaving the career job at "retirement age", the user may take a new "retirement job". "Full retirement" occurs when the user no longer works. NB: these are all independent of when the user takes social security
  
An alternative flow is to fill out a scenario and perform a "run all". This will run the scenario using EVERY asset class and asset mix. The results will be written to a file called "output.csv", which can be opened by Excel for examination.
