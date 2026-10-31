#!/usr/bin/env python3
"""Portable media inventory, storyboard validation and map-led film rendering.

The agent authors the story. This module only performs reproducible media work.
No accounts, network, private photo-library access or external models required.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
except ImportError:
    raise SystemExit("Pillow is required: python -m pip install Pillow")

IMAGE = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tif', '.tiff'}
VIDEO = {'.mp4', '.mov', '.m4v', '.webm', '.mkv'}
AUDIO = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg'}
TEXT = {'.md', '.txt', '.srt', '.vtt'}
KINDS = {'intro', 'map', 'move', 'photo', 'video', 'note', 'transition', 'outro'}
ASSETS = Path(__file__).resolve().parents[1] / 'assets'
PALETTES = {
    'paper': {'paper': '#f7efdd', 'ink': '#17394c', 'accent': '#d66a4c', 'water': '#93cbd1', 'green': '#91aa88', 'road': '#e3d0ac'},
    'night': {'paper': '#172b38', 'ink': '#f2e9d4', 'accent': '#e7ab62', 'water': '#284e61', 'green': '#426a62', 'road': '#435964'},
    'forest': {'paper': '#edf0dc', 'ink': '#214639', 'accent': '#bd6b47', 'water': '#91bec0', 'green': '#719869', 'road': '#d2d7b6'},
}

def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def binary(name):
    value = os.environ.get('ROUTE_STORY_' + name.upper()) or shutil.which(name)
    if not value:
        raise ValueError(f'{name} is not installed/on PATH; see references/runtime.md')
    return value

def run(args):
    p = subprocess.run(list(map(str, args)), capture_output=True)
    if p.returncode:
        raise ValueError(p.stderr.decode(errors='replace')[-2400:] or str(args))
    return p.stdout

def probe(path):
    return json.loads(run([binary('ffprobe'), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path]))

def font(size, override=None):
    choices = [override, os.environ.get('ROUTE_STORY_FONT'), str(ASSETS / 'fonts/LXGWWenKai-Regular.ttf')]
    for folder in ['/usr/share/fonts', '/usr/local/share/fonts', str(Path.home() / '.fonts'),
                   '/System/Library/Fonts/Supplemental', '/Library/Fonts', 'C:/Windows/Fonts']:
        d = Path(folder)
        if not d.exists():
            continue
        for pattern in ['*NotoSansCJK*', '*NotoSerifCJK*', '*SourceHanSans*', '*Songti*', 'msyh.ttc', 'simsun.ttc', 'DejaVuSans.ttf']:
            choices.extend(str(p) for p in d.rglob(pattern))
    for path in choices:
        if path and Path(path).is_file():
            try:
                return ImageFont.truetype(path, max(10, int(size)))
            except OSError:
                pass
    raise ValueError('No usable font; restore the bundled WenKai font or provide ROUTE_STORY_FONT. Tiny default bitmap type is not a production fallback.')

def defaults():
    return read(ASSETS / 'defaults.json')

def template(name):
    path = ASSETS / name
    if not path.is_file():
        raise ValueError(f'Required illustrated template is missing: {name}; restore the package instead of downgrading the film to a diagram.')
    return path

def curved_segment(a,b,count=48):
    dx,dy=b[0]-a[0],b[1]-a[1];length=max(1,math.hypot(dx,dy));bend=min(36,length*.1)
    cx,cy=(a[0]+b[0])/2-dy/length*bend,(a[1]+b[1])/2+dx/length*bend
    return [((1-q)**2*a[0]+2*(1-q)*q*cx+q*q*b[0],(1-q)**2*a[1]+2*(1-q)*q*cy+q*q*b[1]) for q in [i/count for i in range(count+1)]]

def dash_route(draw,points,fill,width,dash=14,gap=9):
    distance=0
    for a,b in zip(points,points[1:]):
        length=math.dist(a,b);steps=max(1,math.ceil(length/2))
        for i in range(steps):
            q=i/steps;r=(i+1)/steps
            if (distance+length*q)%(dash+gap)<dash:
                draw.line((a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q,a[0]+(b[0]-a[0])*r,a[1]+(b[1]-a[1])*r),fill=fill,width=width)
        distance+=length

def resolve_asset(ledger, asset_id):
    entries = {a['id']: a for a in ledger['assets']}
    if asset_id not in entries:
        raise ValueError(f'Unknown asset ID: {asset_id}')
    root = Path(ledger['root']).resolve()
    path = (root / entries[asset_id]['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Asset escapes the input root: {asset_id}')
    if not path.is_file():
        raise ValueError(f'Asset file is missing: {asset_id}')
    return path, entries[asset_id]

def load_image(path):
    try:
        if Path(path).suffix.lower() in {'.heic', '.heif'}:
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)
            if 'A' in im.getbands():
                bg=Image.new('RGBA',im.size,'#fff8e8');bg.alpha_composite(im.convert('RGBA'));im=bg.convert('RGB')
            else:im=im.convert('RGB')
            # Phone wide-gamut files are converted to sRGB when Pillow has the profile.
            if im.info.get('icc_profile'):
                from PIL import ImageCms
                try:
                    im = ImageCms.profileToProfile(im, io.BytesIO(im.info['icc_profile']), ImageCms.createProfile('sRGB'), outputMode='RGB')
                except (OSError, ValueError):
                    pass
            return im.copy()
    except (OSError, ValueError):
        # Native conversion is optional, never an assumed dependency.
        if sys.platform == 'darwin' and shutil.which('sips'):
            with tempfile.TemporaryDirectory(prefix='route-story-image-') as temp:
                dest = Path(temp) / 'decoded.jpg'
                run(['sips', '-s', 'format', 'jpeg', path, '--out', dest])
                with Image.open(dest) as im:
                    return ImageOps.exif_transpose(im).convert('RGB').copy()
        raw = run([binary('ffmpeg'), '-v', 'error', '-i', path, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'])
        return Image.open(io.BytesIO(raw)).convert('RGB')

def video_frame(path, t, width=960):
    raw = run([binary('ffmpeg'), '-v', 'error', '-ss', max(0, t), '-i', path, '-frames:v', '1',
               '-vf', f'scale={width}:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'])
    return Image.open(io.BytesIO(raw)).convert('RGB')

def inventory(root, out):
    root = Path(root).resolve(); entries = []; index = 0
    if not root.is_dir():
        raise ValueError('Input must be a directory')
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink() or any(p.startswith('.') for p in path.relative_to(root).parts):
            continue
        suffix = path.suffix.lower()
        kind = 'image' if suffix in IMAGE else 'video' if suffix in VIDEO else 'audio' if suffix in AUDIO else 'text' if suffix in TEXT else None
        if not kind:
            continue
        index += 1
        entry = {'id': f'A{index:04d}', 'path': path.relative_to(root).as_posix(), 'kind': kind,
                 'bytes': path.stat().st_size, 'status': 'ok'}
        try:
            if kind == 'image':
                im = load_image(path); entry.update(width=im.width, height=im.height)
                try:
                    with Image.open(path) as original:
                        exif = original.getexif()
                        entry['capture_time'] = exif.get(36867) or exif.get(306)
                        entry['capture_time_zone'] = exif.get(36881) or 'unknown'
                except OSError:
                    pass
            elif kind in {'video', 'audio'}:
                m = probe(path); v = next((s for s in m['streams'] if s['codec_type'] == 'video'), {})
                entry.update(duration=float(m.get('format', {}).get('duration', 0)),
                             width=v.get('width'), height=v.get('height'),
                             capture_time=m.get('format', {}).get('tags', {}).get('creation_time'),
                             has_audio=any(s['codec_type'] == 'audio' for s in m['streams']))
            else:
                content = path.read_text(encoding='utf-8', errors='replace')
                entry['text'] = content; entry['characters'] = len(content)
        except (ValueError, OSError) as e:
            entry.update(status='unreadable', error=str(e)[:400])
        entries.append(entry)
    result = {'schema_version': 1, 'root': str(root), 'assets': entries}
    dump(out, result)
    return result

def contact(ledger, outdir, videos_only=False):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for a in ledger['assets']:
        if a['status'] != 'ok' or a['kind'] not in {'image', 'video'} or (videos_only and a['kind'] != 'video'):
            continue
        path, _ = resolve_asset(ledger, a['id'])
        times = [a['duration'] * q for q in [.1, .35, .6, .85]] if videos_only else [a.get('duration', 0) * .3]
        for t in times:
            try:
                im = load_image(path) if a['kind'] == 'image' else video_frame(path, t, 400)
                tiles.append((a, t, im))
            except (ValueError, OSError):
                continue
    f = font(18); outputs = []
    for page in range(math.ceil(len(tiles) / 24)):
        batch = tiles[page * 24:(page + 1) * 24]
        sheet = Image.new('RGB', (1440, 1100), '#eee9df'); d = ImageDraw.Draw(sheet)
        for i, (a, t, im) in enumerate(batch):
            x = i % 6 * 240; y = i // 6 * 275
            label = a['id'] + (' V ' + f'{t:.1f}s' if a['kind'] == 'video' else '')
            d.text((x + 8, y + 5), label, font=f, fill='#17394c')
            thumb = ImageOps.contain(im, (226, 230), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x + (240 - thumb.width) // 2, y + 32 + (230 - thumb.height) // 2))
        dest = outdir / f'{"video-" if videos_only else ""}contact-{page+1:02d}.jpg'
        sheet.save(dest, quality=91); outputs.append(str(dest))
    return outputs

def validate(plan, ledger):
    errors = []; warnings = []; ids = {a['id']: a for a in ledger['assets']}
    width, height = plan.get('size', [1280, 720]); fps = plan.get('fps', 24)
    if width < 480 or height < 270 or width % 2 or height % 2:
        errors.append('size must use even dimensions, at least 480x270')
    if fps not in [24, 25, 30]:
        errors.append('fps must be 24, 25 or 30')
    chapters = {c['id']: c for c in plan.get('chapters', [])}
    if len(chapters) != len(plan.get('chapters', [])):
        errors.append('chapter IDs must be unique')
    for c in chapters.values():
        nodes = c.get('nodes', []); node_ids = {n['id'] for n in nodes}
        if len(node_ids) != len(nodes):
            errors.append('node IDs must be unique within each chapter')
        for n in nodes:
            if not (0.03 <= n['x'] <= .97 and .03 <= n['y'] <= .97):
                errors.append(f'node {n["id"]} must have normalized x,y in .03..97')
        if c.get('route') and not set(c['route']).issubset(node_ids):
            errors.append(f'chapter {c["id"]}: unknown route node')
        if c.get('map_geometry', 'schematic') not in ['schematic', 'geographic']:
            errors.append('map_geometry must be schematic or geographic')
    scene_ids = set(); frames = 0
    for s in plan.get('scenes', []):
        name = s.get('id', '?'); duration = s.get('duration', 0)
        if name in scene_ids:
            errors.append(f'duplicate scene ID {name}')
        scene_ids.add(name)
        if s.get('kind') not in KINDS:
            errors.append(f'{name}: unknown scene kind')
        if not .25 <= duration <= 45:
            errors.append(f'{name}: duration must be .25..45 seconds')
        frames += round(duration * fps)
        c = chapters.get(s.get('chapter'))
        if s.get('kind') in {'map', 'move', 'photo', 'video', 'note'} and c is None:
            errors.append(f'{name}: chapter is required')
        if c:
            nodes = {n['id'] for n in c.get('nodes', [])}
            for key in ['at', 'from', 'to']:
                if s.get(key) and s[key] not in nodes:
                    errors.append(f'{name}: unknown {key} node {s[key]}')
            if s.get('kind') == 'move' and not all(s.get(k) for k in ['from', 'to']):
                errors.append(f'{name}: move needs from and to')
        if s.get('kind') in {'photo', 'video'}:
            a = ids.get(s.get('asset'))
            if not a or a['status'] != 'ok':
                errors.append(f'{name}: unknown/unreadable asset')
            elif a['kind'] != ('image' if s['kind'] == 'photo' else 'video'):
                errors.append(f'{name}: asset kind does not match scene')
            elif s['kind'] == 'video' and (s.get('source_in', 0) < 0 or s.get('source_in', 0) + duration > a['duration'] + .04):
                errors.append(f'{name}: video trim exceeds original duration; shorten the scene')
            if s.get('caption') and not s.get('evidence'):
                errors.append(f'{name}: caption needs evidence asset IDs')
            for box in s.get('redactions', []) + ([s['crop']] if s.get('crop') else []):
                if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                    errors.append(f'{name}: crop/redaction needs normalized x0,y0,x1,y1 bounds')
        if any(e not in ids for e in s.get('evidence', [])):
            errors.append(f'{name}: evidence refers to unknown asset')
        if s.get('kind') == 'note' and not s.get('evidence'):
            warnings.append(f'{name}: note has no source; use neutral observations, not invented personal feelings')
    if not frames:
        errors.append('at least one scene is required')
    if plan.get('mode') not in ['one-shot', 'interactive']:
        errors.append('mode must be one-shot or interactive')
    if plan.get('mode') == 'interactive' and plan.get('intake_status') != 'ready':
        errors.append('interactive mode may render only after the user closes intake')
    total = frames / fps
    if plan.get('target_seconds') and total > plan['target_seconds'] * 1.1:
        errors.append(f'film {total:.2f}s exceeds target duration by more than 10%')
    for cue in plan.get('music', []):
        if cue.get('duration',0) <= 0 or cue.get('source_in',0) < 0:
            errors.append('music cue needs positive duration and nonnegative source_in')
        a = ids.get(cue.get('asset'))
        if not a or not a.get('has_audio'):
            errors.append('music cue needs an audio-bearing asset')
        elif cue.get('source_in', 0) + cue['duration'] > a['duration'] + .04:
            errors.append('music cue exceeds source duration')
        if cue.get('start', 0) < 0 or cue.get('start', 0) + cue['duration'] > total + .04:
            errors.append('music cue is outside the film')
    return {'ok': not errors, 'errors': errors, 'warnings': warnings, 'frames': frames, 'fps': fps, 'duration': total}

def ease(t):
    t = max(0, min(1, t)); return t * t * (3 - 2 * t)

def wrap(text, f, width):
    result = []; line = ''
    for ch in str(text):
        if ch == '\n':
            result.append(line); line = ''; continue
        if line and f.getlength(line + ch) > width and ch not in '，。！？、：；,.!?;:)]}':
            result.append(line.rstrip()); line = ch.lstrip()
        else:
            line += ch
    if line:
        result.append(line.rstrip())
    return result

class Renderer:
    def __init__(self, plan, ledger):
        self.plan = plan; self.ledger = ledger
        self.w, self.h = plan.get('size', [1280, 720]); self.scale = self.w / 1280
        self.fps = plan.get('fps', 24); self.chapters = {c['id']: c for c in plan['chapters']}
        self.cache = {}; self.backplates = {}; self.fonts = {}; self.layouts = {}

    def f(self, size):
        if size not in self.fonts:
            self.fonts[size] = font(size * self.scale, self.plan.get('font'))
        return self.fonts[size]

    def prepared_media(self,scene,t=0,supplied=None):
        if supplied is not None:media=supplied
        else:
            path,_=resolve_asset(self.ledger,scene['asset'])
            if scene['kind']=='video':media=video_frame(path,scene.get('source_in',0)+t,self.w)
            else:
                if str(path) not in self.cache:self.cache[str(path)]=load_image(path)
                media=self.cache[str(path)]
        if scene.get('redactions'):
            media=media.copy()
            for a,b,c,d in scene['redactions']:
                box=(int(a*media.width),int(b*media.height),int(c*media.width),int(d*media.height))
                region=media.crop(box).resize((max(1,(box[2]-box[0])//22),max(1,(box[3]-box[1])//22)),Image.Resampling.BOX)
                media.paste(region.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.NEAREST),box[:2])
        if scene.get('crop'):
            a,b,c,d=scene['crop'];media=media.crop((int(a*media.width),int(b*media.height),int(c*media.width),int(d*media.height)))
        return media

    def filmstrip(self,im,scene,t):
        covers=[];seen=set()
        for candidate in self.plan['scenes']:
            if candidate['kind']=='photo' and candidate['asset'] not in seen and candidate.get('opening_allow',True):
                covers.append(candidate);seen.add(candidate['asset'])
            if len(covers)==6:break
        if not covers:return im
        w,h=self.w,self.h;d=ImageDraw.Draw(im);sw=int(w*.307);sh=int(h*.365);gap=int(w*.018);y=int(h*.26)
        d.rectangle((0,y-25*self.scale,w,y+sh+25*self.scale),fill='#fff7e7')
        for x in range(5,w,max(10,round(27*self.scale))):
            for yy in [y-17*self.scale,y+sh+12*self.scale]:d.rounded_rectangle((x,yy,x+12*self.scale,yy+6*self.scale),radius=2,fill='#dcc19c')
        start=(w-(3*sw+2*gap))/2;travel=max(0,len(covers)-3)*(sw+gap)*ease(min(1,t/(scene['duration']*.65)))
        for i,candidate in enumerate(covers):
            x=round(start+i*(sw+gap)-travel)
            if x+sw<0 or x>w:continue
            key='cover-'+candidate['id']
            if key not in self.cache:self.cache[key]=ImageOps.fit(self.prepared_media(candidate),(sw,sh),method=Image.Resampling.LANCZOS)
            im.paste(self.cache[key],(x,y))
        wash=Image.new('RGBA',im.size);wd=ImageDraw.Draw(wash)
        wd.rounded_rectangle((w*.10,h*.675,w*.90,h*.84),radius=20,fill=(255,248,232,235))
        im=Image.alpha_composite(im,wash.filter(ImageFilter.GaussianBlur(15)))
        d=ImageDraw.Draw(im);f=self.f(54);title=scene.get('title',self.plan.get('title','A Journey'))
        lines=wrap(title,f,w*.86)
        for i,line in enumerate(lines[:2]):d.text((w/2,h*.72+i*57*self.scale),line,font=f,anchor='mm',fill='#16384c')
        if scene.get('subtitle') and len(lines)==1:d.text((w/2,h*.80),scene['subtitle'],font=self.f(27),anchor='mm',fill='#16384c')
        return im

    def xy(self, node):
        return round(node['x'] * self.w), round((.18 + node['y'] * .68) * self.h)

    def background(self, chapter):
        key = chapter.get('id', 'intro')
        if key in self.backplates:
            return self.backplates[key].copy()
        p = PALETTES.get(chapter.get('palette', self.plan.get('palette', 'paper')), PALETTES['paper'])
        if chapter.get('background_asset'):
            path, _ = resolve_asset(self.ledger, chapter['background_asset'])
            im = ImageOps.fit(load_image(path), (self.w, self.h)).convert('RGBA')
        else:
            preset=defaults();name=preset['maps'].get(chapter.get('terrain','urban'),preset['maps']['urban'])
            im=ImageOps.fit(load_image(template(name)),(self.w,self.h),method=Image.Resampling.LANCZOS).convert('RGBA')
        if chapter.get('palette')=='night':
            night=Image.new('RGBA',im.size,(6,23,40,105));im=Image.alpha_composite(im,night)
        self.backplates[key] = im.copy(); return im

    def map_frame(self, scene, t):
        c = self.chapters[scene['chapter']]
        p = PALETTES.get(c.get('palette', self.plan.get('palette', 'paper')), PALETTES['paper'])
        im = self.background(c); d = ImageDraw.Draw(im); w,h = self.w,self.h
        nodes = {n['id']: n for n in c.get('nodes', [])}; route = c.get('route', list(nodes))
        points = [self.xy(nodes[i]) for i in route]
        if len(points) > 1:
            smooth=[]
            for a,b in zip(points,points[1:]):smooth+=curved_segment(a,b)
            d.line(smooth,fill='#fffbed',width=max(7,round(11*self.scale)),joint='curve')
            dash_route(d,smooth,'#f07b61',max(3,round(4*self.scale)),round(14*self.scale),round(9*self.scale))
            for a,b in zip(points,points[1:]):
                mid=curved_segment(a,b);x,y=mid[len(mid)//2];angle=math.atan2(mid[25][1]-mid[23][1],mid[25][0]-mid[23][0]);r=9*self.scale
                d.polygon([(x+r*math.cos(angle),y+r*math.sin(angle)),
                           (x+r*math.cos(angle+2.5),y+r*math.sin(angle+2.5)),
                           (x+r*math.cos(angle-2.5),y+r*math.sin(angle-2.5))],fill=p['accent'])
        active = scene.get('at')
        for ident,n in nodes.items():
            x,y=self.xy(n);r=9*self.scale; color='#f07b61' if ident==active else p['green']
            d.ellipse((x-r,y-r,x+r,y+r),fill=color,outline=p['paper'],width=2)
            label=n.get('label',ident); f=self.f(28); tw=d.textlength(label,font=f)
            lx=max(12,min(w-tw-12,x-tw/2));ly=y+13*self.scale
            d.rounded_rectangle((lx-10,ly-3,lx+tw+10,ly+35*self.scale),radius=6,fill='#fff8e8')
            d.text((lx,ly),label,font=f,fill=p['ink'])
        if scene['kind']=='move':
            a=self.xy(nodes[scene['from']]);b=self.xy(nodes[scene['to']]);q=ease(t/scene['duration'])
            route_points=curved_segment(a,b);i=min(len(route_points)-2,int(q*(len(route_points)-1)));fraction=q*(len(route_points)-1)-i
            avatar=(route_points[i][0]+(route_points[i+1][0]-route_points[i][0])*fraction,route_points[i][1]+(route_points[i+1][1]-route_points[i][1])*fraction)
        elif active:
            avatar=self.xy(nodes[active])
        else:
            avatar=None
        if avatar:
            x,y=avatar;r=39*self.scale;cy=y-57*self.scale
            d.line((x,cy+r,x,y),fill=p['accent'],width=3)
            d.ellipse((x-r-3,cy-r-3,x+r+3,cy+r+3),fill='#fffbed')
            d.ellipse((x-r,cy-r,x+r,cy+r),fill=p['paper'],outline='#f07b61',width=max(3,round(4*self.scale)))
            if self.plan.get('avatar_asset'):
                asset,_=resolve_asset(self.ledger,self.plan['avatar_asset'])
                face=ImageOps.fit(load_image(asset),(round(r*1.8),round(r*1.8)))
                mask=Image.new('L',face.size);ImageDraw.Draw(mask).ellipse((0,0,face.width-1,face.height-1),fill=255)
                im.paste(face,(round(x-face.width/2),round(cy-face.height/2)),mask)
            else:
                # Anonymous illustrated portrait is part of the production preset.
                avatar_file=template(defaults()['avatar'])
                if 'default-avatar' not in self.cache:self.cache['default-avatar']=load_image(avatar_file)
                source=self.cache['default-avatar'];source=source.crop((source.width*.10,source.height*.02,source.width*.90,source.height*.82))
                face=ImageOps.fit(source,(round(r*1.8),round(r*1.8)),method=Image.Resampling.LANCZOS)
                mask=Image.new('L',face.size);ImageDraw.Draw(mask).ellipse((0,0,face.width-1,face.height-1),fill=255)
                im.paste(face,(round(x-face.width/2),round(cy-face.height/2)),mask)
        title=c.get('title',c['id']);titlefont=self.f(82 if len(title)<=6 else 61);titlelines=wrap(title,titlefont,w*.58)
        if len(titlelines)>2:raise ValueError('Chapter title is too long; move the explanation to its story note')
        cursor=.035*h
        for line in titlelines:
            d.text((.038*w,cursor),line,font=titlefont,anchor='lt',fill=p['ink'])
            bounds=d.textbbox((.038*w,cursor),line,font=titlefont,anchor='lt');cursor=bounds[3]+9*self.scale
        dy=cursor+3*self.scale
        d.line((.038*w,dy,.038*w+min(w*.30,max(d.textlength(x,font=titlefont) for x in titlelines)),dy-3*self.scale),fill='#f07b61',width=max(2,round(3*self.scale)))
        datetext=scene.get('date',c.get('date',''))
        if len(datetext)>26:datetext=''
        d.text((.041*w,dy+9*self.scale),datetext,font=self.f(28),anchor='lt',fill=p['ink'])
        themes=c.get('themes',[])
        if themes:
            x=.035*w
            for theme in themes:
                current=theme==scene.get('topic'); textcolor=p['paper'] if current else p['ink']; f=self.f(25)
                tw=d.textlength(theme,font=f)
                if current:d.rounded_rectangle((x-6,h*.93-4,x+tw+6,h*.93+29*self.scale),radius=4,fill=p['accent'])
                d.text((x,h*.93),theme,font=f,fill=textcolor);x+=tw+28*self.scale
        return im,p

    def media_card(self, im, media, caption, scene, t, p):
        w,h=self.w,self.h;maxw=int(w*scene.get('photo_width',.54));maxh=int(h*.76)
        if scene.get('anchor','right')=='left':maxh=int(h*.70)
        caption=caption.rstrip('。.')
        f=self.f(40);padding=int(14*self.scale)
        lines=wrap(caption,f,maxw-2*padding) if caption else []
        if len(lines)>3:
            raise ValueError(f'{scene["id"]}: caption needs shortening; more than three lines')
        footer=max(int(25*self.scale),int((len(lines)*49+24)*self.scale))
        photo=ImageOps.contain(media,(maxw-2*padding,maxh-footer-padding),Image.Resampling.LANCZOS)
        measured=max([f.getlength(line) for line in lines] or [0])
        cardw=max(photo.width+2*padding,math.ceil(measured)+2*padding)
        if cardw>maxw:
            raise ValueError(f'{scene["id"]}: caption wider than the available card')
        card=Image.new('RGBA',(cardw,photo.height+padding+footer),'#fff9ec')
        card.paste(photo,((card.width-photo.width)//2,padding));d=ImageDraw.Draw(card)
        for i,line in enumerate(lines):
            d.text((card.width/2,photo.height+padding+(i+.5)*49*self.scale+10*self.scale),line,font=f,anchor='mm',fill='#17394c')
        self.layouts[scene['id']]={'card_size':list(card.size),'photo_size':list(photo.size),'caption_lines':lines,
                                  'maximum_text_width':measured,'caption_padding':padding,
                                  'caption_fits':measured<=card.width-2*padding,'photo_aspect_ratio':photo.width/photo.height}
        anchor=scene.get('anchor','right')
        card=card.rotate(scene.get('tilt',-1.4),Image.Resampling.BICUBIC,expand=True)
        arrival=.94+.06*ease(t/.32)
        if arrival<1:card=card.resize((round(card.width*arrival),round(card.height*arrival)),Image.Resampling.LANCZOS)
        x=int(w*.44) if anchor=='right' else int(w*.025) if anchor=='left' else (w-card.width)//2
        x=max(12,min(w-card.width-12,x));y=int(h*.20)+(int(h*.76)-card.height)//2
        if anchor=='left':y=max(y,round(h*.23))
        q=ease(t/.22)*(1-ease((t-scene['duration']+.22)/.22))
        if q<1:card.putalpha(card.getchannel('A').point(lambda a:round(a*q)))
        shadow=Image.new('RGBA',im.size);alpha=Image.new('L',im.size);alpha.paste(card.getchannel('A'),(x+5,y+8));alpha=alpha.filter(ImageFilter.GaussianBlur(9)).point(lambda v:round(v*.24))
        shadow.putalpha(alpha);im=Image.alpha_composite(im,shadow);im.alpha_composite(card,(x,y));return im

    def frame(self, scene, t, supplied_video=None):
        kind=scene['kind'];w,h=self.w,self.h
        if kind in {'intro','outro','transition'}:
            chapter=self.chapters.get(scene.get('chapter'),{'id':'title','terrain':'urban'})
            if 'title-backdrop' not in self.cache:self.cache['title-backdrop']=ImageOps.fit(load_image(template(defaults()['title_background'])),(w,h),method=Image.Resampling.LANCZOS).convert('RGBA')
            im=self.cache['title-backdrop'].copy();d=ImageDraw.Draw(im);p=PALETTES.get(chapter.get('palette','paper'),PALETTES['paper'])
            if kind=='intro' and scene.get('layout','filmstrip')=='filmstrip':return self.filmstrip(im,scene,t).convert('RGB')
            title=scene.get('title',self.plan.get('title','A Journey'));f=self.f(72)
            lines=wrap(title,f,w*.84)
            for i,line in enumerate(lines):d.text((w/2,h*.35+i*76*self.scale),line,font=f,anchor='mm',fill=p['ink'])
            d.line((w*.43,h*.49,w*.57,h*.49),fill='#e79680',width=max(2,round(3*self.scale)))
            subtitle=scene.get('subtitle','');f=self.f(28)
            for i,line in enumerate(wrap(subtitle,f,w*.83)):
                d.text((w/2,h*.59+i*36*self.scale),line,font=f,anchor='mm',fill=p['ink'])
            return im.convert('RGB')
        im,p=self.map_frame(scene,t)
        if kind in {'photo','video'}:
            media=self.prepared_media(scene,t,supplied_video)
            im=self.media_card(im,media,scene.get('caption',''),scene,t,p)
        elif kind=='note':
            layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
            box=(int(w*.16),int(h*.25),int(w*.84),int(h*.83))
            shade=Image.new('RGBA',im.size);sd=ImageDraw.Draw(shade);sd.rounded_rectangle((box[0]+7,box[1]+10,box[2]+7,box[3]+10),radius=10,fill=(30,35,30,90));shade=shade.filter(ImageFilter.GaussianBlur(12));im=Image.alpha_composite(im,shade)
            d.rounded_rectangle(box,radius=10,fill='#fff9ec',outline='#d7c7a7',width=1)
            d.rectangle((int(w*.43),box[1]-8,int(w*.57),box[1]+10),fill=(214,182,137,180))
            d.text((box[0]+w*.035,box[1]+h*.035),scene.get('title','旅途手记'),font=self.f(32),fill='#17394c')
            paragraphs=scene.get('text',[])
            if isinstance(paragraphs,str):paragraphs=paragraphs.split('\n')
            f=self.f(scene.get('text_size',31));y=box[1]+h*.115; content=[]
            for paragraph in paragraphs:content.append(wrap(paragraph,f,box[2]-box[0]-w*.07))
            line_height=40*self.scale
            if sum(len(x) for x in content)*line_height+(len(content)-1)*12*self.scale>box[3]-y-14*self.scale:
                raise ValueError(f'{scene["id"]}: note too dense; shorten/split it rather than shrinking text')
            for i,lines in enumerate(content):
                visible=scene.get('reveal','paragraph')=='instant' or t>=i*scene['duration']*.65/max(1,len(content))
                for line in lines:
                    if visible:d.text((box[0]+w*.035,y),line,font=f,fill='#17394c')
                    y+=line_height
                y+=12*self.scale
            im=Image.alpha_composite(im,layer)
        return im.convert('RGB')

def require_valid(plan,ledger):
    report=validate(plan,ledger)
    if not report['ok']:raise ValueError('\n'.join(report['errors']))
    return report

def keyframes(plan,ledger,outdir):
    require_valid(plan,ledger);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True);r=Renderer(plan,ledger);files=[]
    for i,s in enumerate(plan['scenes']):
        dest=outdir/f'{i+1:02d}-{s["id"]}.png';r.frame(s,s['duration']*.65).save(dest);files.append(str(dest))
    columns=3;tw=480;th=290;sheet=Image.new('RGB',(columns*tw,math.ceil(len(files)/columns)*th),'#ece8de');d=ImageDraw.Draw(sheet)
    for i,file in enumerate(files):
        im=ImageOps.contain(load_image(file),(tw,th-26));x=i%columns*tw;y=i//columns*th
        d.text((x+8,y+4),plan['scenes'][i]['id'],font=font(18),fill='#17394c');sheet.paste(im,(x+(tw-im.width)//2,y+26))
    sheet.save(outdir/'storyboard.jpg',quality=92);dump(outdir/'layout-report.json',r.layouts);return files

def render(plan,ledger,outdir):
    report=require_valid(plan,ledger);outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    r=Renderer(plan,ledger);ff=binary('ffmpeg');w,h=r.w,r.h;fps=r.fps
    silent=outdir/'picture.mp4';dest=outdir/'film.mp4'
    encoder=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-',
        '-an','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-map_metadata','-1','-movflags','+faststart',str(silent)],stdin=subprocess.PIPE)
    timeline=[];total_frames=0
    try:
        for s in plan['scenes']:
            count=round(s['duration']*fps);video=None
            if s['kind']=='video':
                path,_=resolve_asset(ledger,s['asset'])
                sample=video_frame(path,s.get('source_in',0),min(w,768));vw,vh=sample.size
                video=subprocess.Popen([ff,'-v','error','-ss',str(s.get('source_in',0)),'-i',str(path),'-an',
                    '-vf',f'scale={vw}:{vh},fps={fps}',
                    '-frames:v',str(count),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
            try:
                for n in range(count):
                    supplied=None
                    if video:
                        raw=video.stdout.read(vw*vh*3)
                        if len(raw)!=vw*vh*3:raise ValueError(f'{s["id"]}: source video ended before the promised trim')
                        supplied=Image.frombytes('RGB',(vw,vh),raw)
                    encoder.stdin.write(r.frame(s,n/fps,supplied).tobytes())
            finally:
                if video:
                    video.stdout.close();code=video.wait()
                    if code:raise ValueError(f'{s["id"]}: video decoder failed ({code})')
            timeline.append({'scene':s['id'],'kind':s['kind'],'start':total_frames/fps,'end':(total_frames+count)/fps,
                             'frames':count,'asset':s.get('asset'),'evidence':s.get('evidence',[])})
            total_frames+=count
            print(f'rendered {s["id"]}: {count} frames',flush=True)
    finally:
        encoder.stdin.close();code=encoder.wait()
    if code:raise ValueError('video encoder failed')
    mix_music(plan,ledger,silent,dest,timeline,total_frames/fps)
    meta=probe(dest);v=next(s for s in meta['streams'] if s['codec_type']=='video')
    if int(v.get('nb_frames',-1))!=total_frames:raise ValueError('encoded frame count mismatch')
    run([ff,'-v','error','-i',dest,'-f','null','-'])
    dump(outdir/'timeline.json',timeline);dump(outdir/'story.json',plan);dump(outdir/'asset-ledger.json',ledger)
    dump(outdir/'layout-report.json',r.layouts)
    dump(outdir/'validation.json',{**report,'output':str(dest.resolve()),'metadata':meta,'full_decode':'passed'})
    chosen=set(s.get('asset') for s in plan['scenes'])-{None}
    text=['# '+plan.get('title','Route story'),'','Mode: '+plan['mode'],'',f'Duration: {total_frames/fps:.2f}s','',
          '## Story structure','']
    for c in plan['chapters']:text.append('- '+c.get('title',c['id'])+': '+' / '.join(c.get('themes',[])))
    text+=['','## Source use','',f'Selected {len(chosen)} visual assets. Unused assets remain in the original input.','',
           '## Assumptions / gaps','']+['- '+str(x) for x in plan.get('assumptions',[])]
    (outdir/'story.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    r.frame(plan['scenes'][0],1).save(outdir/'poster.png')
    return dest

def mix_music(plan,ledger,silent,dest,timeline,duration):
    cues=list(plan.get('music',[]))
    for s,timing in zip(plan['scenes'],timeline):
        if s['kind']=='video' and s.get('source_audio',False):
            _,a=resolve_asset(ledger,s['asset'])
            if a.get('has_audio'):cues.append({'asset':s['asset'],'start':timing['start'],'source_in':s.get('source_in',0),
                                               'duration':timing['end']-timing['start'],'target_lufs':-20})
    if not cues:
        shutil.copy2(silent,dest);return
    ff=binary('ffmpeg');args=[ff,'-y','-v','error','-i',silent];filters=[];labels=[]
    for i,cue in enumerate(cues,1):
        path,_=resolve_asset(ledger,cue['asset']);args+=['-i',path]
        d=cue['duration'];fi=min(cue.get('fade_in',.6),d/2);fo=min(cue.get('fade_out',.8),d/2)
        label=f'a{i}';labels.append('['+label+']');delay=round(cue.get('start',0)*1000)
        filters.append(f'[{i}:a:0]atrim=start={cue.get("source_in",0)}:duration={d},asetpts=PTS-STARTPTS,'
            f'loudnorm=I={cue.get("target_lufs",-20)}:TP=-2:LRA=11,aresample=48000,'
            f'aformat=channel_layouts=stereo,afade=t=in:d={fi},afade=t=out:st={d-fo}:d={fo},'
            f'adelay={delay}|{delay}[{label}]')
    filters.append(''.join(labels)+f'amix=inputs={len(cues)}:duration=longest:normalize=0,apad,atrim=duration={duration},'
                   'alimiter=limit=0.84:level=false:latency=true[a]')
    run(args+['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k',
              '-t',duration,'-map_metadata','-1','-movflags','+faststart',dest])

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    p=sub.add_parser('inventory');p.add_argument('input');p.add_argument('--out',required=True)
    p=sub.add_parser('contact');p.add_argument('ledger');p.add_argument('--out',required=True);p.add_argument('--video-frames',action='store_true')
    for name in ['validate','keyframes','render']:
        p=sub.add_parser(name);p.add_argument('plan');p.add_argument('--ledger',required=True)
        if name!='validate':p.add_argument('--out',required=True)
    args=parser.parse_args()
    try:
        if args.command=='doctor':
                preset=defaults()
                for name in list(preset['maps'].values())+[preset['title_background'],preset['avatar'],preset['font']]:template(name)
                value={'python':sys.version.split()[0],'ffmpeg':binary('ffmpeg'),'ffprobe':binary('ffprobe'),'font':getattr(font(20),'path','fallback'),'default_design':preset['name'],'illustrated_templates':'present'}
        elif args.command=='inventory':
            v=inventory(args.input,args.out);value={'assets':len(v['assets']),'unreadable':sum(a['status']!='ok' for a in v['assets'])}
        elif args.command=='contact':value=contact(read(args.ledger),args.out,args.video_frames)
        else:
            plan=read(args.plan);ledger=read(args.ledger)
            if args.command=='validate':
                value=validate(plan,ledger)
                if not value['ok']:print(json.dumps(value,ensure_ascii=False,indent=2));return 2
            elif args.command=='keyframes':value=keyframes(plan,ledger,args.out)
            else:value=str(render(plan,ledger,args.out))
        print(json.dumps(value,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError) as e:
        print('route-story: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':
    raise SystemExit(main())
