#!/usr/bin/env python3
"""Write a soundtrack reference catalogue; never automatically collect audio.

OpenTracks prohibits bot collection. Its pages are human-facing references,
not an automated acquisition endpoint. Use user-provided licensed copies or
another source whose conditions permit the required acquisition and use.
"""
from pathlib import Path
import argparse,json
CATALOG=[
 {'role':'opening','title':'野良猫は宇宙を目指した','artist':'しゃろう','page':'https://opentracks.com/bgm/detail/2862'},
 {'role':'heritage','title':'autumn travel','artist':'のる','page':'https://opentracks.com/bgm/detail/15214'},
 {'role':'city','title':'2:23 AM','artist':'しゃろう','page':'https://opentracks.com/bgm/detail/13494'},
 {'role':'reflection','title':'思い出は遠く響いて','artist':'のる','page':'https://opentracks.com/bgm/detail/21249'}]
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 (out/'soundtrack-reference-catalogue.json').write_text(json.dumps({'status':'reference-only-no-audio-downloaded','terms':'https://opentracks.com/help/articles/terms/','tracks':CATALOG},ensure_ascii=False,indent=2))
 print('Reference catalogue only. No audio requests were made.')
