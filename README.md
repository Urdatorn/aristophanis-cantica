# Aristophanis Canticorum Omniorum Responsio Accentuum

## Work flow
1. Extract the cantica from the Diogenes XMLs
2. Manually mark 
   1. syllable boundaries and their weight, 
   2. anceps and resolution/contraction attributes
   3. macrons
3. Compile into machine-friendly custom XML
4. Runs responsion stats 

## The stats

There are tree separate statistical analyses:

- Count accents/προσῳδίαι straight off
  - Might prove that grave responsion is not statistically significant
- Count βαρύς and ὀξύς, where
  - a heavy syll is βαρύς if it has circumflex or the preceeding syll has an acute 
  - a syll is ὀξύς if it has an acute and the subsequent syll is light
- Count compatible syllables

These metrics should also be run on subsets of 
- rhythmic genres:
  - on trochaic verses only
  - on iambic verses only
  - on Aeolic verses only
- individual plays

We search for statistical development
- between the songs within a play (are the earlier or latter more responding? Linear dev?)
- between all plays 
- between machine generated clusters of plays!

## TODO

☐ word breaks
☐ 3rd statistic: melodic direction (rate of change) based on responsion
    ☐ melodic acceleration: a metric of the larger arc of the melody
    ☐ melodic jerk: a metric of the vivacity of the melody d3[melody]/dt3


## Take-aways

The penultimate paeon of  997 is an intersting example of melodic responsion as influencing editorial decisions. The strophe has τήνδε, and readings vary between ὄρχον (L, adoped by Wilson 2007), κλάδον (cett), ὄσχον (Brunck) and ὦσχον (Deubner, adopted by Parker 1997). Bracketing the sense, the first three readings gain extra attraction (for what its worth) because they make the acutes respond, perhaps the more convincing since the outlier is a conjecture.