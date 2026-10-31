#!/usr/bin/env python3
"""Build fictional, code-drawn input and an executable story example."""
from pathlib import Path
import argparse
import json
import subprocess
from PIL import Image, ImageDraw
from route_story import inventory, dump, font, binary
from tone_bed import create

def make(out):
    out=Path(out).resolve();media=out/'input/media';media.mkdir(parents=True,exist_ok=True)
    specs=[('01-harbor.jpg','FICTIONAL HARBOR','#86bac5'),('02-market.jpg','SYNTHETIC MARKET','#d49b64'),
           ('03-hills.jpg','ILLUSTRATED HILLS','#82a47a'),('04-window.jpg','DEMO WINDOW','#a8c8d2')]
    for i,(name,label,color) in enumerate(specs):
        size=(1000,1400) if i==1 else (1600,1000)
        im=Image.new('RGB',size,'#f7efdd');d=ImageDraw.Draw(im);w,h=size
        d.rectangle((0,h*.45,w,h),fill=color)
        d.ellipse((w*.70,h*.10,w*.82,h*.29),fill='#efce76')
        for j in range(9):
            x=j*w/9;y=h*(.34+(j%3)*.03)
            d.rectangle((x,y,x+w*.065,h*.62),fill=['#b98265','#e4c792','#729b88'][j%3])
            d.polygon([(x-w*.01,y),(x+w*.032,y-h*.06),(x+w*.075,y)],fill='#526d74')
        d.text((w/2,h*.80),label,font=font(48),anchor='mm',fill='#17394c')
        im.save(media/name,quality=91)
    video=media/'05-demo-motion.mp4'
    subprocess.run([binary('ffmpeg'),'-y','-v','error','-loop','1','-i',str(media/'04-window.jpg'),'-t','4',
                    '-vf','scale=960:600,zoompan=z=1+0.0003*on:x=iw/2-iw/zoom/2:y=ih/2-ih/zoom/2:d=1:s=960x600:fps=24',
                    '-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p',str(video)],check=True)
    create(media/'06-original-review-score.wav',40)
    (out/'input/BRIEF.md').write_text('This is a fictional, code-drawn demonstration. No real trip or personal experience is claimed.\n')
    ledger=inventory(out/'input',out/'ledger.json');ids={Path(a['path']).name:a['id'] for a in ledger['assets']}
    c1={'id':'bay','title':'Aster Bay · Fictional','date':'Day 1','themes':['Street life','Waterfront'],
        'map_geometry':'schematic','terrain':'coastal','nodes':[{'id':'entry','label':'Arrival','x':.12,'y':.68},
        {'id':'market','label':'Market','x':.28,'y':.25},{'id':'pier','label':'Pier','x':.72,'y':.59}], 'route':['entry','market','pier']}
    c2={'id':'hill','title':'Cedar Hill · Fictional','date':'Day 2','themes':['Open space','Departure'],
        'map_geometry':'schematic','palette':'forest','terrain':'mountain','nodes':[{'id':'trail','label':'Trail','x':.17,'y':.30},
        {'id':'overlook','label':'Overlook','x':.72,'y':.66}], 'route':['trail','overlook']}
    def s(ident,kind,duration,**kw):return dict(id=ident,kind=kind,duration=duration,**kw)
    scenes=[s('opening','intro',2,title='A Small Journey',subtitle='Synthetic example · no real personal story'),
        s('bay-map','map',2,chapter='bay',at='entry'),s('walk-to-market','move',1.5,chapter='bay',**{'from':'entry','to':'market'}),
        s('market-detail','photo',4,chapter='bay',at='market',topic='Street life',asset=ids['02-market.jpg'],caption='A closer look at the market',evidence=[ids['02-market.jpg']]),
        s('walk-to-water','move',1.5,chapter='bay',**{'from':'market','to':'pier'}),
        s('harbor-view','photo',4,chapter='bay',at='pier',topic='Waterfront',asset=ids['01-harbor.jpg'],caption='The route opens toward the water',evidence=[ids['01-harbor.jpg']],anchor='left'),
        s('between-regions','transition',2,title='From the bay to the hills',subtitle='A fictional change of scene'),
        s('hill-map','map',2,chapter='hill',at='trail'),s('hill-detail','photo',4,chapter='hill',at='trail',topic='Open space',asset=ids['03-hills.jpg'],caption='Green slopes and open sky',evidence=[ids['03-hills.jpg']]),
        s('hill-walk','move',1.5,chapter='hill',**{'from':'trail','to':'overlook'}),
        s('window-motion','video',3.5,chapter='hill',at='overlook',topic='Departure',asset=ids['05-demo-motion.mp4'],caption='An illustrated window on the journey',evidence=[ids['05-demo-motion.mp4']],source_in=.2),
        s('closing-thought','note',5,chapter='hill',title='Story connection',text=['Two regions, two rhythms.','The map connects them; the details make each distinct.'],evidence=[ids['01-harbor.jpg'],ids['03-hills.jpg']]),
        s('farewell','outro',3,title='Until the next journey',subtitle='Fictional demonstration')]
    duration=sum(x['duration'] for x in scenes)
    plan={'schema_version':1,'title':'A Small Journey','mode':'one-shot','intake_status':'ready','size':[1280,720],'fps':24,
          'target_seconds':40,'chapters':[c1,c2],'scenes':scenes,'music':[{'asset':ids['06-original-review-score.wav'],
          'start':0,'duration':duration,'target_lufs':-20,'fade_in':.8,'fade_out':1.2}],
          'assumptions':['All places and imagery are fictional.','Diagram positions are not geographic coordinates.','Music is an original synthetic review bed.']}
    dump(out/'story.json',plan)
    print(json.dumps({'plan':str(out/'story.json'),'ledger':str(out/'ledger.json'),'duration':duration},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);make(p.parse_args().out)
