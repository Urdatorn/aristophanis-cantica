# Aristophanis Canticorum Omniorum Responsio Accentuum

## Antistrophic Cantica

Cantica med responsion: 
- ☑︎ Ach.: 10 (1 polystr.)
- ☑︎ Eq.: 8, alla körer! (1 polystr. m. 4)
- ☑︎ Nu.: 6
- ☑︎ V.: 8
- ☐ Pax: 6 (1 polystr.)
- ☐ Av.: 10
- ☐ Lys.: 8 (1 polystr.)
- ☐ Th.: 4
- ☐ Ra.: 11 (2 polystr.)
- ☐ Ec.: 6 
- ☐ Pl.: 2 

Summa: 79
Varav polystrofiska: 6 (≈ 7.6%)

## Work flow
1. Extract the cantica from the Diogenes XMLs
2. Manually mark 
   1. syllable boundaries and their weight, 
   2. anceps and resolution/contraction attributes
   3. macrons
3. Compile into machine-friendly custom XML
4. Runs responsion stats 

## The stats

There are three separate statistical analyses:

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
- inside a song, e.g. if as in V. 526 (νῦν δὴ...) the opening 7 cola have no responsion while the last 6 all have. For such a corrupt text, that can also be a possible indicator of reliability

We also need to show
- the degree of dependence between word-end distribution and accent distribution and
- how often word-end responsion and accentual responsion come together 

## URGENT TODOS!!

☐ fix accent count only counting one strophe sometimes
☐ polystrophic songs
☐ add "compatible syllables" stats
☐ scan some recitative as baseline, both since Conser does not provide a baseline of barys, and because it would be more fitting to use comic recitative 
☐ show word breaks in visualization 
- might be good to add option to remove "precisely repeating rephrains" from stats; cf. Conser's diss. p. 374.

## Upgrades to Conser's compatibility stats

- Support for manually scanned source
- Support for > 2 strophes, incl comp. percentages for each position
- 


## Take-aways

The penultimate paeon of  997 is an intersting example of melodic responsion as influencing editorial decisions. The strophe has τήνδε, and readings vary between ὄρχον (L, adoped by Wilson 2007), κλάδον (cett), ὄσχον (Brunck) and ὦσχον (Deubner, adopted by Parker 1997). Bracketing the sense, the first three readings gain extra attraction (for what its worth) because they make the acutes respond, perhaps the more convincing since the outlier is a conjecture.

# Results