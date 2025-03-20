import re
from pathlib import Path


def clean_transcript(text):
    # Enhanced regex pattern for timestamp removal
    timestamp_pattern = r'([0-9:]*)'

    lines = []
    for line in text.split('\n'):
        # Remove timestamp prefixes while preserving text
        cleaned_line = re.sub(timestamp_pattern, '', line.strip(), flags=re.VERBOSE)
        if cleaned_line:
            lines.append(cleaned_line)
    # Join and clean remaining text
    return re.sub(r'\s+', ' ', ' '.join(lines))



def process_transcripts(input_dir, output_file):
    combined = []

    # Get all TXT files in the directory
    input_files = list(Path(input_dir).glob('*.txt'))

    for file_path in input_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            combined.append(clean_transcript(content))

    # Combine with paragraph spacing
    final_text = '\n\n'.join(combined)

    with open(Path(input_dir) / output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
    print(f"Combined transcripts saved to: {Path(input_dir) / output_file}")


# Use raw string for Windows paths
transcript_path = r"C:\Users\Jeremy.Smith\OneDrive - Michigan Medicine\Desktop\PharmD\P1 Winter\Course Materials\PS518 Dispersed and Solid Forms\Lectures\Unit 2\Transcripts"

process_transcripts(
    input_dir=transcript_path,
    output_file='PharmSci518_Unit2_combined_transcripts.txt'
)
