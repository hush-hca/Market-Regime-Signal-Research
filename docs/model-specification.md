# Exploratory specification v1

This is a frozen description of this implementation, not a claim of preregistration before previously inspected data. Any parameter changes require a new specification version and new untouched evaluation to support confirmatory claims.

Baseline: four KMeans clusters, random seed 42, n_init 10, expanding complete-observation training after 365 daily warm-up rows, refits every 90 days, final 180 days frozen. At least 180 complete training observations per fit. StandardScaler fits only on training rows. Names rank centroid 30-day momentum within each fit; labels do not guarantee stable economic identity across fits.

Feature sets:

1. Price only: 7/30-day momentum, 30-day annualized volatility, 30-day log-volume z-score.
2. Price + derivatives: those features plus seven-day mean funding and seven-day USD OI change.
3. Price + derivatives + on-chain: previous set plus MVRV and exchange net flows; SOPR only if supplied. Manifest lists exact columns and unavailable metrics.

Feature sets with insufficient complete training data are explicitly unavailable. Available models are compared on common classified signal dates, using the same next-open entries and non-overlapping 7/14/30-day horizons. Coverage and training counts are reported. Conditional-return summaries describe groups, not profitable strategies learned after the fact. Equal labels across fits or feature sets do not mean equal centroids.

Context hypothesis: daily funding crosses from nonnegative to negative, and MVRV is strictly below the 20th percentile of the prior 365 rows, requiring at least 180 nonmissing prior MVRV observations. Threshold excludes the current observation. Missing required input yields unknown. This is negative-funding/low-MVRV context, not established capital inflow.

Existing final holdout has been inspected. All new comparisons are exploratory. No supervised probability, tuned profitable-cluster rule, automatic parameter search or significance claim is introduced. A future evaluation should record a fixed start date, dataset/model version and all decisions before seeing forward outcomes.
