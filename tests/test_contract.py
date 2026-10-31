"""Meaningful storyboard failure cases; no real/private media is needed."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('route_story',ROOT/'skills/route-story/scripts/route_story.py')
rs=importlib.util.module_from_spec(spec);spec.loader.exec_module(rs)

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.ledger={'root':'/nonexistent-input','assets':[{'id':'photo','path':'p.jpg','kind':'image','status':'ok'},
            {'id':'video','path':'v.mp4','kind':'video','status':'ok','duration':5,'has_audio':True}]}
        self.plan={'mode':'one-shot','fps':24,'size':[1280,720],'target_seconds':12,
            'chapters':[{'id':'c','nodes':[{'id':'a','x':.2,'y':.2},{'id':'b','x':.7,'y':.7}],'route':['a','b']}],
            'scenes':[{'id':'map','kind':'map','chapter':'c','duration':2},
                {'id':'travel','kind':'move','chapter':'c','from':'a','to':'b','duration':1},
                {'id':'detail','kind':'video','chapter':'c','asset':'video','at':'b','duration':4,'source_in':.5,
                 'caption':'A visible detail','evidence':['video']} ]}
    def test_valid_frame_budget(self):
        r=rs.validate(self.plan,self.ledger);self.assertTrue(r['ok']);self.assertEqual(r['frames'],168)
    def test_trim_must_fit(self):
        self.plan['scenes'][-1]['source_in']=2
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_negative_trim_rejected(self):
        self.plan['scenes'][-1]['source_in']=-1
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_map_topology_rejected(self):
        self.plan['scenes'][1]['to']='unknown'
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_closed_intake_is_enough(self):
        self.plan['mode']='interactive';self.plan['intake_status']='collecting'
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
        self.plan['intake_status']='ready'
        self.assertTrue(rs.validate(self.plan,self.ledger)['ok'])
    def test_caption_needs_traceable_evidence(self):
        self.plan['scenes'][-1]['evidence']=[]
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_no_escape_from_asset_root(self):
        self.ledger['assets'][0]['path']='../outside.jpg'
        with self.assertRaisesRegex(ValueError,'escapes'):rs.resolve_asset(self.ledger,'photo')
    def test_redaction_invalid_bounds(self):
        self.plan['scenes'][-1]['redactions']=[[.8,.2,.3,.4]]
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_target_not_silently_exceeded(self):
        self.plan['target_seconds']=3
        self.assertFalse(rs.validate(self.plan,self.ledger)['ok'])
    def test_portrait_long_caption_fits_actual_card(self):
        renderer=rs.Renderer(self.plan,self.ledger)
        scene={'id':'portrait-regression','kind':'photo','duration':4}
        renderer.media_card(Image.new('RGBA',(1280,720)),Image.new('RGB',(300,900),'#cbb68a'),
                            '金色礼车的层层纹饰，换到餐桌看见另一种颜色',scene,2,rs.PALETTES['paper'])
        layout=renderer.layouts['portrait-regression']
        self.assertTrue(layout['caption_fits'])
        self.assertLessEqual(layout['maximum_text_width']+2*layout['caption_padding'],layout['card_size'][0])

if __name__=='__main__':unittest.main()
