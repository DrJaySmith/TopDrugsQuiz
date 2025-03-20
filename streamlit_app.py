import streamlit as st
import json
import random
from pathlib import Path

# Initialize session state
def initialize_session():
    st.session_state.update({
        'selected': {
            'dataset': '200',
            'sections': list(range(1, 11)),  # Default to 1-10
            'quiz_types': [
                "Generic to Brand",
                "Brand to Generic",
                "Generic to Class",
                "Brand to Class",
                "Generic to Indication",
                "Brand to Indication"
            ],
            'num_questions': 20
        },
        'questions': [],
        'current_question': 0,
        'score': 0,
        'show_answer': False,
        'current_drug': None,
        'selected_answer': None,
        'quiz_started': False  # Add this flag
    })

def restart_quiz():
    st.session_state.clear()
    initialize_session()
    st.rerun()


def load_drugs(dataset):
    """Load drugs from selected dataset and sections"""
    try:
        # Modified filename handling for combined dataset
        filename = 'data/drugs_both.json' if dataset == 'Both' \
                  else f'data/drugs_{dataset}.json'
        
        with open(filename, 'r') as f:
            data = json.load(f)
            
        # Filter sections based on selection
        return [drug for section in data
                if section['section_number'] in st.session_state.selected['sections']
                for drug in section['drugs']]
                
    except FileNotFoundError:
        st.error(f"Data file not found: {filename}")
        return []


def quiz_setup():
    """Quiz configuration sidebar"""
    with st.sidebar:
        st.header("Quiz Configuration")
        
        num_questions = st.slider(
            "Number of Questions:",
            min_value=5, max_value=50, value=20,
            key='num_questions'
        )

        # New answer choices slider
        num_choices = st.slider(
            "Number of Answer Choices:",
            min_value=2, max_value=10, value=4,
            key='num_choices'
        )
        
        # Dataset selection
        dataset = st.radio(
            "Select Drug Set:",
            ('100', '200', 'Both'),
            key='dataset_select'
        )
        
        # Dynamic section handling
        if dataset == 'Both':
            max_section = 20
            default_sections = list(range(1, 21))
        else:
            max_section = 10
            default_sections = list(range(1, 11))
            
        # Section multiselect
        selected_sections = st.multiselect(
            "Select Sections to Study:",
            options=list(range(1, max_section + 1)),
            default=default_sections,
            key='section_select'
        )
        
        # Ensure at least one section is selected
        if not selected_sections:
            st.error("Please select at least one section")
            st.stop()
        
        # Store selections
        st.session_state.selected.update({
            'dataset': dataset,
            'sections': selected_sections
        })
        
        quiz_types = [
            "Generic to Brand",
            "Brand to Generic",
            "Generic to Class",
            "Brand to Class",
            "Generic to Indication",
            "Brand to Indication"
        ]
        selected_quiz_types = st.multiselect(
            "Select Question Types:",
            options=quiz_types,
            default=quiz_types,
            key='type_select'
        )
        
        st.session_state.selected = {
            'dataset': dataset,
            'sections': selected_sections,
            'quiz_types': selected_quiz_types,
            'num_questions': num_questions,
            'num_choices': num_choices  # Store choices
        }
        

def initialize_quiz():
    """Generate quiz questions"""
    drugs = load_drugs(st.session_state.selected['dataset'])
    
    if not drugs:
        st.error("No drugs found in selected sections")
        st.session_state.quiz_started = False
        st.rerun()
    
    question_pool = []
    num_choices = st.session_state.selected['num_choices']
    
    for drug in drugs:
        if "Generic to Brand" in st.session_state.selected['quiz_types']:
            options = get_brand_options(drugs, drug, num_choices)
            if len(options) == num_choices:
                question_pool.append({
                    'type': 'generic_to_brand',
                    'question': f"Brand names for {drug['generic_name']}?",
                    'answer': drug['brand_names'],
                    'drug': drug,
                    'options': options
                })

        if "Brand to Generic" in st.session_state.selected['quiz_types']:
            for brand in drug['brand_names']:
                question_pool.append({
                    'type': 'brand_to_generic',
                    'question': f"Generic name for {brand}?",
                    'answer': [drug['generic_name']],
                    'drug': drug,
                    'options': get_generic_options(drugs, drug, num_choices)
                })
                # Generic to Class
        if "Generic to Class" in st.session_state.selected['quiz_types']:
            question_pool.append({
                'type': 'generic_to_class',
                'question': f"Class of {drug['generic_name']}?",
                'answer': [drug['drug_class']],
                'drug': drug,
                'options': get_class_options(drugs, drug, num_choices)
            })
        
        # Brand to Class
        if "Brand to Class" in st.session_state.selected['quiz_types']:
            for brand in drug['brand_names']:
                question_pool.append({
                    'type': 'brand_to_class',
                    'question': f"Class of {brand}?",
                    'answer': [drug['drug_class']],
                    'drug': drug,
                    'options': get_class_options(drugs, drug, num_choices)
                })
        
        # Generic to Indication (updated)
        if "Generic to Indication" in st.session_state.selected['quiz_types'] and drug['conditions']:
            correct_answer = random.choice(drug['conditions'])
            options = get_indication_options(drugs, correct_answer, num_choices)
            if len(options) == num_choices:  # Changed from 4 to num_choices
                question_pool.append({
                    'type': 'generic_to_indication',
                    'question': f"Which FDA indication applies to {drug['generic_name']}?",
                    'answer': [correct_answer],
                    'drug': drug,
                    'options': options
                })

        # Brand to Indication (updated)
        if "Brand to Indication" in st.session_state.selected['quiz_types'] and drug['conditions']:
            for brand in drug['brand_names']:
                correct_answer = random.choice(drug['conditions'])
                options = get_indication_options(drugs, correct_answer, num_choices)
                if len(options) == num_choices:  # Changed from 4 to num_choices
                    question_pool.append({
                        'type': 'brand_to_indication',
                        'question': f"Which FDA indication applies to {brand}?",
                        'answer': [correct_answer],
                        'drug': drug,
                        'options': options
                    })
        # Add shuffle and session state update
    random.shuffle(question_pool)
    st.session_state.update({
        'questions': question_pool[:st.session_state.selected['num_questions']],
        'current_question': 0,
        'score': 0
    })


def get_brand_options(drugs, current_drug, num_choices):
    """Generate brand name options with safe sampling"""
    correct = current_drug['brand_names']
    others = list({
        b for d in drugs
        for b in d['brand_names']
        if d != current_drug and b not in correct
    })
    
    remaining = max(num_choices - len(correct), 0)
    sampled = []
    
    if others:
        sample_size = min(remaining, len(others))
        sampled = random.sample(others, sample_size)
        remaining -= sample_size
        
        if remaining > 0:
            sampled += random.choices(others, k=remaining)
    else:
        sampled = ["Unknown"] * remaining
    
    options = correct + sampled
    random.shuffle(options)
    return options[:num_choices]

def get_generic_options(drugs, current_drug, num_choices):
    """Generate generic name options with dynamic choice count"""
    others = [d['generic_name'] for d in drugs if d != current_drug]
    
    try:
        # Get required number of wrong answers (total choices - 1 correct)
        wrong_answers = random.sample(others, num_choices - 1)
    except ValueError:
        # If not enough unique options, use random choices with fallback
        wrong_answers = random.choices(others, k=num_choices - 1) if others else ["Unknown"] * (num_choices - 1)
    
    options = [current_drug['generic_name']] + wrong_answers
    random.shuffle(options)
    return options[:num_choices]

def get_class_options(drugs, current_drug, num_choices):
    """Generate drug class options with dynamic choice count"""
    others = list({d['drug_class'] for d in drugs if d != current_drug})
    
    try:
        wrong_answers = random.sample(others, num_choices - 1)
    except ValueError:
        # Handle insufficient unique classes
        wrong_answers = random.choices(others, k=num_choices - 1) if others else ["Unknown"] * (num_choices - 1)
    
    options = [current_drug['drug_class']] + wrong_answers
    random.shuffle(options)
    return options[:num_choices]

def get_indication_options(drugs, correct_answer, num_choices):
    """Generate indication options with dynamic choice count"""
    others = list({
        cond for drug in drugs
        for cond in drug['conditions']
        if cond != correct_answer
    })
    
    # Calculate needed incorrect answers
    needed_incorrect = num_choices - 1
    
    try:
        incorrect = random.sample(others, needed_incorrect)
    except ValueError:
        # Get as many unique as possible, then fill with duplicates/unknowns
        unique_incorrect = random.sample(others, min(len(others), needed_incorrect)) if others else []
        remaining = needed_incorrect - len(unique_incorrect)
        incorrect = unique_incorrect + random.choices(others, k=remaining) if others else ["Unknown"] * remaining
    
    options = [correct_answer] + incorrect
    random.shuffle(options)
    return options[:num_choices]

def handle_answer(option, question):
    st.session_state.update({
        'selected_answer': option,
        'show_answer': True,
        'current_drug': question['drug']
    })
    st.session_state.score += 1 if option in question['answer'] else 0
    st.rerun()

def display_question():
    """Render current question and handle answers"""
    if st.session_state.current_question >= len(st.session_state.questions):
        st.success(f"Final Score: {st.session_state.score}/{len(st.session_state.questions)}")
        if st.button("🔄 Take Quiz Again"):
            initialize_session()
            st.rerun()
        return

    question = st.session_state.questions[st.session_state.current_question]
    
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.write(f"**{question['question']}**")

    if not st.session_state.show_answer:
        num_cols = 2
        cols = st.columns(num_cols, gap="small")
        chunk_size = (len(question['options']) + num_cols - 1) // num_cols

        for col_idx, col in enumerate(cols):
            with col:
                start_idx = col_idx * chunk_size
                end_idx = start_idx + chunk_size
                for opt_idx, option in enumerate(question['options'][start_idx:end_idx], start=start_idx):
                    # Create unique key with question index, option index, and sanitized text
                    sanitized_text = "".join(c for c in option if c.isalnum())
                    unique_key = f"q{st.session_state.current_question}_opt{opt_idx}_{sanitized_text}"
                    if st.button(option, key=unique_key):
                        handle_answer(option, question)
    else:
        # Show answer feedback
        if st.session_state.selected_answer in question['answer']:
            st.success("Correct! 🎉")
        else:
            st.error(f"Incorrect. Correct answer: {', '.join(question['answer'])}")
        
        # Display drug details
        st.subheader("Drug Information")
        drug = st.session_state.current_drug
        st.markdown(f"""
        - **Generic Name**: {drug['generic_name']}
        - **Brand Names**: {', '.join(drug['brand_names'])}
        - **Drug Class**: {drug['drug_class']}
        - **Indications**: {', '.join(drug['conditions'])}
        """)
        
        if st.button("Next Question →"):
            st.session_state.current_question += 1
            st.session_state.show_answer = False
            st.rerun()

def main():
    st.set_page_config(page_title="Drug Quiz", layout="wide")
    
    if 'selected' not in st.session_state:
        initialize_session()
    
    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Top Drugs Quiz</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add signature
        # Add signature with better positioning
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            text-align: center;
            color: #666;
            padding: 10px;
            z-index: 1000;
        }
        </style>
        
        <div class="footer">
            by Jay Smith, Class of 2028
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.get('quiz_started'):
        # Show configuration in sidebar
        quiz_setup()  # This now only contains the sidebar controls
        
        # Centered start button in main area
        _, center_col, _ = st.columns([1, 3, 1])
        with center_col:
            st.write("\n" * 2)  # Add vertical space
            if st.button(
                "🚀 Start Quiz",
                key="main_start_btn",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.quiz_started = True
                initialize_quiz()
                st.rerun()
            
            # Optional styling for the button
            st.markdown("""
                <style>
                    div[data-testid="stHorizontalBlock"] {
                        justify-content: center;
                    }
                    button[kind="primary"] {
                        padding: 1rem 2rem;
                        font-size: 1.25rem;
                        width: 100%;
                    }
                </style>
            """, unsafe_allow_html=True)
    else:
        display_question()

if __name__ == "__main__":
    main()
