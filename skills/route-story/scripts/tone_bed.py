#!/usr/bin/env python3
"""Create an original, simple instrumental placeholder; no samples or network.

This is a review aid, not a claim to have composed a finished soundtrack.
Requires NumPy. The output has no vocals or field recording.
"""
import argparse
import math
from pathlib import Path
import wave
import numpy as np

def create(out, seconds=60, bpm=76):
    if not 2 <= seconds <= 900 or not 35 <= bpm <= 160:
        raise ValueError('seconds: 2..900, bpm: 35..160')
    sr=48000; audio=np.zeros((round(seconds*sr),2),np.float32);beat=60/bpm
    chords=[(48,55,60,64),(45,52,57,60),(41,48,53,57),(43,50,55,59)]
    for index,start in enumerate(np.arange(0,seconds,beat)):
        chord=chords[(index//8)%len(chords)];note=chord[index%len(chord)]+(12 if index%8>3 else 0)
        frequency=440*2**((note-69)/12);length=min(2.7,seconds-start);t=np.arange(round(length*sr))/sr
        env=(1-np.exp(-t*55))*np.exp(-t*2.2)
        sound=(np.sin(2*np.pi*frequency*t)+.23*np.sin(2*np.pi*frequency*2*t)+.07*np.sin(2*np.pi*frequency*3*t))*env*.12
        i=round(start*sr);sound=sound[:len(audio)-i]
        pan=.45+.12*math.sin(index*.8)
        audio[i:i+len(sound),0]+=sound*(1-pan);audio[i:i+len(sound),1]+=sound*pan
    for delay,gain in [(.13,.14),(.29,.08),(.43,.035)]:
        k=round(delay*sr);audio[k:]+=audio[:-k].copy()*gain
    fade=min(round(sr*1.5),len(audio)//2);q=np.linspace(0,1,fade)
    audio[:fade]*=q[:,None];audio[-fade:]*=q[::-1,None]
    peak=max(.001,float(np.max(np.abs(audio))));audio*=.65/peak
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((audio*32767).astype('<i2').tobytes())
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--seconds',type=float,default=60);p.add_argument('--bpm',type=float,default=76)
    a=p.parse_args();print(create(a.out,a.seconds,a.bpm))
