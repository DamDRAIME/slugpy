import json
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm

SYSTEM_PROMPT = """
Your job is to extract information from a screenplay's action/narrative lines.

Here are the elements to extract:
- PROPS: all props mentioned in the chunk (e.g.: "Colt 38mm", "red car", "smartphone", "letter from John", "empty bottle of water");
- CAST: all named characters mentioned in the chunk (e.g.: "Jack", "Michael Montano", "Mr Doubtfire");
- EXTRA: all unnamed characters (background characters) mentioned in the chunk (e.g.: "gorgeous blonde", "waiter", "crowd of fans").

REMARKS:
- Do not include duplicates
- Use best judgment to infer indirect mentions of a prop (e.g.: if a character is smoking, it's likely that there's a cigarette in the scene, even if it's not explicitly mentioned)
- Retain as much information as possible about the props and characters, including adjectives, relative clauses, appositions, etc.

EXAMPLES:
- "All is still -- suddenly it comes crashing down -- the end wall comes crashing down - a flurry of bricks and mortar... Crashing down...  Through a smokey powdered fog we can see a group of men in the downstairs room of the derelict house... On the walls faded 40's wallpaper, peeling in parts to reveal older dim patterns... A few unmatched armchairs in various states of disrepair -- a 60's black vinyl, a deco-patterned smoker, a 70's cream plastic, a brown wooden kitchen chair etc... The colours in the room are browns, greys, caramels, darks, muted..."  -> {"props": ["brown wooden kitchen chair", "faded 40's wallpaper", "60's black vinyl armchair", "deco-patterned smoker armchair", "70's cream plastic armchair"], "cast": [], "extra": ["group of men"]}
- "In the middle of the room, standing on dusty, bare wooden floorboards, his fist clenched aggressively by his sides, is OLD MAN PEANUT, aged 80... Skinny... Wearing a CONTINUED: (2)  dark three piece suit... Gold watch chain... Black Homburg... He is squaring up to us... " -> {"props": ["dark three piece suit", "gold watch chain", "black Homburg"], "cast": [], "extra": ["old man peanut"]}
- "sitting nonchalantly cross- legged in a battered brown leather wingback armchair and casually smoking a Davidoff cigarette, is MEREDITH, late 40's... Suave... Immaculate... Wearing black handmade boots, black Saville Row suit, black cashmere roll neck sweater, " -> {"props": ["black handmade boots", "black Saville Row suit", "black cashmere roll neck sweater", "Davidoff cigarette"], "cast": ["Meredith"], "extra": []}
- "His friend is on the toilet with his head in his hands. He seems to be in some pain.  He is SCOTT SUMMERS - AGE 13\nThe Freckled kid offers a small plastic bottle.\nThe freckled kid looks and sees that Scott's eyes are watering so badly that tears" -> {"props": ["small plastic bottle"], "cast": ["Scott Summers"], "extra": ["freckled kid"]}
- "The two combatants roll madly down the hill obscured by flying snow. Finally, we see Logan separate from his attacker and CRASH THROUGH THE ICE of the frozen lake. E.C.U. - A MASSIVE CLAW-LIKE HAND lifts into frame the SHINING DOG TAG hanging from it.  The tags chain slides off. " -> {"props": ["dog tag"], "cast": ["Logan"], "extra": ["attacker"]}
- "Aunt Emma spots some white powder on the edge of Jordan's nostril. Deftly, she wipes it off, smiling.\nAunt Emma leans in to his ear.\nAnd with that, she turns back to Naomi." -> {"props": ["white powder"], "cast": ["Aunt Emma", "Jordan", "Naomi"], "extra": []}
- "Jordan sips a martini and studies Mark Hanna, hitting on a STRIPPER.\nBriefcase in hand, Jordan boards the elevator with a dozen other BROKERS." -> {"props": ["martini", "briefcase"], "cast": ["Jordan", "Mark Hanna"], "extra": ["stripper", "brokers"]}
- "Ryan hurriedly signs a hand-held device, hops into a SEDAN and speeds off. The RENTAL CAR ASSISTANT suddenly realizes..." -> {"props": ["hand-held device", "sedan"], "cast": ["Ryan"], "extra": ["rental car assistant"]}
- "The helicopter is CIRCLING above the destroyed reactor.\nTrailers have been set up near the site as mobile offices. A web of FIRE HOSES extend out from the ruins toward Pikalov's specialized military fire trucks. Pikalov waits" -> {"props": ["fire hoses", "helicopter", "military fire trucks", "trailers"], "cast": ["Pikalov"], "extra": []}
"""


class NarrativeChunkData(BaseModel):
    props: list[str] | None = Field(
        None,
        description="All physical items handled or used by a character or serving for the movie's narrative.",
        examples=["pen", "light saber", "One Ring", "painting on the wall", "Jaguar convertible car"],
    )
    cast: list[str] | None = Field(
        None,
        description="All named characters. This does NOT include unnamed characters, which should be included in the 'extra' field.",
        examples=["Leonard", "Darth Vader", "Lyudmilla", "Cassie Lafayette", "Jordan Belfort"],
    )
    extra: list[str] | None = Field(
        None,
        description="All unnamed characters.",
        examples=["airplane steward", "nascar driver", "dozen of zombies", "2 brookers"],
    )

    def dump_json_with_chunk(self, chunk: str) -> str:
        data = self.model_dump()
        data["narrative_chunk"] = chunk
        return json.dumps(data)


def build_prompt(chunk: str):
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"<chunk>{chunk}</chunk>"}]


def annotate_narrative_chunks(
    narrative_chunks_filepath: Path, output_folderpath: Path, url: str, model_name: str, **client_kwargs
):
    output_folderpath.mkdir(parents=True, exist_ok=True)
    output_filepath = output_folderpath / f"{narrative_chunks_filepath.stem}_annotated.jsonl"
    output_filepath_errors = output_folderpath / f"{narrative_chunks_filepath.stem}_errors.jsonl"

    client = OpenAI(base_url=url, **client_kwargs)

    with output_filepath.open("a", encoding="utf-8") as out_fh, output_filepath_errors.open(
        "a", encoding="utf-8"
    ) as out_fh_er, narrative_chunks_filepath.open("r", encoding="utf-8") as in_fh:
        n_chunks = sum(1 for _ in in_fh)
        in_fh.seek(0)
        for chunk in tqdm(in_fh, total=n_chunks):
            response = client.chat.completions.parse(
                model=model_name,
                messages=build_prompt(chunk),
                response_format=NarrativeChunkData,
            )
            try:
                narrative_chunk_data = NarrativeChunkData.model_validate_json(response.choices[0].message.content)
                ncd_string = narrative_chunk_data.dump_json_with_chunk(chunk)
                out_fh.writelines(ncd_string + "\n")
                out_fh.flush()
            except:
                print("Failed to process chunk:", chunk)
                print("response:", response.choices[0].message.content)
                out_fh_er.writelines(json.dumps({"narrative_chunk": chunk}) + "\n")
                out_fh_er.flush()
