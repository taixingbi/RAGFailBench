# Sample Gallery

## Clean Seeds

- **Q:** Where did Hall receive his B.S. degree?
  - **A:** Carnegie Institute of Technology (organization, easy)
  - **Evidence:** Hall holds three degrees from Carnegie Institute of Technology, a B.S. in 1956, an M.S. in 1958, and a Ph.D. in 1961.
  - **Source:** John L. Hall / Biography

- **Q:** In what year was Andrew Gould Bostom born?
  - **A:** 1955 or 1956 (numeric, easy)
  - **Evidence:** Andrew Gould Bostom (born 1955 or 1956) is an American author, physician and critic of Islam, who is a former associate professor of medicine and researcher at Brown University Medical School.
  - **Source:** Andrew G. Bostom / Lead

- **Q:** Where was Bekele born?
  - **A:** Addis Ababa (location, easy)
  - **Evidence:** Bekele was born in Addis Ababa, Ethiopia, and emigrated to the United States with his family at the age of four.
  - **Source:** Heman Bekele / Early life and education

## missing_evidence

- **[low]** Where did Hall receive his B.S. degree?
  - expected: abstain (answer_available=False)
  - contexts (2): He completed his postdoctoral studies at the Department of Commerce's National B | John Lewis "Jan" Hall (born August 21, 1934) is an American physicist, and Nobel

- **[medium]** Where did Hall receive his B.S. degree?
  - expected: abstain (answer_available=False)
  - contexts (2): John Lewis "Jan" Hall (born August 21, 1934) is an American physicist, and Nobel | Hall is one of the 20 American recipients of the Nobel Prize in Physics to sign 

- **[high]** Where did Hall receive his B.S. degree?
  - expected: abstain (answer_available=False)
  - contexts (3): Higgs turned down a knighthood in 1999, but in 2012, he accepted membership of t | At Edinburgh, Higgs first became interested in mass, developing the idea that pa | Robert Hofstadter coined the term fermi, symbol fm,
in honor of the Italian phys

## context_noise

- **[low]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (3): Born in Denver, Colorado, Hall holds three degrees from Carnegie Institute of Te | Title 3, Provisions on the institutions
Article 13 establishes the institutions  | assertion
In computer programming, a statement that a predicate (Boolean-valued 

- **[medium]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (5): Born in Denver, Colorado, Hall holds three degrees from Carnegie Institute of Te | In 1914, Braun went to New York in the United States to be a witness for the def | Joshua Lionel Cohen was born in Queens, New York City on August 25, 1877 to Hyma

- **[high]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (7): Einstein bequeathed his personal archives, library, and intellectual assets to t | In 1957, Esaki recognized that when the p–n junction width of germanium is thinn | During 1956 and 1957, Heisenberg was the chairman of the Arbeitskreis Kernphysik

## chunk_boundary

- **[low]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (2): Hall holds three degrees from Carnegie Institute of Technology, a B.S. | in 1956, an M.S. in 1958, and a Ph.D. in 1961. He completed his postdoctoral stu

- **[medium]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (3): Hall holds three degrees from Carnegie Institute of Technology, a B.S. | 1943: Madame Curie, a U.S. Oscar-nominated film by Mervyn LeRoy starring Greer G | in 1956, an M.S. in 1958, and a Ph.D. in 1961. He completed his postdoctoral stu

- **[high]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (5): Hall holds three degrees from Carnegie Institute of Technology, a B.S. | Hinton is a Fellow of the US Association for the Advancement of Artificial Intel | in 1956, an M.S. in

## evidence_position

- **[low]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (8): Born in Denver, Colorado, Hall holds three degrees from Carnegie Institute of Te | C99 added five more reserved words: (‡ indicates an alternative spelling alias f | From the 1990s onwards, major urban developments in the Klang Valley extended th

- **[medium]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (8): At the 2020 census, Indianapolis had a population of 887,642 and a population de | Despite being somewhat limited in accuracy, the engraved Denkmäler plates formed | The Gaborone Dam is located south of Gaborone along the Gaborone-Lobatse road, a

- **[high]** Where did Hall receive his B.S. degree?
  - expected: answer (answer_available=True)
  - contexts (8): Law Professor Solon Solomon said "the court’s stance suggests a hesitation to ex | AccuWeather's broadcast meteorologist Jim Kosek attracted attention in 2010 due  | Grand Teton National Park is a popular destination for mountain and rock climber
