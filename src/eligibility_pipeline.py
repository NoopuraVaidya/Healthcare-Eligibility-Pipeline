import pandas as pd
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EligibilityPipeline:
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.base_dir = self.config_path.parent.parent
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _read_partner_file(self, partner_name: str, partner_config: Dict[str, Any]) -> pd.DataFrame:
        file_path = self.base_dir / partner_config['input_file']
        file_format = partner_config['file_format']
        
        try:
            df = pd.read_csv(
                file_path,
                sep=file_format['delimiter'],
                encoding=file_format.get('encoding', 'utf-8'),
                header=0 if file_format.get('header', True) else None
            )
            logger.info(f"Read {len(df)} records from {partner_name}")
            return df
        except Exception as e:
            logger.error(f"Failed to read {partner_name}: {e}")
            raise
    
    def _standardize_phone(self, phone: str) -> str:
        if pd.isna(phone):
            return ""
        
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 10:
            return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            logger.warning(f"Invalid phone format: {phone}")
            return str(phone)
    
    def _standardize_date(self, date_value: str, input_format: str, output_format: str) -> str:
        if pd.isna(date_value):
            return ""
        
        try:
            date_obj = datetime.strptime(str(date_value), input_format)
            return date_obj.strftime(output_format)
        except Exception as e:
            logger.warning(f"Date parse error for '{date_value}': {e}")
            return str(date_value)
    
    def _apply_transformations(self, df: pd.DataFrame, partner_config: Dict[str, Any]) -> pd.DataFrame:
        result = df.copy()
        
        if 'first_name' in result.columns:
            result['first_name'] = result['first_name'].str.title()
        
        if 'last_name' in result.columns:
            result['last_name'] = result['last_name'].str.title()
        
        if 'email' in result.columns:
            result['email'] = result['email'].str.lower()
        
        if 'dob' in result.columns:
            dob_config = partner_config['transformations']['dob']
            result['dob'] = result['dob'].apply(
                lambda x: self._standardize_date(
                    x, 
                    dob_config['input_format'], 
                    dob_config['output_format']
                )
            )
        
        if 'phone' in result.columns:
            result['phone'] = result['phone'].apply(self._standardize_phone)
        
        result['partner_code'] = partner_config['partner_code']
        
        return result
    
    def _map_columns(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        reverse_mapping = {v: k for k, v in column_mapping.items()}
        mapped_df = df.rename(columns=reverse_mapping)
        
        standard_columns = list(column_mapping.keys())
        available_columns = [col for col in standard_columns if col in mapped_df.columns]
        
        return mapped_df[available_columns]
    
    def process_partner(self, partner_name: str) -> pd.DataFrame:
        logger.info(f"Processing {partner_name}")
        
        partner_config = self.config['partners'][partner_name]
        
        raw_df = self._read_partner_file(partner_name, partner_config)
        mapped_df = self._map_columns(raw_df, partner_config['column_mapping'])
        standardized_df = self._apply_transformations(mapped_df, partner_config)
        
        logger.info(f"Processed {len(standardized_df)} records for {partner_name}")
        
        return standardized_df
    
    def process_all_partners(self) -> pd.DataFrame:
        all_data = []
        
        for partner_name in self.config['partners'].keys():
            try:
                partner_df = self.process_partner(partner_name)
                all_data.append(partner_df)
            except Exception as e:
                logger.error(f"Failed to process {partner_name}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No partner data was processed successfully")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        output_columns = self.config['output']['columns']
        combined_df = combined_df[output_columns]
        
        logger.info(f"Processed {len(combined_df)} total records from {len(all_data)} partners")
        
        return combined_df
    
    def save_output(self, df: pd.DataFrame) -> str:
        output_config = self.config['output']
        output_path = self.base_dir / output_config['path']
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_config['format'] == 'csv':
            df.to_csv(output_path, index=False)
        elif output_config['format'] == 'parquet':
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {output_config['format']}")
        
        logger.info(f"Output saved to {output_path}")
        return str(output_path)
    
    def run(self) -> str:
        logger.info("Starting pipeline")
        
        standardized_data = self.process_all_partners()
        output_path = self.save_output(standardized_data)
        
        logger.info("Pipeline completed")
        
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Healthcare Eligibility Data Pipeline')
    parser.add_argument('--config', type=str, default='config/partners_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--partner', type=str, help='Process specific partner only')
    
    args = parser.parse_args()
    
    pipeline = EligibilityPipeline(args.config)
    
    if args.partner:
        result_df = pipeline.process_partner(args.partner)
        print(f"\nProcessed {len(result_df)} records for {args.partner}")
        print("\nSample output:")
        print(result_df.head())
    else:
        output_path = pipeline.run()
        print(f"\nPipeline completed! Output: {output_path}")


if __name__ == "__main__":
    main()
