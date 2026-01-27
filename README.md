# UCL-MScQT-BB84KeyRateSimulator
Python simulator to parameterise hardware setup and generate key rates of the BB84 protocol dependent on device characteristics.

To obtain a key rate for (currently standardised, unparameterised, no error reconciliation) BB84, run `python key/alice&bob/test_no_eve.py` from your terminal.

To obtain a key rate for (standardised, unparameterised, with error reconciliation) BB84, run `python key/alice&bob/test_eve.py` from your terminal.