# Healthcare Eligibility Pipeline - Technical Documentation

## Architecture Overview

### Design Philosophy

This pipeline follows a **configuration-driven architecture** where:
- Business logic is separated from data source specifications
- Adding new partners requires only YAML configuration changes
- Core transformation logic is reusable across all partners
- The system is designed for both small-scale (Pandas) and large-scale (PySpark) processing

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Configuration Layer                      │
│                  (partners_config.yaml)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Pipeline Engine                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Ingestion  │─▶│ Transformation│─▶│    Output    │      │
│  │    Module    │  │    Module     │  │   Module     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Standardized Output                        │
│              (CSV, Parquet, or Delta Lake)                   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ingestion Phase
```python
Partner File (Various Formats)
    │
    ├─ Read with configured delimiter
    ├─ Parse headers
    └─ Load into DataFrame
```

### 2. Transformation Phase
```python
Raw DataFrame
    │
    ├─ Column Mapping (Partner → Standard)
    ├─ Name Standardization (Title Case)
    ├─ Email Normalization (Lowercase)
    ├─ Date Formatting (ISO-8601)
    ├─ Phone Formatting (XXX-XXX-XXXX)
    └─ Add Partner Code
```

### 3. Output Phase
```python
Standardized DataFrame
    │
    ├─ Validate Schema
    ├─ Order Columns
    └─ Write to Output Format
```

## Configuration Schema

### Partner Configuration Structure

```yaml
partners:
  partner_name:
    partner_code: "CODE"           # 4-letter identifier
    input_file: "path/to/file"     # Relative to project root
    file_format:
      type: "delimited"            # File type
      delimiter: ","               # Field separator
      header: true                 # Has header row?
      encoding: "utf-8"            # File encoding
    column_mapping:
      external_id: "partner_id_col"
      first_name: "fname_col"
      # ... other mappings
    transformations:
      dob:
        input_format: "%m/%d/%Y"   # Python strftime format
        output_format: "%Y-%m-%d"  # ISO-8601
      phone:
        input_pattern: "various"
        output_format: "XXX-XXX-XXXX"
```

## Transformation Rules

### Name Standardization
- **Input**: Any case (JOHN, john, JoHn)
- **Output**: Title Case (John)
- **Implementation**: `str.title()` or `F.initcap()`

### Email Normalization
- **Input**: Any case (JOHN@EMAIL.COM, John@Email.com)
- **Output**: Lowercase (john@email.com)
- **Implementation**: `str.lower()` or `F.lower()`

### Date Formatting
- **Input**: Various formats (01/15/1985, 1985-01-15)
- **Output**: ISO-8601 (1985-01-15)
- **Implementation**: Parse with input format → Format as YYYY-MM-DD

### Phone Formatting
- **Input**: Various formats
  - Raw digits: 5551234567
  - Dashes: 555-123-4567
  - Dots: 555.123.4567
  - Parentheses: (555) 123-4567
  - Spaces: 555 123 4567
- **Output**: XXX-XXX-XXXX (555-123-4567)
- **Implementation**: 
  1. Extract all digits
  2. Validate 10-digit format
  3. Format as XXX-XXX-XXXX

## Performance Considerations

### Pandas Version (eligibility_pipeline.py)
- **Best for**: < 1M records per partner
- **Memory**: Loads entire file into memory
- **Parallelism**: Single-threaded
- **Use case**: Development, testing, small datasets

### PySpark Version (eligibility_pipeline_spark.py)
- **Best for**: > 1M records, distributed processing
- **Memory**: Lazy evaluation, distributed processing
- **Parallelism**: Multi-node cluster support
- **Use case**: Production, large datasets, Databricks

## Scalability Features

### 1. Configuration-Driven Design
Adding a new partner requires **zero code changes**:
```yaml
# Just add this to partners_config.yaml
new_partner:
  partner_code: "NEWP"
  input_file: "data/newpartner.csv"
  # ... rest of config
```

### 2. Extensible Transformations
New transformation types can be added by:
1. Adding transformation logic to the pipeline class
2. Referencing it in the configuration
3. No changes to existing partner configs

### 3. Multiple Output Formats
Supports:
- CSV (for compatibility)
- Parquet (for analytics)
- Delta Lake (for data lakes)

## Error Handling

### File Reading Errors
- **Issue**: File not found, encoding issues
- **Handling**: Log error, skip partner, continue with others
- **Recovery**: Fix file path/encoding in config

### Transformation Errors
- **Issue**: Invalid date format, malformed phone
- **Handling**: Log warning, keep original value
- **Recovery**: Update transformation config

### Data Quality Issues
- **Issue**: Missing required fields, null values
- **Handling**: Currently passes through, can add validation
- **Future**: Add data quality rules to config

## Testing Strategy

### Unit Tests
- Test individual transformation functions
- Test configuration loading
- Test column mapping logic

### Integration Tests
- Test end-to-end pipeline with sample data
- Test each partner separately
- Test combined output

### Data Quality Tests
- Verify all transformations applied correctly
- Check for data loss
- Validate output schema

## Deployment Options

### Local Development
```bash
python src/eligibility_pipeline.py
```

### Databricks Notebook
```python
%run ./src/eligibility_pipeline_spark.py
pipeline = SparkEligibilityPipeline('config/partners_config.yaml', spark)
result = pipeline.run()
display(result)
```

### Scheduled Job
```bash
# Cron job or Databricks job
0 2 * * * python /path/to/eligibility_pipeline.py
```

### Airflow DAG
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

def run_pipeline():
    from eligibility_pipeline import EligibilityPipeline
    pipeline = EligibilityPipeline('config/partners_config.yaml')
    pipeline.run()

dag = DAG('eligibility_pipeline', schedule_interval='@daily')
task = PythonOperator(task_id='run', python_callable=run_pipeline, dag=dag)
```

## Future Enhancements

### Data Validation
- Add schema validation
- Implement data quality rules
- Generate data quality reports

### Incremental Processing
- Track processed files
- Process only new/changed data
- Maintain processing history

### Monitoring & Alerting
- Add metrics collection
- Implement alerting for failures
- Create processing dashboards

### Advanced Transformations
- Address standardization
- Name parsing (suffix, prefix)
- Data enrichment from external sources

## Troubleshooting Guide

### Common Issues

**Issue**: Pipeline fails with "File not found"
- **Solution**: Check `input_file` path in config is relative to project root

**Issue**: Dates not parsing correctly
- **Solution**: Verify `input_format` matches actual date format in file

**Issue**: Phone numbers malformed
- **Solution**: Check that input has 10 digits (excluding country code)

**Issue**: Names not in Title Case
- **Solution**: Verify transformation is applied (check logs)

## Best Practices

1. **Always test with sample data first**
2. **Validate configuration before running**
3. **Monitor logs for warnings**
4. **Keep configurations in version control**
5. **Document partner-specific quirks**
6. **Run data quality checks on output**
7. **Maintain separate configs for dev/prod**

## Performance Tuning

### Pandas Version
- Use `dtype` parameter for efficient memory usage
- Process partners in parallel with multiprocessing
- Use chunked reading for very large files

### PySpark Version
- Adjust partition count based on data size
- Use broadcast joins for small lookup tables
- Enable adaptive query execution
- Cache intermediate results if reused

## Security Considerations

- **PHI/PII Data**: This pipeline processes healthcare data
- **Encryption**: Ensure data at rest and in transit is encrypted
- **Access Control**: Restrict access to configuration and data files
- **Audit Logging**: Log all pipeline executions
- **Data Retention**: Follow HIPAA guidelines for data retention
