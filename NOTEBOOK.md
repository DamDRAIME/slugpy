# Development notes

## Models


## Dataset
### Labels

| Label | Name | ID | Description | Examples |
|-------|------|----|-------------|----------|
| A | Audio | 0 | All guidances related to sound | The music fades...
| G | Camera | 1 | All guidances for the camera | CLOSE UP on Liam<br>We see Liam<br>in the background...
| C | Character | 2 | Character line from a dialogue block | LIAM |
| D | Deletion | 3 | Omitted/deleted scenes | 4. OMITTED / Replaced by 5.   4. |
| E | Extension | 4 | Additional information attached to `C` but not related to an action | (V.O.)<br>CONT'D<br>(o.s.) |
| I | Introduction | 5 | When a character is first introduced | LIAM (30's) strong man with black hair... |
| M | Meta | 6 | All meta information (e.g.: Title, End, Author's comments, ...) | Written by ...<br>The End<br>(Note to Postprod: ...)|
| N | Narrative | 7 | Action lines between dialogue blocks | Liam goes to the other room |
| O | Omit | 8 | Lines to be discarded such as blank lines, page headers, ... | YS #504 - Produciton Draft(4/29/22) 2. |
| P | Parenthetical | 9 | Small actions to be performed during a dialogue | (nods to her)<br>(disagreeing) |
| S | Slugline | 10 | Scene header | 2 INT. INTERVIEW ROOM - BOZEMAN POLICE STATION - DAY  2 |
| T | Transition | 11 | Transition between scenes or betwen shots | CUT TO<br>FADE IN | 
| U | Utterance | 12 | What the actor utters during a dialogue | Let's go<br>You don’t look like a Bethany.|


### File format
- format convention: `{LABEL_1},{LABEL_2},...,{LABEL_N}|{LINE}`. Example: `N,G|               From his POV is a menu of times and dates, icons for past`
- `.script` extension doesn't play nicely with `pathlib`. It can't write text in it. Changed to `.screenplay`

### Annotations
#### Specificities of each screenplay

| IMDB ID    | Title              | Type    | Specificities |
|------------|--------------------|---------|---------------|
| tt8806272  | Euphoria (108)     | TV Show | - OCR perturbations<br>- Cast and set lists<br>- Page header |
| tt2089050  | Black Mirror (103) | TV Show | - Playback scenes<br>- Page header<br>- Meta |
| tt23642488 | Yellowstone (504)  | TV Show | - Charcters and Sets lists<br>- Page header<br>- Disclaimer<br>- Versioning in header |
| tt16311594 | F1: The Movie      | Movie   | - Alternative dialogues/scenes<br>- Page header<br>- (into radio) vs (over radio)<br>- Camera guidances in slugs<br>- Omits |
| tt15242998 | Severance (210)    | TV Show | - Cast and set lists<br>- Versioning in header<br>- Disclaimer<br>- Page header<br>- Omits |
| tt13868048 | The White Lotus (101) | TV Show | - Page header |

#### Todos

- [ ] Annotate 40-50 screenplays
- [ ] Annotate `A` ?
- [ ] Second pass:
    - [ ] Standardize annotation of `I`: Only when a new character is introduced for the first time? Only when you have a clear introduction, i.e. not for background actors? Only the name or also the description?
    - [ ] Standardize annotation of `M`: Alternative dialogue? Notes/Comments? Supplement with other label?
    - [ ] Standardize annotation of `G`: "Back on", "Black", "Insert", "Title", ...?
    - [ ] Standardize annotation of `T`: What about "Cut to" in the middle of a scene?


## Further development ideas

- UI
- Detect scene boundaries with a multi-modal approach: [Netflix approach](https://netflixtechblog.com/detecting-scene-changes-in-audiovisual-content-77a61d3eaad6) 
- Detect all cast in scene
- Scene summary / meta explaination (like E.T.)
- Story board generation
- Cast description
- Estimate scene budget
- Sanitize script / Deconflict lines with multiple labels (e.g.: N,U,C -> N/U/C)
- Extract props from scene
- Extract extras (background actors)