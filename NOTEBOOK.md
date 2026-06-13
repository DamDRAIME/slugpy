# Development notes

## Models


## Dataset
### Labels

| ID | Label | Name          | Definition | Examples |
|:--:|:-----:|:-------------:|------------|----------|
| 0  | C     | Character     | A line from a *dialogue block* that indicates **who is speaking**. | LIAM<br>REPORTER<br>MECHANIC SON |
| 1  | D     | Deletion      | A line that refers to a **deleted/omitted scene**. | 4. OMITTED / Replaced by 5.   4. |
| 2  | E     | Extension     | A line from a *dialogue block* (usually place directly next to the character's name) that indicates **how or from where the character’s voice is heard, or clarify continuity of speech**, and that is not related to an action, emotion, or camera behavior. | (V.O.)<br>CONT'D<br>(o.s.) |
| 3  | G     | Camera        | A line that explicitly **directs the camera, describes camera movement, or frames what the audience sees** in a way that is not simply narrative action. | CLOSE UP on Liam<br>We see Liam<br>in the background...
| 4  | I     | Introduction  | A line that both:<br>&emsp;- mentions a **named character for the first time**, and;<br>&emsp;- provides **descriptive information** about who they are, what they look like, or how they behave | LIAM (30's) strong man with black hair... |
| 5  | M     | Metadata      | A line that provides **informational, contextual, or production‑oriented notes** that are not part of the story world (e.g.: Title, End, Author's comments, ...) and not part of the screenplay’s formal structure (like scene headers or transitions). | Written by ...<br>The End<br>(Note to Postprod: ...)|
| 6  | N     | Narrative     | A line that describes **events, behaviors, or physical changes** occurring in the story world, without giving instructions to the camera and without functioning as dialogue.<br>It communicates what happens, what characters do, and what the environment does, strictly from an in‑world perspective. | Liam goes to the other room |
| 7  | O     | Omit | A line that contains **non‑narrative, non‑structural, or non‑creative content—material** that is not part of the screenplay itself but exists for document formatting, production bookkeeping, or archival purposes (e.g. page header, blank line, ...). As such this line can be ignored. | (blank)<br>CONTINUED<br>YS #504 - Production Draft(4/29/22) 2. |
| 8  | P     | Parenthetical | A line from a *dialogue block* (usually placed directly beneath a character’s name and immediately before their spoken dialogue), that provides **brief, specific guidance on how a line is delivered or what the character is doing while speaking**. It exists solely to clarify tone, emotion, or small behavioral cues tied to the utterance. | (nods to her)<br>(disagreeing) |
| 9  | S     | Slugline      | A line that marks the **beginning of a new scene and provides structural information** rather than story action. The scene heading formally identifies the location and time of a scene. | 2 INT. INTERVIEW ROOM - BOZEMAN POLICE STATION - DAY  2<br>EXT. CHARLIE’S HOUSE - LATER |
| 10 | T     | Transition    | A line that indicates a **change in scene, shot, or narrative flow**. They do not describe story events or visuals within the world of the film. | CUT TO<br>FADE IN<br>INSERT<br>Blackness fills the screen | 
| 11 | U     | Utterance     | A line from a *dialogue block*  that represents **verbal communication** within the story world—anything a character says, whether it’s a full speech, a short response, a shout, a whisper, or a single word. | Let's go<br>You don’t look like a Bethany.|


> Remarks:<br>&emsp;For label `I`, the definition explicitly requires a description. This serves two purposes: 1/ Weak guarantee that it is the first mention of the character (otherwise the model wouldn't have any information to know if that character has already been mentioned), 2/ Exclude extras (i.e. background actors) as they are too numerous.

### File format
- format convention: `{LABEL_1},{LABEL_2},...,{LABEL_N}|{LINE}`. Example: `N,G|               From his POV is a menu of times and dates, icons for past`
- `.script` extension doesn't play nicely with `pathlib`. It can't write text in it. Changed to `.screenplay`

### Annotations

When a Screenplay is annotated, each line is preceded by label(s). Line and label(s) are separated by a `|` and labels, if several, are separated from one another by a `,`.

The first label is the main one to be associated to the line. The other ones are secondary and given in no particular order.

### Movies and TV Shows

A mix of contemporary and older movies and TV shows have been selected to create this dataset.

Great care has been put into creating a dataset representative of the diverse screenplay's formats. However, only those having a generally consistent structure throughout the script were considered.

> Note that some movies' screenplays have been shortened.

<details>
<summary>Screenplays' data and specificities</summary>

| #  | IMDB ID     | Title                      | Type    | Nbr lines | Specificities |
|----|-------------|----------------------------|---------|:---------:|---------------|
| 01 | tt2089050   | Black Mirror (103)         | TV Show | 3648      | - Playbacks<br>- Page header<br>- Metadata |
| 02 | tt9166672   | Chernobyl (103)            | TV Show | 2768      | - Disclaimer<br>- Omits |
| 03 | tt6701648   | Electric Dreams (107)      | TV Show | 3151      | - Disclaimer<br>-Quotes in header<br>- Page header<br>- Metadata<br>- Flashbacks<br>- INT./EXT. |
| 04 | tt8806272   | Euphoria (108)             | TV Show | 3304      | - OCR perturbations<br>- Cast and set lists<br>- Page header<br>- Edit markers (*) |
| 05 | tt3097534   | Fargo (101)                | TV Show | 3481      |  |
| 06 | tt8052820   | Fargo (401)                | TV Show | 3639      | - Cast and set lists<br>-Quotes in header<br>- Disclaimer<br>- Page header<br>- Double lines scene headers<br>- Many camera guidances<br>- Many Character Introductions  |
| 07 | tt11610562  | Mare of Easttown (107)     | TV Show | 3494      | - Versioning in header<br>- Disclaimer<br>- Page header<br>- Omits<br>- Metadata<br>- Flashbacks<br>- INT./EXT.<br>- Alternative dialogues |
| 08 | tt11650328  | Severance (101)            | TV Show | 2701      | - Expressions on separate line<br>- Metadata |
| 09 | tt15242998  | Severance (210)            | TV Show | 2341      | - Cast and set lists<br>- Versioning in header<br>- Disclaimer<br>- Page header<br>- Omits<br>- Edit markers (*) |
| 10 | tt21151974  | Succession (403)           | TV Show | 4326      | - Disclaimer<br>- Page header<br>- Double dialogues<br>- Many audio guidances<br>- Character with scene ID<br>- Omits<br>- INT./EXT. |
| 11 | tt7435258   | The Handmaid's Tale (211)  | TV Show | 6577      | - Playbacks<br>- Cast and set lists<br>- Page header<br>- Alternative dialogues/scenes<br>- Edit markers (*) |
| 12 | tt8054880   | The Morning Show (101)     | TV Show | 276       | - Metadata<br>- Dialogue blocks in one line<br>- Parentheticals on Utterance line |
| 13 | tt13868048  | The White Lotus (101)      | TV Show | 2647      | - Page header |
| 14 | tt2790196   | True Detective (105)       | TV Show | 2689      | - Metadata<br>- Page header<br>- Double extensions<br>- Inconsistent extensions |
| 15 | tt23642488  | Yellowstone (504)          | TV Show | 2265      | - Characters and Sets lists<br>- Page header<br>- Disclaimer<br>- Versioning in header |
| 16 | tt0069762   | Badlands                   | Movie   | 3314      | - No indentation<br>- Dialogue blocks in one line<br>- Parentheticals on Character line |
| 17 | tt1542344   | 127 Hours                  | Movie   | 4244      | - Same indentation for utterance and narrative<br>- INT./EXT.<br>- Metadata<br>- Camera guidances in scene headings<br>- Poor formatting |
| 18 | tt8579674   | 1917                       | Movie   | 6385      | - Disclaimer<br>-Quotes in header<br>- Double extensions<br>- Metadata<br>- Multi-languages<br>- Subtitles |
| 19 | tt0765429   | American Gangster          | Movie   | 3197      | - INT./EXT.<br>- Omits |
| 20 | tt16311594  | F1: The Movie              | Movie   | 7953      | - Alternative dialogues/scenes<br>- Page header<br>- (into radio) vs (over radio)<br>- Camera guidances in scene headings<br>- Omits<br>- Edit markers (*) |
| 21 | tt4123430   | Fantastic Beats: tCoG      | Movie   | 6577      | - Page header<br>- Poor formatting |
| 22 | tt0080745   | Flash Gordon               | Movie   | 3444      | - X's VOICE<br>- Characters in scene metadata line<br>- Page header |
| 23 | tt0083866   | E.T.                       | Movie   | 2415      | - No indentation<br>- Metadata<br>- Dialogue blocks in one line |
| 24 | tt0038650   | It's a Wonderful Life      | Movie   | 9576      | - X's VOICE<br>- Unrecognized characters<br>- Many camera guidances |
| 25 | tt0035423   | Kate and Leopold           | Movie   | 6086      | - X's VOICE|
| 26 | tt0209144   | Memento                    | Movie   | 7280      | - Edit markers (*)<br>- Camera guidances in scene headings<br>- Page header<br>- OCR perturbations |
| 27 | tt0054167   | Peeping Tom                | Movie   | 8239      | - Many camera guidances<br>- X's VOICE<br>- Confusion between camera prop and camera guidances |
| 27 | tt0047396   | Rear Window                | Movie   | 3510      | - Camera guidances in scene headings<br>- Many camera guidances |
| 28 | tt0049470   | The Man Who Knew Too Much  | Movie   | 9593      | - Many camera guidances<br>- Page header<br>- Camera guidances in scene headings<br>- OCR perturbations<br>- Multi-languages<br>- Poor formatting |
| 29 | tt1663202   | The Revenant               | Movie   | 5528      | - Same indentation for utterance and narrative<br>-Quote in header<br>- Page header<br>- Camera guidances in scene headings |
| 30 | tt0049730   | The Searchers              | Movie   | 7563      | - Camera guidances in scene headings<br>- Double lines scene headers<br>- Metadata<br>- Poor formatting<br>- Subtitles |
| 31 | tt0032138   | The Wizard of Oz           | Movie   | 1178      | - Poor formatting<br>- Many camera guidances<br>- Camera guidance acronyms<br>- Scene headers included in narrative block<br>- Dialogue blocks in one line |

</details>

TV Show' scripts have the advantage of being shorter, which results in a more diverse set of scripts being annotated. They also present features not commonly seen in Movie's scripts such as Cast and Set lists. However, as TV Shows tend to have a recurring set of characters, those are often not reintroduced in subsequent episodes, resulting in less `I` labels. This obviously doesn't affect Movie's scripts. Another draw for Movie's scripts is their lengths, which can be useful for analysis of richer and more complex characters interactions.

#### Todos

- [x] Annotate 30 screenplays
- [ ] Annotate 40-50 screenplays
- [x] Annotate `A` ? Not for this first iteration 
- [x] Second pass:
    - [x] Standardize annotation of `I`: Only when a new character is introduced for the first time? Only when you have a clear introduction, i.e. not for background actors? Only the name or also the description?
    - [x] Standardize annotation of `M`: Alternative dialogue? Notes/Comments? Supplement with other label?
    - [x] Standardize annotation of `G`: "Back on", "Black", "Insert", "Title", ...?
    - [x] Standardize annotation of `T`: What about "Cut to" in the middle of a scene?
- [ ] Train/FT models:
    - [ ] Multi-label line classifier
    - [ ] Multi-class line classifier
    - [ ] Props/Extra extractor
    - [ ] Scene heading parser
    - [ ] Single line dialogue block formatter

## Further development ideas

- UI
- Detect scene boundaries with a multi-modal approach: [Netflix approach](https://netflixtechblog.com/detecting-scene-changes-in-audiovisual-content-77a61d3eaad6) 
- Detect all cast in scene
- Scene summary / meta explanation (like E.T.)
- Story board generation
- Cast description
- Estimate scene budget
- Sanitize script / De-conflict lines with multiple labels (e.g.: N,U,C -> N/U/C)
- Extract props from scene and link them inter scenes
- Extract extras (background actors)
- Read script with different voices for each character and narrator.
- Capitalize props and new characters that haven't been mentioned before