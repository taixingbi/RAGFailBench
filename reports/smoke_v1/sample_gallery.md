# Sample Gallery

## Clean Seeds

- **Q:** Where did Sarah Allen attend university?
  - **A:** Brown University (organization, easy)
  - **Evidence:** Allen attended Brown University in Rhode Island, where she majored in computer science and visual arts.
  - **Source:** Sarah Allen (software developer) / Lead

- **Q:** When was Michael Bell born?
  - **A:** July 30, 1938 (date, easy)
  - **Evidence:** Michael Bell (born July 30, 1938) is an American actor who is most active in voice over roles.
  - **Source:** Michael Bell (actor) / Lead

- **Q:** What is the third capital of Goguryeo according to the passage?
  - **A:** Pyongyang (location, easy)
  - **Evidence:** Pyongyang — third capital of Goguryeo (427 — 668 CE)
  - **Source:** Capital of Korea / During the Three Kingdoms of Korea

## missing_evidence

- **[low]** Where did Sarah Allen attend university?
  - expected: abstain (answer_available=False)
  - contexts (2): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | In 2010, Allen co-founded and serves as the chief technology officer of mobile s

- **[medium]** Where did Sarah Allen attend university?
  - expected: abstain (answer_available=False)
  - contexts (1): In 2010, Allen co-founded and serves as the chief technology officer of mobile s

- **[high]** Where did Sarah Allen attend university?
  - expected: abstain (answer_available=False)
  - contexts (3): The WIFIRE lab currently serves a community of 130+ organizations, and works to  | After the winners of this prize were announced, Arritt told the Des Moines Regis | To speed up adoption and provide broadband Internet access in rural areas with p

## context_noise

- **[low]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (3): During the Finnish Civil War in 1918, Vaasa served as the temporary capital of W | On 4 August 2017, the Trump administration delivered an official notice to the U | Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre

- **[medium]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (4): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | As leader of Microsoft's Networking over White Spaces (KNOWS) project, Bahl led  | Over the past 20 years, Bahl has been a keystone figure in the mobile computing 

- **[high]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (5): In 1991, Bell and his colleague Melanie Chartoff conceived the Grayway Rotating  | He opened a free daycare at the factory so that mothers could work without leavi | Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre

## chunk_boundary

- **[low]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (2): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | she majored in computer science and visual arts. Early in her career, she led th

- **[medium]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (3): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | Bill Booth appears as a part of a waiver and introduction-to-skydiving video sho | she majored in computer science and visual arts. Early in her career, she led th

- **[high]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (5): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | Bradham was born Caleb Davis Bradham on May 27, 1867, in Chinquapin, North Carol | she majored in computer

## evidence_position

- **[low]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (6): Sarah Allen (born Sarah Lindsley) is an American software developer and entrepre | Nagaland was created in 1963 as the 16th state of the Indian Union, before which | Media center applications are multimedia applications for digital media and comb

- **[medium]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (6): The United States National Microbiome Data Collaborativem for storing data relat | Israeli foreign minister Shlomo Ben-Ami described the Oslo Accords as legitimizi | Google acquired Metaweb in 2010 and stated part of the acquisition was to improv

- **[high]** Where did Sarah Allen attend university?
  - expected: answer (answer_available=True)
  - contexts (6): Countries determine themselves what contributions they should make to achieve th | Dropbox has computer apps for Microsoft Windows, Apple macOS, and Linux computer | Following the end of the British Mandate and the Declaration of the Establishmen
