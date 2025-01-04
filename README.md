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

There are two separate statistical analyses:

- Count accents/προσῳδίαι straight off
- Count βαρύς and ὀξύς, where
  - a heavy syll is βαρύς if it has circumflex or the preceeding syll has an acute 
  - a syll is ὀξύς if it has an acute and the subsequent syll is light