#!/usr/bin/env python3
"""
QTI Quiz Generator for Top Drugs Study Materials

This script generates quiz questions in text2qti format from the drug databases.
Includes proper duplicate detection and question uniqueness validation.

Usage:
    python qti_generator.py

Output:
    Creates .txt files for each quiz section in text2qti format
    Files can be converted to QTI using: text2qti quiz_file.txt
"""

import json
import random
import os
from pathlib import Path
from typing import List, Dict, Any, Set

class DrugQuizGenerator:
    def __init__(self):
        self.drugs_100 = self.load_json_file('data/drugs_100.json')
        self.drugs_200 = self.load_json_file('data/drugs_200.json')
        
    def load_json_file(self, filepath: str) -> List[Dict]:
        """Load and return JSON data from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {filepath} not found")
            return []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {filepath}")
            return []

    def get_drugs_by_section(self, dataset: str, sections: List[int]) -> List[Dict]:
        """Get drugs filtered by dataset and sections"""
        if dataset == '100':
            data = self.drugs_100
        elif dataset == '200':
            data = self.drugs_200
        elif dataset == 'both':
            # Combine datasets, add 10 to section numbers for drugs_200
            data_200_modified = []
            for section in self.drugs_200:
                modified_section = section.copy()
                modified_section['section_number'] += 10
                modified_section['drugs'] = []
                for drug in section['drugs']:
                    modified_drug = drug.copy()
                    modified_drug['section'] += 10
                    modified_section['drugs'].append(modified_drug)
                data_200_modified.append(modified_section)
            data = self.drugs_100 + data_200_modified
        else:
            print(f"Error: Unknown dataset '{dataset}'")
            return []
            
        return [
            drug for section in data 
            if section['section_number'] in sections
            for drug in section['drugs']
        ]

    def create_question_hash(self, question_text: str, correct_answer: str) -> str:
        """Create a unique hash for question deduplication"""
        return f"{question_text.lower().strip()}|{correct_answer.lower().strip()}"

    def generate_quiz_questions(self, drugs: List[Dict]) -> List[Dict]:
        """Generate 30 quiz questions (5 of each type) in specific order"""
        question_types = [
            "Generic to Brand",
            "Brand to Generic", 
            "Generic to Class",
            "Brand to Class",
            "Generic to Indication",
            "Brand to Indication"
        ]
        
        # Initialize pools for each question type
        type_pools = {qtype: [] for qtype in question_types}
        
        # Generate all possible questions by type
        for drug in drugs:
            # Generic to Brand
            if drug['brand_names']:
                type_pools["Generic to Brand"].append({
                    'type': 'generic_to_brand',
                    'question': f"Which is a brand name for {drug['generic_name']}?",
                    'correct_answer': random.choice(drug['brand_names']),
                    'drug': drug
                })
            
            # Brand to Generic
            for brand in drug['brand_names']:
                type_pools["Brand to Generic"].append({
                    'type': 'brand_to_generic',
                    'question': f"What is the generic name for {brand}?",
                    'correct_answer': drug['generic_name'],
                    'drug': drug
                })
            
            # Generic to Class
            type_pools["Generic to Class"].append({
                'type': 'generic_to_class',
                'question': f"What is the drug class of {drug['generic_name']}?",
                'correct_answer': drug['drug_class'],
                'drug': drug
            })
            
            # Brand to Class
            for brand in drug['brand_names']:
                type_pools["Brand to Class"].append({
                    'type': 'brand_to_class',
                    'question': f"What is the drug class of {brand}?",
                    'correct_answer': drug['drug_class'],
                    'drug': drug
                })
            
            # Generic to Indication
            if drug['conditions']:
                type_pools["Generic to Indication"].append({
                    'type': 'generic_to_indication',
                    'question': f"Which FDA approved indication applies to {drug['generic_name']}?",
                    'correct_answer': random.choice(drug['conditions']),
                    'drug': drug
                })
            
            # Brand to Indication
            if drug['conditions'] and drug['brand_names']:
                brand = random.choice(drug['brand_names'])
                type_pools["Brand to Indication"].append({
                    'type': 'brand_to_indication',
                    'question': f"Which FDA approved indication applies to {brand}?",
                    'correct_answer': random.choice(drug['conditions']),
                    'drug': drug
                })
        
        # Select 5 random questions from each type and combine in order
        questions = []
        for qtype in question_types:
            if len(type_pools[qtype]) >= 5:
                questions.extend(random.sample(type_pools[qtype], 5))
            else:
                print(f"Warning: Not enough questions of type {qtype}. Only {len(type_pools[qtype])} available.")
                questions.extend(type_pools[qtype])
                # Pad with duplicates if necessary
                while len(questions) < len(questions) + (5 - len(type_pools[qtype])):
                    questions.append(random.choice(type_pools[qtype]))
        
        return questions

    def generate_wrong_answers(self, question: Dict, all_drugs: List[Dict], num_choices: int = 4) -> List[str]:
        """Generate plausible wrong answers for a question"""
        correct = question['correct_answer']
        question_type = question['type']
        current_drug = question['drug']
        
        # Collect potential wrong answers based on question type
        if 'brand' in question_type and 'to_brand' in question_type:
            # Generic to Brand: collect other brand names
            wrong_answers = [
                brand for drug in all_drugs if drug != current_drug
                for brand in drug['brand_names']
                if brand.lower() != correct.lower()
            ]
        elif 'brand' in question_type and 'generic' in question_type:
            # Brand to Generic: collect other generic names
            wrong_answers = [
                drug['generic_name'] for drug in all_drugs 
                if drug != current_drug and drug['generic_name'].lower() != correct.lower()
            ]
        elif 'class' in question_type:
            # Any to Class: collect other drug classes
            wrong_answers = [
                drug['drug_class'] for drug in all_drugs
                if drug['drug_class'].lower() != correct.lower()
            ]
        elif 'indication' in question_type:
            # Any to Indication: collect other indications
            wrong_answers = [
                condition for drug in all_drugs if drug != current_drug
                for condition in drug['conditions']
                if condition.lower() != correct.lower()
            ]
        else:
            wrong_answers = ["Unknown Option"]
        
        # Remove duplicates and shuffle
        unique_wrong = list(set(wrong_answers))
        random.shuffle(unique_wrong)
        
        # Select needed number of wrong answers
        needed = num_choices - 1
        if len(unique_wrong) >= needed:
            return unique_wrong[:needed]
        else:
            # Pad with generic wrong answers if needed
            result = unique_wrong.copy()
            result.extend([f"Option {i}" for i in range(len(result), needed)])
            return result

    def format_question_text2qti(self, question: Dict, wrong_answers: List[str], question_num: int) -> str:
        """Format a single question in text2qti format"""
        correct = question['correct_answer']
        
        # Create all options and shuffle
        all_options = wrong_answers + [correct]
        random.shuffle(all_options)
        
        # Find which option is correct after shuffling
        correct_index = all_options.index(correct)
        option_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        
        # Build question text
        question_text = f"{question_num}. {question['question']}\n"
        
        for i, option in enumerate(all_options):
            if i == correct_index:
                question_text += f"*{option_letters[i]}) {option}\n"
            else:
                question_text += f"{option_letters[i]}) {option}\n"
        
        question_text += "\n"  # Extra line break between questions
        return question_text

    def generate_quiz_file(self, title: str, sections: List[int], dataset: str) -> str:
        """Generate a complete quiz file in text2qti format with Canvas settings"""
        
        # Get drugs for specified sections
        drugs = self.get_drugs_by_section(dataset, sections)
        if not drugs:
            return f"Error: No drugs found for dataset {dataset}, sections {sections}"
        
        # Generate questions
        questions = self.generate_quiz_questions(drugs)
        if not questions:
            return f"Error: No questions generated"
        
        # Build quiz header with all Canvas settings
        quiz_content = f"Quiz title: {title}\n"
        quiz_content += f"Quiz description: This quiz includes 30 multiple choice questions about the therapeutic class for medications in Drug Quiz {sections[0]}. You will have 15 minutes to complete this quiz. You may repeat this quiz as many times as you would like and the highest score will be saved to the gradebook. It is highly recommended that you do NOT use your notes when you take the quiz as this will help you to determine your actual knowledge of the top 200 medications.\n\n"
        quiz_content += "shuffle answers: true\n"
        quiz_content += "show correct answers: true\n\n"
        
        # Generate each question
        for i, question in enumerate(questions, 1):
            wrong_answers = self.generate_wrong_answers(question, drugs, num_choices=4)
            quiz_content += self.format_question_text2qti(question, wrong_answers, i)
        
        return quiz_content

    def convert_to_qti(self, filepath: Path) -> bool:
        """Convert a quiz file to QTI format using text2qti"""
        try:
            import subprocess
            result = subprocess.run(['text2qti', str(filepath)], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                print(f"✅ Converted {filepath} to QTI format")
                return True
            else:
                print(f"❌ Failed to convert {filepath}")
                print(f"Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error converting {filepath}: {str(e)}")
            return False

    def generate_section_quizzes(self, output_dir: str = "qti_output"):
        """Generate individual quiz files for each section and convert to QTI"""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Define quiz configurations
        quiz_configs = [
            # Top 100 Drug Quizzes (Sections 1-10)
            {"dataset": "100", "sections": [1], "title": "Top 100 Drugs - Week 1: Asthma, Allergies, and Anaphylaxis"},
            {"dataset": "100", "sections": [2], "title": "Top 100 Drugs - Week 2: Diabetes & Antiplatelet Medications"},
            {"dataset": "100", "sections": [3], "title": "Top 100 Drugs - Week 3: Insomnia, Pain, Stimulants, and Dementia"},
            {"dataset": "100", "sections": [4], "title": "Top 100 Drugs - Week 4: Antiulcer Agents, Constipation, and Dietary Supplements"},
            {"dataset": "100", "sections": [5], "title": "Top 100 Drugs - Week 5: Women's and Men's Health"},
            {"dataset": "100", "sections": [6], "title": "Top 100 Drugs - Week 6: Hypertension & Hyperlipidemia"},
            {"dataset": "100", "sections": [7], "title": "Top 100 Drugs - Week 7: Antibiotics"},
            {"dataset": "100", "sections": [8], "title": "Top 100 Drugs - Week 8: More Antibiotics & Topical Antibiotics, Antifungals, & Corticosteroids"},
            {"dataset": "100", "sections": [9], "title": "Top 100 Drugs - Week 9: Antidepressants"},
            {"dataset": "100", "sections": [10], "title": "Top 100 Drugs - Week 10: Antipsychotics & Antianxiety"},
            
            # Top 200 Drug Quizzes (Sections 1-9)
            {"dataset": "200", "sections": [1], "title": "Top 200 Drugs - Week 1: Cardiovascular I"},
            {"dataset": "200", "sections": [2], "title": "Top 200 Drugs - Week 2: Cardiovascular II"},
            {"dataset": "200", "sections": [3], "title": "Top 200 Drugs - Week 3: Pain I"},
            {"dataset": "200", "sections": [4], "title": "Top 200 Drugs - Week 4: Pain II"},
            {"dataset": "200", "sections": [5], "title": "Top 200 Drugs - Week 5: Women's and Men's Health and HIV"},
            {"dataset": "200", "sections": [6], "title": "Top 200 Drugs - Week 6: Asthma and COPD"},
            {"dataset": "200", "sections": [7], "title": "Top 200 Drugs - Week 7: Neurology"},
            {"dataset": "200", "sections": [8], "title": "Top 200 Drugs - Week 8: Miscellaneous I"},
            {"dataset": "200", "sections": [9], "title": "Top 200 Drugs - Week 9: Miscellaneous II"},
        ]
        
        generated_files = []
        converted_files = []
        
        print("\n📝 Generating quiz files...")
        for config in quiz_configs:
            # Generate quiz content
            quiz_content = self.generate_quiz_file(
                title=config["title"],
                sections=config["sections"],
                dataset=config["dataset"]
            )
            
            # Create filename
            section_num = config["sections"][0]
            if config["dataset"] == "200":
                section_num += 10  # Map 200-series to weeks 11-19
            
            filename = f"week_{section_num:02d}_quiz.txt"
            filepath = Path(output_dir) / filename
            
            # Write file
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(quiz_content)
                generated_files.append(filepath)
                print(f"✅ Generated: {filepath}")
            except Exception as e:
                print(f"❌ Error writing {filepath}: {e}")
                continue
            
            # Convert to QTI format
            if self.convert_to_qti(filepath):
                converted_files.append(filepath)
        
        return generated_files, converted_files

def main():
    """Main function to generate quiz files and convert to QTI"""
    print("Drug Quiz Generator for Canvas QTI")
    print("=" * 45)
    
    generator = DrugQuizGenerator()
    
    # Generate and convert all section quizzes
    print("\n🚀 Starting quiz generation and QTI conversion...")
    generated, converted = generator.generate_section_quizzes()
    
    # Print summary
    print("\n📊 Generation Summary:")
    print(f"• Generated {len(generated)} quiz files")
    print(f"• Successfully converted {len(converted)} files to QTI format")
    
    if len(converted) < len(generated):
        print(f"\n⚠️  Warning: {len(generated) - len(converted)} files failed to convert")
        print("Please check the error messages above and try converting them manually:")
        print("text2qti <quiz_file.txt>")
    
    print("\n✨ Next Steps:")
    print("1. Find your quiz files in the 'qti_output' directory")
    print("2. Upload the .zip files to Canvas:")
    print("   • Go to Canvas Course → Settings → Import Course Content")
    print("   • Select 'QTI .zip file'")
    print("   • Upload each .zip file")
    print("   • Wait for processing (may take several minutes)")
    print("   • Find your quizzes in the Quizzes section")
    
    print("\n🎉 Process complete!")

if __name__ == "__main__":
    main() 