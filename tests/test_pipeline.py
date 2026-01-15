import unittest
import pandas as pd
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eligibility_pipeline import EligibilityPipeline


class TestEligibilityPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.config_path = Path(__file__).parent.parent / 'config' / 'partners_config.yaml'
        cls.pipeline = EligibilityPipeline(str(cls.config_path))
    
    def test_config_loading(self):
        self.assertIsNotNone(self.pipeline.config)
        self.assertIn('partners', self.pipeline.config)
        self.assertIn('acme_health', self.pipeline.config['partners'])
        self.assertIn('better_care', self.pipeline.config['partners'])
    
    def test_phone_standardization(self):
        test_cases = [
            ('5551234567', '555-123-4567'),
            ('555-987-6543', '555-987-6543'),
            ('(555) 654-3210', '555-654-3210'),
            ('555.321.6547', '555-321-6547'),
            ('555 999 8888', '555-999-8888'),
        ]
        
        for input_phone, expected in test_cases:
            result = self.pipeline._standardize_phone(input_phone)
            self.assertEqual(result, expected, f"Failed for: {input_phone}")
    
    def test_date_standardization(self):
        result = self.pipeline._standardize_date('01/15/1985', '%m/%d/%Y', '%Y-%m-%d')
        self.assertEqual(result, '1985-01-15')
        
        result = self.pipeline._standardize_date('1988-06-12', '%Y-%m-%d', '%Y-%m-%d')
        self.assertEqual(result, '1988-06-12')
    
    def test_acme_health_processing(self):
        result_df = self.pipeline.process_partner('acme_health')
        
        self.assertGreater(len(result_df), 0)
        
        required_columns = ['external_id', 'first_name', 'last_name', 'dob', 
                          'email', 'phone', 'partner_code']
        for col in required_columns:
            self.assertIn(col, result_df.columns)
        
        self.assertEqual(result_df['partner_code'].iloc[0], 'ACME')
        self.assertTrue(result_df['first_name'].iloc[0].istitle())
        self.assertTrue(result_df['last_name'].iloc[0].istitle())
        self.assertTrue(result_df['email'].iloc[0].islower())
        
        phone = result_df['phone'].iloc[0]
        self.assertRegex(phone, r'^\d{3}-\d{3}-\d{4}$')
        
        dob = result_df['dob'].iloc[0]
        self.assertRegex(dob, r'^\d{4}-\d{2}-\d{2}$')
    
    def test_better_care_processing(self):
        result_df = self.pipeline.process_partner('better_care')
        
        self.assertGreater(len(result_df), 0)
        self.assertEqual(result_df['partner_code'].iloc[0], 'BTRC')
        self.assertTrue(result_df['first_name'].iloc[0].istitle())
        self.assertTrue(result_df['email'].iloc[0].islower())
    
    def test_all_partners_processing(self):
        result_df = self.pipeline.process_all_partners()
        
        self.assertGreater(len(result_df), 0)
        
        partner_codes = result_df['partner_code'].unique()
        self.assertIn('ACME', partner_codes)
        self.assertIn('BTRC', partner_codes)
        
        required_columns = ['external_id', 'first_name', 'last_name', 'dob', 
                          'email', 'phone', 'partner_code']
        for col in required_columns:
            self.assertIn(col, result_df.columns)


class TestTransformations(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        config_path = Path(__file__).parent.parent / 'config' / 'partners_config.yaml'
        cls.pipeline = EligibilityPipeline(str(config_path))
    
    def test_edge_case_phone_numbers(self):
        self.assertEqual(self.pipeline._standardize_phone(None), "")
        self.assertEqual(self.pipeline._standardize_phone(""), "")
        
        result = self.pipeline._standardize_phone("15551234567")
        self.assertEqual(result, "555-123-4567")
    
    def test_edge_case_dates(self):
        result = self.pipeline._standardize_date("invalid", "%m/%d/%Y", "%Y-%m-%d")
        self.assertEqual(result, "invalid")


if __name__ == '__main__':
    unittest.main()
