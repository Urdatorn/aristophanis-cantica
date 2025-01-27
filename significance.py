#!/usr/bin/env python3
"""
significance.py

A utility module for comparing an observed proportion against 9.7% using a binomial test.
"""

from scipy.stats import binomtest

class SignificanceTester:
    """
    Tests whether an observed proportion differs from the
    reference proportion (default 9.7%) via a binomial test.
    """

    def __init__(self, reference_proportion=0.097):
        """
        :param reference_proportion: The expected proportion (default = 0.097 or 9.7%).
        """
        self.reference_proportion = reference_proportion

    def test_significance(self, successes, trials, alternative='two-sided'):
        """
        Perform a binomial test to compare the observed proportion (successes/trials)
        to the reference proportion.

        :param successes: Number of observed 'successes'.
        :param trials: Total number of trials.
        :param alternative: 'two-sided', 'greater', or 'less' (for the test).
        :return: p-value (float) from the binomial test.
        """
        result = binomtest(
            k=successes,
            n=trials,
            p=self.reference_proportion,
            alternative=alternative
        )
        return result.pvalue

    def is_above_05(self, successes, trials, alternative='two-sided'):
        """
        Check if the p-value is strictly above 0.05.

        :param successes: Number of observed 'successes'.
        :param trials: Total number of trials.
        :param alternative: 'two-sided', 'greater', or 'less'.
        :return: True if the p-value > 0.05, else False.
        """
        p_value = self.test_significance(successes, trials, alternative)
        return p_value > 0.05