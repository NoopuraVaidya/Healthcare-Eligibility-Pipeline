from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import yaml
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SparkEligibilityPipeline:
    
    def __init__(self, config_path: str, spark: SparkSession = None):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.base_dir = self.config_path.parent.parent
        
        if spark is None:
            self.spark = SparkSession.builder \
                .appName("HealthcareEligibilityPipeline") \
                .config("spark.sql.adaptive.enabled", "true") \
                .getOrCreate()
        else:
            self.spark = spark
    
    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Config loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            raise
    
    def _standardize_phone_udf(self):
        def standardize_phone(phone):
            if not phone:
                return ""
            
            import re
            digits = re.sub(r'\D', '', str(phone))
            
            if len(digits) == 10:
                return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
            else:
                return str(phone)
        
        return F.udf(standardize_phone, StringType())
    
    def _read_partner_file(self, partner_name: str, partner_config: dict):
        file_path = str(self.base_dir / partner_config['input_file'])
        file_format = partner_config['file_format']
        
        try:
            df = self.spark.read \
                .option("header", "true" if file_format.get('header', True) else "false") \
                .option("delimiter", file_format['delimiter']) \
                .option("encoding", file_format.get('encoding', 'utf-8')) \
                .csv(file_path)
            
            logger.info(f"Read {df.count()} records from {partner_name}")
            return df
        except Exception as e:
            logger.error(f"Failed to read {partner_name}: {e}")
            raise
    
    def _map_columns(self, df, column_mapping: dict):
        reverse_mapping = {v: k for k, v in column_mapping.items()}
        
        select_exprs = [
            F.col(partner_col).alias(standard_col)
            for partner_col, standard_col in reverse_mapping.items()
            if partner_col in df.columns
        ]
        
        return df.select(select_exprs)
    
    def _apply_transformations(self, df, partner_config: dict):
        result_df = df
        
        if 'first_name' in result_df.columns:
            result_df = result_df.withColumn('first_name', F.initcap(F.col('first_name')))
        
        if 'last_name' in result_df.columns:
            result_df = result_df.withColumn('last_name', F.initcap(F.col('last_name')))
        
        if 'email' in result_df.columns:
            result_df = result_df.withColumn('email', F.lower(F.col('email')))
        
        if 'dob' in result_df.columns:
            dob_config = partner_config['transformations']['dob']
            input_format = dob_config['input_format'].replace('%', '')
            spark_format = input_format.replace('Y', 'y').replace('D', 'd')
            
            result_df = result_df.withColumn(
                'dob',
                F.date_format(F.to_date(F.col('dob'), spark_format), 'yyyy-MM-dd')
            )
        
        if 'phone' in result_df.columns:
            phone_udf = self._standardize_phone_udf()
            result_df = result_df.withColumn('phone', phone_udf(F.col('phone')))
        
        result_df = result_df.withColumn('partner_code', F.lit(partner_config['partner_code']))
        
        return result_df
    
    def process_partner(self, partner_name: str):
        logger.info(f"Processing {partner_name}")
        
        partner_config = self.config['partners'][partner_name]
        
        raw_df = self._read_partner_file(partner_name, partner_config)
        mapped_df = self._map_columns(raw_df, partner_config['column_mapping'])
        standardized_df = self._apply_transformations(mapped_df, partner_config)
        
        logger.info(f"Processed {partner_name}")
        
        return standardized_df
    
    def process_all_partners(self):
        all_dfs = []
        
        for partner_name in self.config['partners'].keys():
            try:
                partner_df = self.process_partner(partner_name)
                all_dfs.append(partner_df)
            except Exception as e:
                logger.error(f"Failed to process {partner_name}: {e}")
                continue
        
        if not all_dfs:
            raise ValueError("No partner data processed")
        
        combined_df = all_dfs[0]
        for df in all_dfs[1:]:
            combined_df = combined_df.union(df)
        
        output_columns = self.config['output']['columns']
        combined_df = combined_df.select(output_columns)
        
        total_count = combined_df.count()
        logger.info(f"Processed {total_count} records from {len(all_dfs)} partners")
        
        return combined_df
    
    def save_output(self, df, output_format: str = None):
        output_config = self.config['output']
        output_path = str(self.base_dir / output_config['path'])
        format_type = output_format or output_config.get('format', 'csv')
        
        try:
            if format_type == 'csv':
                df.coalesce(1).write.mode('overwrite').option('header', 'true').csv(output_path)
            elif format_type == 'parquet':
                df.write.mode('overwrite').parquet(output_path)
            elif format_type == 'delta':
                df.write.mode('overwrite').format('delta').save(output_path)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            logger.info(f"Output saved to {output_path}")
        except Exception as e:
            logger.error(f"Save failed: {e}")
            raise
    
    def run(self, output_format: str = None):
        logger.info("Starting Spark pipeline")
        
        standardized_data = self.process_all_partners()
        self.save_output(standardized_data, output_format)
        
        logger.info("Pipeline completed")
        
        return standardized_data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Healthcare Eligibility Pipeline (PySpark)')
    parser.add_argument('--config', type=str, default='config/partners_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--partner', type=str, help='Process specific partner only')
    parser.add_argument('--format', type=str, choices=['csv', 'parquet', 'delta'],
                       help='Output format')
    
    args = parser.parse_args()
    
    pipeline = SparkEligibilityPipeline(args.config)
    
    if args.partner:
        result_df = pipeline.process_partner(args.partner)
        result_df.show(10, truncate=False)
    else:
        result_df = pipeline.run(args.format)
        print(f"\nCompleted! Total records: {result_df.count()}")
        result_df.show(10, truncate=False)


if __name__ == "__main__":
    main()
