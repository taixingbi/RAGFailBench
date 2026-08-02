# Sample Gallery

## Clean Seeds

- **Q:** When was Johannes Georg Bednorz born?
  - **A:** 16 May 1950 (date, easy)
  - **Evidence:** Johannes Georg Bednorz (German: [ˈɡeːɔʁk ˈbɛdnɔʁt͡s] ; born 16 May 1950) is a German physicist who, together with K. Alex Müller, discovered high-temperature superconductivity in ceramics, for which they shared the 1987 Nobel Prize in Physics.
  - **Source:** Georg Bednorz / Lead

- **Q:** When did Karl Ferdinand Braun die?
  - **A:** 20 April 1918 (date, easy)
  - **Evidence:** Karl Ferdinand Braun (German: [ˈfɛʁdinant ˈbʁaʊ̯n] ; 6 June 1850 – 20 April 1918) was a German applied physicist who shared the 1909 Nobel Prize in Physics with Guglielmo Marconi for their contributions to the development of radio.
  - **Source:** K. Ferdinand Braun / Lead

- **Q:** Where was Esposito born and raised?
  - **A:** El Paso, Texas (location, easy)
  - **Evidence:** Esposito was born and raised in El Paso, Texas.
  - **Source:** Lauren Esposito / Early life and education

## missing_evidence

- **[low]** Where was Esposito born and raised?
  - expected: abstain (answer_available=False)
  - contexts (2): She kept a collection of insects in egg cartons, and her first grade science pro | Lauren Esposito is the assistant curator and Schlinger chair of Arachnology at t

- **[medium]** Where was Esposito born and raised?
  - expected: abstain (answer_available=False)
  - contexts (2): Lauren Esposito is the assistant curator and Schlinger chair of Arachnology at t | In 2011 she joined University of California, Berkeley as a postdoctoral research

- **[high]** Where was Esposito born and raised?
  - expected: abstain (answer_available=False)
  - contexts (3): Elders drew fire, as well as censure from the Clinton administration, when she s | Manfred von Ardenne was made head of Institute A. Goals of von Ardenne's Institu | Amanda Bosh is an American planetary scientist and observational astronomer best

## context_noise

- **[low]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (3): The situation had not stabilized by 17 June, and the Finns were being pushed bac | 1st place: Mitsuku – 24 points
2nd place: Uberbot – 6 points
3rd place: Anna – 5 | Esposito was born and raised in El Paso, Texas. She kept a collection of insects

- **[medium]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (5): Science and the human temperament, Allen & Unwin (1935), translated and introduc | During 1956 and 1957, Heisenberg was the chairman of the Arbeitskreis Kernphysik | In 1946, Richard Scott Perkin recruited Liston to join Perkin-Elmer as a chief e

- **[high]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (7): The day after Koshiba received the Nobel Prize in Physics, Koichi Tanaka, an eng | In the wake of the 1957 Sputnik crisis, the U.S. government's interest in scienc | A crucial moment came when Cockcroft read a paper by George Gamow on quantum tun

## chunk_boundary

- **[low]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (2): Esposito was born and | raised in El Paso, Texas. She kept a collection of insects in egg cartons, and h

- **[medium]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (3): Esposito was born and | From 1924 to 1927, Heisenberg was a Privatdozent at Göttingen, meaning he was qu | raised in El Paso, Texas. She kept a collection of insects in egg cartons, and h

- **[high]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (5): Esposito was born and | William Daniel Phillips (born November 5, 1948) is an American physicist. He sha | raised in

## evidence_position

- **[low]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (8): Esposito was born and raised in El Paso, Texas. She kept a collection of insects | The Napoleonic Wars were taking place in Europe, involving France, Great Britain | US 8,719,592—Secure Telematics (VeeZee) US 8,027,293—Communication Channel Selec

- **[medium]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (8): On June 19, 2018, GitHub expanded its GitHub Education by offering free educatio | The Donald P. Eckman Award, in 1993, awarded by the American Automatic Control C | MIT's Provost Martin Schmidt announced the newly formed institute as an effort t

- **[high]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (8): The United States National Microbiome Data Collaborativem for storing data relat | At the urging of President Sukarno, Prime Minister Ali Sastroamidjojo began auth | The Three Hundred and Thirty-Five Years' War (Dutch: Driehonderdvijfendertigjari

## conflict

- **[low]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (2): Esposito was born and raised in El Paso, Texas. She kept a collection of insects | Esposito was born and raised in Tokyo.

- **[medium]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (4): Esposito was born and raised in Sydney. | Esposito was born and raised in El Paso, Texas. She kept a collection of insects | Amiga was one of the first commercial platforms to allow amateur and professiona

- **[high]** Where was Esposito born and raised?
  - expected: answer (answer_available=True)
  - contexts (8): Esposito was born and raised in Sydney. | Kuhn concluded that Aristotle's concepts were not "bad Newton," just different.  | Memory instructions to set and access numbers and strings in random-access memor

## hard_negative

- **[low]** When was Johannes Georg Bednorz born?
  - expected: abstain (answer_available=False)
  - contexts (2): Karl Alexander Müller (20 April 1927 – 9 January 2023) was a Swiss physicist. He | Since 1988, Kajita has been at the Institute for Cosmic Radiation Research, Univ

- **[medium]** When was Johannes Georg Bednorz born?
  - expected: abstain (answer_available=False)
  - contexts (4): Karl Alexander Müller (20 April 1927 – 9 January 2023) was a Swiss physicist. He | Since 1988, Kajita has been at the Institute for Cosmic Radiation Research, Univ | Val Logsdon Fitch (March 10, 1923 – February 5, 2015) was an American nuclear ph

- **[high]** When was Johannes Georg Bednorz born?
  - expected: abstain (answer_available=False)
  - contexts (8): Karl Alexander Müller (20 April 1927 – 9 January 2023) was a Swiss physicist. He | Since 1988, Kajita has been at the Institute for Cosmic Radiation Research, Univ | Val Logsdon Fitch (March 10, 1923 – February 5, 2015) was an American nuclear ph
