import json
from pathlib import Path
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm

SYSTEM_PROMPT = """
Your job is to extract structured information from scene headings from screenplays.
Scene headings typically follow a format like: ({SCENE_ID}) {SETTING} - {LOCATION} - {TIME_OF_DAY} ({TEMPORAL_MODIFIERS}) ({SHOT_MODIFIERS})
where:
- SCENE_ID is an optional identifier for the scene, often a number or code (e.g.: "127", "A32");
- SETTING indicates whether the scene is interior (INT), exterior (EXT), or both (INT/EXT or I/E or E/I);
- LOCATION describes where the scene takes place and can contain multiple parts to make it more specific (e.g.: "EGUISAC MANOR / ANTEROOM & STUDY");
- TIME_OF_DAY indicates when the scene occurs (e.g.: "DAY", "NIGHT", "MORNING", "EVENING");
- TEMPORAL_MODIFIERS are optional descriptors that provide additional context about the timing of the scene or its era (e.g.: "FLASHBACK", "FLASH FORWARD", "CONTINUOUS", "MOMENTS LATER", "THAT MOMENT", "RIGHT AFTER", "DAY 2", "1940", "FUTURE", "1980's", "3 MONTHS LATER");
- SHOT_MODIFIERS are optional descriptors that provide additional context about the shot type or style (e.g.: "MEDIUM SHOT", "HIS POV", "ESTABLISHING SHOT", "BLACK AND WHITE", "3:2 RATIO", "CLOSE UP", "CLOSE ON XYZ").

REMARKS:
- SCENE_ID may be missing, present at the beginning and/or end of the scene heading. If present at both places and they do not match, use your best judgement knowing there could be some OCR-induced errors.
- SETTING may be `both` interior and exterior, in which case it may be represented as "INT/EXT", "I/E", "E/I" or similar. Use your best judgement to determine if the setting is interior, exterior or both.
- LOCATION field may contain multiple parts separated by separators, regroup those parts into a single location field.
- SHOT_MODIFIERS are often abbreviated such as MS for "MEDIUM SHOT", CU or C/U for "CLOSE UP", B/W for "BLACK AND WHITE". Use your best judgement to expand those abbreviations.
- If the scene heading contains "OMIT"/"OMITTED", it is not a scene heading and all fields should be null except for `is_scene_heading` which should be False.
- Some fields may be missing or not follow the exact format. If a field is missing return null for that field.
- Some OCR-induced errors may be present. Use your best judgement to correct for those errors.

EXAMPLES:
- "a1.       EXT. WOODS, FRANCE 1917 - DAWN  **C/U ON JACQUES**" -> {"is_scene_heading":true,"scene_id":"a1","setting":"exterior","location":"Woods, France","time_of_day":"Dawn","temporal_modifiers":["1917"],"shot_modifiers":["Close Up on Jacques"]}
- "40-42   OMITTED - EXT. ROAD / FARM - DAY" -> {"is_scene_heading":false}
- "351      EXT. FIELDS BEHIND THE FRONT / STABLE - TWILIGHT  18 MONTHS LATER. NOVEMBER 1918.  35l" -> {"is_scene_heading":true,"scene_id":"351","setting":"exterior","location":"Fields Behind the Front, Stable","time_of_day":"Twilight","temporal_modifiers":["18 MONTHS LATER", "NOVEMBER 1918"],"shot_modifiers":null}
- "Bl12   INT. LAKE HOUSE ~ LOUISE’S STUDY -—- DAY (FLASHBACK) B112" -> {"is_scene_heading":true,"scene_id":"B112","setting":"interior","location":"Lake House, Louise's Study","time_of_day":"Day","temporal_modifiers":["Flashback"],"shot_modifiers":null}
- "INT./EXT. SEDAN ON RAINY NEW YORK STREETS - CONTINUOUS  #AERIAL VIEW#" -> {"is_scene_heading":true,"scene_id":null,"setting":"both","location":"Sedan on Rainy New York Streets","time_of_day":null,"temporal_modifiers":["Continuous"],"shot_modifiers":["Arial View"]}
- "INT. SCOTTIE'S CAR - (MOONLIGHT / DAY 3) - LS" -> {"is_scene_heading":true,"scene_id":null,"setting":"interior","location":"Scottie's Car","time_of_day":null,"temporal_modifiers":["Moonlight", "Day 3"],"shot_modifiers":["Long Shot"]}
- "Shooting Draft, 1959"  -> {"is_scene_heading":false}
- "EXT. STARTING POST, THE RACES, SAME TIME--DAY--VRONSKY'S POV" -> {"is_scene_heading":true,"scene_id":null,"setting":"exterior","location":"Starting Post, The Races","time_of_day":"Day","temporal_modifiers":["Same Time"],"shot_modifiers":["Vronsky's POV"]}
- "7B # INT. EVENT HORIZON - AIRLOCK BAY NO. 3 - NIGHT 4 - A SHORT TIME LATER   *" -> {"is_scene_heading":true,"scene_id":"7B","setting":"interior","location":"Event Horizon, Airlock Bay No. 3","time_of_day":"Night","temporal_modifiers":["A short time Later", "Night 4"],"shot_modifiers":[]}
- "I N T .   A I R J E T   -   U P P E R   D E C K   -   B U S I N E S S   -   A I S L E   -   C O N T I N U I N G" -> {"is_scene_heading":true,"scene_id":null,"setting":"interior","location":"Air Jet, Upper Deck, Business, Aisle","time_of_day":null,"temporal_modifiers":["Continuing"],"shot_modifiers":[]}
- "INT. VAN - NIGHT - ESTABLISHING" -> {"is_scene_heading":true,"scene_id":null,"setting":"interior","location":"Van","time_of_day":"Night","temporal_modifiers":null,"shot_modifiers":["Establishing Shot"]}
- "25 B. NEIGHBORHOOD: PROSPERIDAD, VALLEGAS OR LA LATINA. EXT. NIGHT." -> {"is_scene_heading":true,"scene_id":"25 B","setting":"exterior","location":"Neighborhood: Prosperidad, Vallegas or La Latina","time_of_day":"Night","temporal_modifiers":null,"shot_modifiers":null}

TASK:
1. Determine if the input text is a scene heading;
1A. If it is not, return only {"is_scene_heading": false}.
1B. If it is, extract the elements from the scene heading and return them in a structured format.

"""


class SceneHeading(BaseModel):
    is_scene_heading: bool = Field(description="Indicates if the input is a scene heading")
    scene_id: str | None = Field(None, description="AlphanumericIdentifier for the scene", examples=["b34", "127"])
    setting: Literal["interior", "exterior", "both"] | None = Field(
        None, description="The setting of the scene, indicating whether it is interior, exterior or both"
    )
    location: str | None = Field(
        None,
        description="Location of the scene, regrouping all location-related information into a single field",
        examples=["Behind German Lines, Mass Grave", "CIA, Front Parking Lot"],
    )
    time_of_day: str | None = Field(
        None, description="Time when the scene takes place", examples=["Day", "Dawn", "Evening"]
    )
    temporal_modifiers: list[str] | None = Field(
        None,
        description="Any temporal modifiers for the scene",
        examples=[
            "18 months later",
            "March 1918",
            "Flashback",
            "Continuous",
        ],
    )
    shot_modifiers: list[str] | None = Field(
        None, description="Any shot modifiers for the scene", examples=["Medium Shot", "Close on Brice", "Monochrome"]
    )

    def dump_json_with_slugline(self, slugline: str) -> str:
        data = self.model_dump()
        data["scene_heading"] = slugline
        return json.dumps(data)


def build_prompt(slugline: str):
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": slugline}]


def annotate_sluglines(sluglines_filepath: Path, output_folderpath: Path, url: str, model_name: str, **client_kwargs):
    output_folderpath.mkdir(parents=True, exist_ok=True)
    output_filepath = output_folderpath / f"{sluglines_filepath.stem}_annotated.jsonl"
    output_filepath_errors = output_folderpath / f"{sluglines_filepath.stem}_errors.jsonl"

    client = OpenAI(base_url=url, **client_kwargs)

    with output_filepath.open("a", encoding="utf-8") as out_fh, output_filepath_errors.open(
        "a", encoding="utf-8"
    ) as out_fh_er, sluglines_filepath.open("r", encoding="utf-8") as in_fh:
        n_sluglines = sum(1 for _ in in_fh)
        in_fh.seek(0)
        for slugline in tqdm(in_fh, total=n_sluglines):
            response = client.chat.completions.parse(
                model=model_name,
                messages=build_prompt(slugline),
                response_format=SceneHeading,
            )
            try:
                scene_heading = SceneHeading.model_validate_json(response.choices[0].message.content)
                scene_heading_string = scene_heading.dump_json_with_slugline(slugline)
                out_fh.writelines(scene_heading_string + "\n")
                out_fh.flush()
            except:
                print("Failed to process slugline:", slugline)
                print("response:", response.choices[0].message.content)
                out_fh_er.writelines(json.dumps({"scene_heading": slugline}) + "\n")
                out_fh_er.flush()
