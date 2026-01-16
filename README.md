```md
# Healthcare Eligibility Pipeline

This project standardizes eligibility files from multiple healthcare partners into one clean, unified output format.

Each partner may send their eligibility data in a different layout (different delimiter, different column names, different formatting). This pipeline reads each partner file using a configuration file, applies consistent cleaning rules, and produces a single standardized CSV that downstream systems can easily consume.

---

## What this pipeline does

For every partner input file, the pipeline:

1. Reads the file using the delimiter defined in the partner configuration  
2. Renames partner specific columns into a standard set of columns  
3. Applies required formatting rules (name, DOB, email, phone)  
4. Adds a `partner_code` field to track the source of each record  
5. Combines all partners into one final output file  

This design keeps the logic reusable and makes onboarding new partners simple.

---

## Standard Output Schema

The pipeline generates a standardized CSV with these columns:

| Column Name   | Description |
|--------------|------------|
| external_id   | Member identifier from the partner file |
| first_name    | Standardized to Title Case |
| last_name     | Standardized to Title Case |
| dob           | Standardized to `YYYY-MM-DD` |
| email         | Standardized to lowercase |
| phone         | Standardized to `XXX-XXX-XXXX` |
| partner_code  | Partner identifier (ex: `ACME`, `BETTERCARE`) |

---

## Transformations Applied

The pipeline applies the following transformations to ensure consistent data formatting across partners:

### Name formatting
- `first_name` and `last_name` are converted to Title Case  
Example: `jOhN` → `John`

### Date of birth formatting
- `dob` is converted to ISO format: `YYYY-MM-DD`  
Examples:  
- `03/15/1955` → `1955-03-15`  
- `1965-08-10` → `1965-08-10`

### Email formatting
- `email` is converted to lowercase  
Example: `JOHN.DOE@EMAIL.COM` → `john.doe@email.com`

### Phone formatting
- `phone` is standardized to: `XXX-XXX-XXXX`  
Examples:  
- `5551234567` → `555-123-4567`  
- `555-222-3333` → `555-222-3333`

### Partner identification
- A `partner_code` column is appended to every record based on the partner configuration

---

## Project Structure

```

Healthcare-Eligibility-Pipeline/
├── src/
│   └── eligibility_pipeline.py
├── config/
│   └── partners_config.yaml
├── sample_data/
│   ├── acme.txt
│   └── bettercare.csv
├── output/
│   └── standardized_eligibility.csv
├── requirements.txt
└── README.md

````

---

## How to Run the Pipeline

### 1) Clone the repository
```bash
git clone https://github.com/NoopuraVaidya/Healthcare-Eligibility-Pipeline.git
cd Healthcare-Eligibility-Pipeline
````

### 2) Create and activate a virtual environment (recommended)

#### Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the pipeline

```bash
python src/eligibility_pipeline.py
```

### 5) View the output

After running successfully, the standardized file will be created at:

```
output/standardized_eligibility.csv
```

You can preview the output in terminal using:

```bash
head output/standardized_eligibility.csv
```

---

## How to Add a New Partner

This pipeline is configuration driven, so onboarding a new partner does not require changing the main pipeline logic.

To add a new partner:

### Step 1: Add the partner configuration

Open:

```
config/partners_config.yaml
```

Add a new section with the following fields:

* `file_path`: path to the partner’s eligibility file
* `delimiter`: delimiter used in the file (`,`, `|`, `\t`, etc.)
* `partner_code`: short identifier to store in the final output
* `column_mapping`: mapping from the partner columns to the standard schema

Example:

```yaml
new_partner:
  file_path: sample_data/new_partner.csv
  delimiter: ","
  partner_code: NEWPARTNER
  column_mapping:
    member_id: external_id
    fname: first_name
    lname: last_name
    birth_date: dob
    email_address: email
    phone_number: phone
```

### Step 2: Add the partner input file

Place the partner file in the location referenced in `file_path`, for example:

```
sample_data/new_partner.csv
```

### Step 3: Run the pipeline again

```bash
python src/eligibility_pipeline.py
```

The new partner will automatically be included in the combined standardized output.

---

## Testing and Validation

The pipeline was validated end to end using the provided sample input files to confirm:

* each partner file is parsed correctly using its configured delimiter
* all transformations are applied correctly
* the final output schema matches the expected standardized format

---

## Tech Stack

* Python 3
* Pandas
* PyYAML

```
::contentReference[oaicite:0]{index=0}
```
