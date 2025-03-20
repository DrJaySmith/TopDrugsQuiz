import json
import logging
from pathlib import Path

def clean_field(value: str) -> list:
    """Clean and split semicolon-separated values"""
    return [v.strip() for v in value.split(',') if v.strip()]

def convert_txt_to_json(input_file: str, output_file: str):
    """Convert drug data from TXT to structured JSON with sections"""
    sections = []
    current_section = None
    error_count = 0
    line_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers (lines containing only a number)
                if line.isdigit():
                    current_section = int(line)
                    sections.append({
                        "section_number": current_section,
                        "drugs": []
                    })
                    continue
                
                # Process drug entries
                line_count += 1
                parts = [p.strip() for p in line.split(';', 6)]
                
                if len(parts) != 7:
                    logging.error(f"Line {line_num}: Invalid format - {line}")
                    error_count += 1
                    continue
                
                try:
                    drug = {
                        "generic_name": parts[0],
                        "brand_names": clean_field(parts[1]),
                        "drug_class": parts[5],
                        "conditions": clean_field(parts[6]),
                        "section": current_section
                    }
                    if current_section is not None:
                        sections[-1]["drugs"].append(drug)
                    else:
                        logging.warning(f"Line {line_num}: Drug before first section - {line}")
                except Exception as e:
                    logging.error(f"Line {line_num}: Parsing error - {e}")
                    error_count += 1

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2)
            
        print(f"Converted {sum(len(s['drugs']) for s in sections)} drugs in {len(sections)} sections")
        if error_count > 0:
            print(f"Encountered {error_count} errors (see error.log)")
            
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(
        filename='error.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    convert_txt_to_json(
        input_file='top_100_Drugs_formatted.txt',
        output_file='data/drugs_100.json'
    )
    convert_txt_to_json(
        input_file='top_Drugs_formatted_all200.txt',
        output_file='data/drugs_200.json'
    )