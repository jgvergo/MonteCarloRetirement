# MonteCarloRetirement
Performs a configurable number of Monte Carlo experiments to determine success/failure rates for various investment scenarios.

Variables that are modeled statistically:
- Asset classes 
- Asset Mixes (a portfolio of asset classes)
- Inflation
- Social Security cost of living adjustments (a.k.a. COLA)
- Spend decay (how much less a person will spend in retirement year over year. American Express estimates a 2%/yr reduction)

All asset classes and inflation are modeled using covariance (with each other)

The typical user flow is:
  1) Create a new scenario and fill out the form
  2) Save and run the scenario
  
Definition of terms

- The tool assumes that a typical user will work a full time, career job. After leaving the career job at "retirement age", the user may take a new "retirement job". "Full retirement" occurs when the user no longer works. NB: these are all independent of when the user takes social security
- An alternative flow is to fill out a scenario and perform a "run all". This will run the scenario using EVERY asset class and asset mix.

At this time, new Asset Classes are ignored and may cause errors. If a new asset class is desired, please contact John and be prepared to supply historica data for the new asset class(es).

To run the program locally:
1. Make sure all required packages are installed
2. In the directory of the program
   1. Open a terminal window and run 'redis-server'
   2. Open a terminal window and run 'python Worker.py'
3. In the directory of the program, run 'python run'
