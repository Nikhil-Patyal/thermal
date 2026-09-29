import pandas as pd
from django.test import TestCase
from ml.evidence_engine import EvidenceEngine

class MockLandCoverSampler:
    def __init__(self, c, n, v):
        self.c = c
        self.n = n
        self.v = v
        
    def sample(self, lat, lng, scan, track):
        return {
            'cropland_fraction': self.c,
            'tree_fraction': self.n,
            'shrub_fraction': 0.0,
            'grass_fraction': 0.0,
            'other_fraction': max(0.0, 1.0 - self.c - self.n),
            'valid_coverage': self.v,
            'footprint_method': '375mx375m',
            'landcover_source': 'Mock',
            'landcover_version': 'v1'
        }

class LandCoverRulesTestCase(TestCase):
    def setUp(self):
        self.engine = EvidenceEngine()
    
    def test_a_missing_context(self):
        """A. Default missing context: V=0.0"""
        self.engine.sampler = MockLandCoverSampler(c=0.0, n=0.0, v=0.0)
        df = pd.DataFrame([{'id': 1, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['attribution_status'], 'insufficient_landcover')
        self.assertFalse(res['is_tentative'])

    def test_b_pure_agricultural(self):
        """B. Pure agricultural field: V=1.0, C=1.0, N=0.0"""
        self.engine.sampler = MockLandCoverSampler(c=1.0, n=0.0, v=1.0)
        df = pd.DataFrame([{'id': 2, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['label'], 'Likely agricultural burning')
        self.assertEqual(res['label_confidence_str'], 'Moderate')
        self.assertFalse(res['is_tentative'])

    def test_c_pure_forest(self):
        """C. Pure forest: V=1.0, C=0.0, N=1.0"""
        self.engine.sampler = MockLandCoverSampler(c=0.0, n=1.0, v=1.0)
        df = pd.DataFrame([{'id': 3, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['label'], 'Likely wildland vegetation burning')
        self.assertEqual(res['label_confidence_str'], 'Moderate')
        self.assertFalse(res['is_tentative'])

    def test_d_agricultural_dominance(self):
        """D. Agricultural dominance: V=1.0, C=0.75, N=0.15"""
        self.engine.sampler = MockLandCoverSampler(c=0.75, n=0.15, v=1.0)
        df = pd.DataFrame([{'id': 4, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['label'], 'Likely agricultural burning')
        self.assertEqual(res['label_confidence_str'], 'Moderate')
        self.assertFalse(res['is_tentative'])

    def test_e_mixed_leaning_agri(self):
        """E. Mixed landscape leaning agricultural: C=0.45, N=0.20"""
        self.engine.sampler = MockLandCoverSampler(c=0.45, n=0.20, v=1.0)
        df = pd.DataFrame([{'id': 5, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['label'], 'Likely agricultural burning — tentative')
        self.assertEqual(res['label_confidence_str'], 'Low')
        self.assertTrue(res['is_tentative'])

    def test_f_mixed_leaning_natural(self):
        """F. Mixed landscape leaning natural: C=0.20, N=0.45"""
        self.engine.sampler = MockLandCoverSampler(c=0.20, n=0.45, v=1.0)
        df = pd.DataFrame([{'id': 6, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['label'], 'Likely wildland vegetation burning — tentative')
        self.assertEqual(res['label_confidence_str'], 'Low')
        self.assertTrue(res['is_tentative'])

    def test_g_ambiguous_mix(self):
        """G. Ambiguous mix: C=0.40, N=0.40"""
        self.engine.sampler = MockLandCoverSampler(c=0.40, n=0.40, v=1.0)
        df = pd.DataFrame([{'id': 7, 'lat': 20.0, 'lng': 80.0, 'scan': 0.375, 'track': 0.375}])
        res = self.engine.generate_weak_labels(df).iloc[0]
        self.assertEqual(res['attribution_status'], 'needs_additional_evidence')
        self.assertFalse(res['is_tentative'])
