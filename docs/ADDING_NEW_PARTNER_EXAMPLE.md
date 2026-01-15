# Adding a New Partner - Step-by-Step Example

This guide demonstrates how to add a third partner (Wellness Corp) to the pipeline **without modifying any code**.

## Scenario

**Wellness Corp** has provided a new eligibility file with:
- Format: CSV (comma-delimited)
- Date format: YYYY/MM/DD
- Different column names than our existing partners

## Step 1: Examine the New Partner's File

File: `sample_data/wellnesscorp.csv`

```csv
provider_key,given_name,family_name,birth_date,email_addr,telephone
WC-9001,ALICE,thompson,1991/08/20,ALICE.THOMPSON@EMAIL.COM,555.111.2222
WC-9002,bob,JACKSON,1987/03/15,Bob.Jackson@email.com,(555) 333-4444
```

**Observations:**
- Delimiter: `,` (comma)
- ID column: `provider_key`
- Name columns: `given_name`, `family_name`
- Date column: `birth_date` (format: YYYY/MM/DD)
- Email column: `email_addr`
- Phone column: `telephone`

## Step 2: Update Configuration

Open `config/partners_config.yaml` and add the new partner:

```yaml
partners:
  # ... existing partners (acme_health, better_care) ...
  
  wellness_corp:
    partner_code: "WLNS"
    input_file: "sample_data/wellnesscorp.csv"
    file_format:
      type: "delimited"
      delimiter: ","
      header: true
      encoding: "utf-8"
    column_mapping:
      external_id: "provider_key"
      first_name: "given_name"
      last_name: "family_name"
      dob: "birth_date"
      email: "email_addr"
      phone: "telephone"
    transformations:
      dob:
        input_format: "%Y/%m/%d"  # Note: YYYY/MM/DD format
        output_format: "%Y-%m-%d"
      phone:
        input_pattern: "various"
        output_format: "XXX-XXX-XXXX"
```

### Configuration Breakdown

| Config Field | Value | Explanation |
|-------------|-------|-------------|
| `partner_code` | "WLNS" | Unique 4-letter identifier for Wellness Corp |
| `input_file` | "sample_data/wellnesscorp.csv" | Path to their data file |
| `delimiter` | "," | Comma-separated values |
| `column_mapping` | See above | Maps their column names to our standard names |
| `dob.input_format` | "%Y/%m/%d" | Their date format (YYYY/MM/DD with slashes) |

## Step 3: Run the Pipeline

No code changes needed! Just run:

```bash
python src/eligibility_pipeline.py
```

## Step 4: Verify the Output

Check `output/standardized_eligibility.csv`:

```csv
external_id,first_name,last_name,dob,email,phone,partner_code
ACM001,John,Doe,1985-01-15,john.doe@email.com,555-123-4567,ACME
BC1001,Sarah,Williams,1988-06-12,sarah.w@email.com,555-789-0123,BTRC
WC-9001,Alice,Thompson,1991-08-20,alice.thompson@email.com,555-111-2222,WLNS
WC-9002,Bob,Jackson,1987-03-15,bob.jackson@email.com,555-333-4444,WLNS
```

**Success!** The new partner's data is:
- Names converted to Title Case
- Emails converted to lowercase
- Dates formatted as ISO-8601 (YYYY-MM-DD)
- Phone numbers formatted as XXX-XXX-XXXX
- Partner code added (WLNS)

## Step 5: Process Only the New Partner (Optional)

To test just the new partner:

```bash
python src/eligibility_pipeline.py --partner wellness_corp
```

## Common Scenarios

### Scenario 1: Tab-Delimited File

```yaml
file_format:
  delimiter: "\t"  # Tab character
```

### Scenario 2: No Header Row

```yaml
file_format:
  header: false
# You'll need to specify column positions instead of names
```

### Scenario 3: Different Date Format

| Format | `input_format` |
|--------|---------------|
| MM-DD-YYYY | "%m-%d-%Y" |
| DD/MM/YYYY | "%d/%m/%Y" |
| YYYYMMDD | "%Y%m%d" |
| Mon DD, YYYY | "%b %d, %Y" |

### Scenario 4: Different Encoding

```yaml
file_format:
  encoding: "latin-1"  # or "iso-8859-1", etc.
```

## Validation Checklist

After adding a new partner, verify:

- [ ] Configuration syntax is valid (YAML formatting)
- [ ] File path is correct and file exists
- [ ] Delimiter matches the actual file format
- [ ] Column names in mapping match the file headers exactly
- [ ] Date format string matches the actual date format
- [ ] Partner code is unique (not used by other partners)
- [ ] Pipeline runs without errors
- [ ] Output contains expected number of records
- [ ] All transformations applied correctly

## Troubleshooting

### Error: "KeyError: 'column_name'"
**Cause**: Column name in mapping doesn't match file header  
**Fix**: Check exact spelling and case of column names in the file

### Error: "time data '...' does not match format"
**Cause**: Date format string doesn't match actual dates  
**Fix**: Verify the date format in the file and update `input_format`

### Warning: "Invalid phone number format"
**Cause**: Phone numbers don't have 10 digits  
**Fix**: Check if numbers include country codes or extensions

## Summary

Adding Wellness Corp required:
- 0 lines of code changed
- 1 configuration block added (15 lines of YAML)
- Less than 5 minutes of work

This demonstrates the power of configuration-driven design.
