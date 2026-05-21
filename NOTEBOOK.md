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
| M | Metadata | 6 | All meta information (e.g.: Title, End, Author's comments, ...) | Written by ...<br>The End<br>(Note to Postprod: ...)|
| N | Narrative | 7 | Action lines between dialogue blocks | Liam goes to the other room |
| O | Omit | 8 | Lines to be ignored such as blank lines, page headers, ... | YS #504 - Produciton Draft(4/29/22) 2. |
| P | Parenthetical | 9 | Small actions to be performed during a dialogue | (nods to her)<br>(disagreeing) |
| S | Slugline | 10 | Scene header | 2 INT. INTERVIEW ROOM - BOZEMAN POLICE STATION - DAY  2 |
| T | Transition | 11 | Transition between scenes or betwen shots | CUT TO<br>FADE IN | 
| U | Utterance | 12 | What the actor utters during a dialogue | Let's go<br>You don’t look like a Bethany.|


### File format
- format convention: `{LABEL_1},{LABEL_2},...,{LABEL_N}|{LINE}`. Example: `N,G|               From his POV is a menu of times and dates, icons for past`
- `.script` extension doesn't play nicely with `pathlib`. It can't write text in it. Changed to `.screenplay`

### Annotations

When a Screenplay is annotated, each line is preceded by label(s). Line and label(s) are separated by a `|` and labels, if several, are separated from one another by a `,`.

The first label is the main one to be associated to the line. The other ones are secondary and given in no particular order.

### Movies and TV Shows

A mix of contemporary and older movies and TV shows have been selected to create this dataset.

Great care has been put into creating a dataset representative of the diverse screenplay's formats. However, only those having a generally consistent structure throughout the script were considered.

Some movies' screenplays have been shortened.

<details>
<summary>Screenplays' data and specificities</summary>

| #  | IMDB ID     | Title                      | Type    | Nbr lines | Specificities |
|----|-------------|----------------------------|---------|:---------:|---------------|
| 01 | tt2089050   | Black Mirror (103)         | TV Show | 3648      | - Playbacks<br>- Page header<br>- Metadata |
| 02 | tt9166672   | Chernobyl (103)            | TV Show | 2768      | - Disclaimer<br>- Omits |
| 03 | tt6701648   | Electric Dreams (107)      | TV Show | 3151      | - Disclaimer<br>-Quotes in header<br>- Page header<br>- Metadata<br>- Flashbacks<br>- INT./EXT. |
| 04 | tt8806272   | Euphoria (108)             | TV Show | 3304      | - OCR perturbations<br>- Cast and set lists<br>- Page header |
| 05 | tt3097534   | Fargo (101)                | TV Show | 3481      |  |
| 06 | tt8052820   | Fargo (401)                | TV Show | 3639      | - Cast and set lists<br>-Quotes in header<br>- Disclaimer<br>- Page header<br>- Double lines scene headers<br>- Many camera guidances<br>- Many Character Introductions  |
| 07 | tt11610562  | Mare of Easttown (107)     | TV Show | 3494      | - Versioning in header<br>- Disclaimer<br>- Page header<br>- Omits<br>- Metadata<br>- Flashbacks<br>- INT./EXT.<br>- Alternative dialogues |
| 08 | tt11650328  | Severance (101)            | TV Show | 2701      | - Expressions on separate line<br>- Metadata |
| 09 | tt15242998  | Severance (210)            | TV Show | 2341      | - Cast and set lists<br>- Versioning in header<br>- Disclaimer<br>- Page header<br>- Omits |
| 10 | tt21151974  | Succession (403)           | TV Show | 4326      | - Disclaimer<br>- Page header<br>- Double dialogues<br>- Many audio guidances<br>- Character with scene ID<br>- Omits<br>- INT./EXT. |
| 11 | tt7435258   | The Handmaid's Tale (211)  | TV Show | 6577      | - Playbacks<br>- Cast and set lists<br>- Page header<br>- Alternative dialogues/scenes |
| 12 | tt8054880   | The Morning Show (101)     | TV Show | 276       | - Metadata |
| 13 | tt13868048  | The White Lotus (101)      | TV Show | 2647      | - Page header |
| 14 | tt2790196   | True Detective (105)       | TV Show | 2689      | - Metadata<br>- Page header<br>- Double extensions<br>- Inconsistent extensions |
| 15 | tt23642488  | Yellowstone (504)          | TV Show | 2265      | - Characters and Sets lists<br>- Page header<br>- Disclaimer<br>- Versioning in header |
| 16 | tt0069762   | Badlands                   | Movie   | 3314      | - No indentation<br>- Dialogue blocks in one line |
| 17 | tt1542344   | 127 Hours                  | Movie   | 4244      | - Same indentation for utterance and narrative<br>- INT./EXT.<br>- Metadata<br>- Camera guidances in slugs |
| 18 | tt8579674   | 1917                       | Movie   | 6385      | - Disclaimer<br>-Quotes in header<br>- Double extensions<br>- Metadata |
| 19 | tt0765429   | American Gangster          | Movie   | 3197      | - INT./EXT.<br>- Omits |
| 20 | tt16311594  | F1: The Movie              | Movie   | 7953      | - Alternative dialogues/scenes<br>- Page header<br>- (into radio) vs (over radio)<br>- Camera guidances in slugs<br>- Omits |
| 21 | tt4123430   | Fantastic Beats: tCoG      | Movie   | 6577      | - Page header |
| 22 | tt0080745   | Flash Gordon               | Movie   | 3444      | - No indentation<br>- Characters in scene metadata line<br>- Page header |
| 23 | tt0083866   | E.T.                       | Movie   | 2415      | - No indentation<br>- Metadata<br>- Dialogue blocks in one line |
| 24 | tt0038650   | It's a Wonderful Life      | Movie   | 9576      | - X's VOICE<br>- Unrecognized characters<br>- Many camera guidances |
| 25 | tt0035423   | Kate and Leopold           | Movie   | 6086      | - X's VOICE|
| 26 | tt0209144   | Memento                    | Movie   | 7280      | - Edit markers (*)<br>- Camera guidances in slugs<br>- Page header<br>- OCR perturbations |
| 27 | tt0047396   | Rear Window                | Movie   | 3510      | - Camera guidances in slugs<br>- Many camera guidances |
| 28 | tt1542344   | The Revenant               | Movie   | 5528      | - Same indentation for utterance and narrative<br>-Quote in header<br>- Page header<br>- Camera guidances in slugs |
| 29 | tt0049730   | The Searchers              | Movie   | 7563      | - Camera guidances in slugs<br>- Double lines scene headers<br>- Metadata |
| 30 | tt0032138   | The Wizard of Oz           | Movie   | 1178      | - No indentation<br>- Many camera guidances<br>- Camera guidance acronyms<br>- Scene headers included in narrative block |

</details>


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
- Scene summary / meta explanation (like E.T.)
- Story board generation
- Cast description
- Estimate scene budget
- Sanitize script / De-conflict lines with multiple labels (e.g.: N,U,C -> N/U/C)
- Extract props from scene and link them inter scenes
- Extract extras (background actors)
- Read script with different voices for each character and narrator.
