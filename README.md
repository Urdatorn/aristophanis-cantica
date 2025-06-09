# Aristophanis Canticorum Omniorum Responsio Accentuum

## Copyright and citation

That science is "open" should be an analytical truth, since without transparency of method and sharing of data there can be no true replicability and hence no interesting peer review (you can't *RE*-view what you aren't allowed to *view* in the first place!). Sadly, its not, and so I have to explicitly state that this repository is under the copyleft GNU GPL 3 license, which means you are more than welcome to fork and build on this software for your own open-science research. If you have found this repository useful, please cite it in the following way:

> Thörn Cleland, Albin Ruben Johannes (2025, June 16-18). Hidden Choral Stimuli: The Role of Accent in the Refrains of Aristophanes [Conference presentation]. PLOTTING POETRY 8: Skeletons in the Closet, Prague, The Czech Republic.

```
@inproceedings{thorncleland2025hidden,
  author       = {Thörn Cleland, Albin Ruben Johannes},
  title        = {Hidden Choral Stimuli: The Role of Accent in the Refrains of Aristophanes},
  eventtitle   = {PLOTTING POETRY 8: Skeletons in the Closet},
  eventdate    = {2025-06-16/2025-06-18},
  venue        = {Prague, The Czech Republic},
  note         = {Conference presentation},
}
```

## Corpus

The corpus consists of all the **78** Aristophanic cantica (songs, chorals) that have responding strophes, i.e. that are either antistrophic (exactly two strophes) or polystrophic (that have 3 or 4 strophes):

- ✅ Ach.: 9 (1 polystr. with 4 str.)
- ✅ Eq.: 8, alla körer! (1 polystr. with 4 str.)
- ✅ Nu.: 6
- ✅ V.: 8
- ✅ Pax: 6 (1 polystr. with 3 str.)
- ✅ Av.: 10
- ✅ Lys.: 8 (1 polystr. with 4 str.)
- ✅ Th.: 4
- ✅ Ra.: 11 (2 polystr. with 3 and 4 str. resp.)
- ✅ Ec.: 6 
- ✅ Pl.: 2

As seen above, only 6 songs (≈ 7.6%) are polystrophic, only 3 of which have 4 strophes. 

## Work flow
1. Extract the cantica from the Diogenes XMLs
2. Manually mark 
   1. syllable boundaries and their weight, 
   2. anceps and resolution/contraction attributes
   3. (optional: macrons for some superlongs)
3. Compile into machine-friendly custom XML
4. Compute the three responsion metrics 
5. Interpret and cluster the results in interesting ways

## Hypotheses to test

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
  - on the two songs of "undeveloped Attic dactylo-epitrite", av02 and Ran. 674ff~706ff
- individual plays

We search for statistical development
- between the songs within a play (are the earlier or latter more responding? Linear dev?)
- between all plays
  - do "virtuosic" plays (such as Av. acc. to Parker, and arguably Ra.) stand out in any way?
- between machine generated clusters of plays!
- inside a song, e.g. if as in V. 526 (νῦν δὴ...) the opening 7 cola have no responsion while the last 6 all have. For such a corrupt text, that can also be a possible indicator of reliability

We also need to show
- the degree of dependence between word-end distribution and accent distribution and
- how often word-end responsion and accentual responsion come together 

## Upgrades to Conser's compatibility stats

- Support for manually scanned source
- Support for > 2 strophes, incl comp. percentages for each position
- 


## Take-aways

The penultimate paeon of  997 is an intersting example of melodic responsion as influencing editorial decisions. The strophe has τήνδε, and readings vary between ὄρχον (L, adoped by Wilson 2007), κλάδον (cett), ὄσχον (Brunck) and ὦσχον (Deubner, adopted by Parker 1997). Bracketing the sense, the first three readings gain extra attraction (for what its worth) because they make the acutes respond, perhaps the more convincing since the outlier is a conjecture.

# Results

See [this notebook](nb_results.ipynb). 