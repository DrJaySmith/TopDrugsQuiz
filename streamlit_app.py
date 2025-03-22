import streamlit as st
import json
import random
from pathlib import Path
# Add to imports
import os
import time
from datetime import datetime
# added for github analytics updating
import requests
from base64 import b64encode, b64decode

# Add analytics constants
ANALYTICS_FILE = "data/enhanced_analytics.json"

def update_github_file(result):
    try: 
        # GitHub credentials from Streamlit secrets
        token = st.secrets["GITHUB_TOKEN"]
        repo = "DrJaySmith/TopDrugsQuiz"
        path = "data/enhanced_analytics.json"
        
        # Get current file contents
        headers = {"Authorization": f"token {token}"}
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        response = requests.get(url, headers=headers)
        
        # Update contents
        current_content = b64decode(response.json()['content']).decode()
        analytics_data = json.loads(current_content)
        analytics_data["quizzes"].append(result)  # Add your new data
        
        # Commit changes
        commit_message = "Update analytics data"
        updated_content = b64encode(json.dumps(analytics_data).encode()).decode()
        data = {
            "message": commit_message,
            "content": updated_content,
            "sha": response.json()["sha"]
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"GitHub API error: {str(e)}")
        return False

def update_github_file_with_retry(result, max_retries=3):
    for attempt in range(max_retries):
        if update_github_file(result):
            return True
        time.sleep(2 ** attempt)
    return False


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
        'analytics_updated': False,  # Add this line
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
            
        return [
            drug
            for section in data
            if section['section_number'] in st.session_state.selected['sections']
            for drug in section['drugs']
        ]
                
    except FileNotFoundError:
        st.error(f"Data file not found: {filename}")
        return []


def quiz_setup():
    """Quiz configuration sidebar"""
    with st.sidebar:
        st.header("Quiz Configuration")
        
        num_questions = st.slider(
            "Number of Questions:",
            min_value=5, max_value=100, value=20,
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
            question_pool.append({
                'type': 'generic_to_brand',
                'question': f"What is the brand names for {drug['generic_name']}?",
                'answer': drug['brand_names'],
                'drug': drug,
                'options': options
            })

        if "Brand to Generic" in st.session_state.selected['quiz_types']:
            for brand in drug['brand_names']:
                question_pool.append({
                    'type': 'brand_to_generic',
                    'question': f"What is the generic name for {brand}?",
                    'answer': [drug['generic_name']],
                    'drug': drug,
                    'options': get_generic_options(drugs, drug, num_choices)
                })
                # Generic to Class
        if "Generic to Class" in st.session_state.selected['quiz_types']:
            question_pool.append({
                'type': 'generic_to_class',
                'question': f"What is the drug class of {drug['generic_name']}?",
                'answer': [drug['drug_class']],
                'drug': drug,
                'options': get_class_options(drugs, drug, num_choices)
            })
        
        # Brand to Class
        if "Brand to Class" in st.session_state.selected['quiz_types']:
            for brand in drug['brand_names']:
                question_pool.append({
                    'type': 'brand_to_class',
                    'question': f"What is the drug class of {brand}?",
                    'answer': [drug['drug_class']],
                    'drug': drug,
                    'options': get_class_options(drugs, drug, num_choices)
                })
        
        # Generic to Indication (updated)
        if "Generic to Indication" in st.session_state.selected['quiz_types'] and drug['conditions']:
            correct_answer = random.choice(drug['conditions'])
            options = get_indication_options(drugs, correct_answer, num_choices)
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
        'score': 0,
        'quiz_start_time': time.time()  # ðŸ‘ˆ Add this line
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
    
    # Combine correct answers with sampled incorrect options
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
    # Add session state validation
    required_keys = ['selected', 'questions', 'current_question', 'score']
    for key in required_keys:
        if key not in st.session_state:
            st.error("Session configuration error. Please restart the quiz.")
            if st.button("ðŸ”„ Restart Quiz"):
                restart_quiz()
            return

    # Validate selected configuration
    selected = st.session_state.selected
    required_config = ['dataset', 'sections', 'quiz_types']
    for key in required_config:
        if key not in selected:
            st.error(f"Missing configuration: {key}. Please restart the quiz.")
            if st.button("ðŸ”„ Restart Quiz"):
                restart_quiz()
            return
    
    if st.session_state.current_question >= len(st.session_state.questions):
        # Only update analytics if not already done for this quiz
        if not st.session_state.get('analytics_updated'):
            result = {
                'score': st.session_state.score,
                'total': len(st.session_state.questions),
                'dataset': st.session_state.selected['dataset'],
                'sections': st.session_state.selected['sections'],
                'question_types': st.session_state.selected['quiz_types'],
                'time_taken': round(time.time() - st.session_state.quiz_start_time, 1)
            }
            update_analytics(result)
            st.session_state.analytics_updated = True  # Flag to prevent duplicates

        st.success(f"Final Score: {st.session_state.score}/{len(st.session_state.questions)}")
        if st.button("ðŸ”„ Take Quiz Again"):
            initialize_session()
            st.rerun()
        return

    question = st.session_state.questions[st.session_state.current_question]
    question['start_time'] = time.time()  # Track question start time
    
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
            st.success("Correct! ðŸŽ‰")
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
        
        if st.button("Next Question â†’"):
            st.session_state.current_question += 1
            st.session_state.show_answer = False
            st.rerun()

def update_analytics(result):
    """Update analytics with detailed tracking"""
    if not update_github_file_with_retry(result):
        st.warning("Failed to update GitHub. Saving locally.")
        save_local_analytics(result)
    save_local_analytics(result)


def save_local_analytics(result):
    try:
        Path("data").mkdir(exist_ok=True)
        analytics = {"quizzes": []}

        # Handle existing data
        if os.path.exists(ANALYTICS_FILE):
            try:
                with open(ANALYTICS_FILE, "r") as f:
                    analytics = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                analytics = {"quizzes": []}

        # Add detailed question tracking
        quiz_data = {
            "timestamp": datetime.now().isoformat(),
            "dataset": result['dataset'],
            "sections": result['sections'],
            "question_types": result['question_types'],
            "score": result['score'],
            "total": result['total'],
            "time_taken": result['time_taken']
        }

        analytics["quizzes"].append(quiz_data)

        with open(ANALYTICS_FILE, "w") as f:
            json.dump(analytics, f, indent=0)

    except Exception as e:
        st.error(f"Analytics update failed: {str(e)}")

# Updated show_minimal_analytics function
def show_minimal_analytics():
    """Enhanced analytics with filters, fetching data from GitHub"""
    with st.sidebar.expander("📊 Advanced Analytics"):
        try:
            # Fetch data from GitHub
            token = st.secrets["GITHUB_TOKEN"]
            repo = "DrJaySmith/TopDrugsQuiz"
            path = "data/enhanced_analytics.json"
            
            headers = {"Authorization": f"token {token}"}
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                st.warning("No analytics data available from GitHub")
                return
            
            content = b64decode(response.json()['content']).decode('utf-8')
            data = json.loads(content)
            
            if not data.get("quizzes"):
                st.warning("No analytics data yet")
                return

            # Filters
            st.subheader("Filters")
            
            # Dataset filter
            dataset = st.radio("Dataset:", 
                             ["All", "100", "200", "Both"],
                             horizontal=True)

            # Process data
            filtered = [q for q in data["quizzes"] if (dataset == "All" or q['dataset'] == dataset)]
            
            if not filtered:
                st.warning("No data matching filters")
                return

            # Calculate metrics
            total_quizzes = len(filtered)
            total_questions = sum(q['total'] for q in filtered)
            correct_answers = sum(q['score'] for q in filtered)
            avg_score = (correct_answers / total_questions) * 100 if total_questions else 0
            
            # Calculate total time
            total_seconds = sum(q['time_taken'] for q in filtered)
            total_minutes = round(total_seconds / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            hours_label = "hour" if hours == 1 else "hours"
            minutes_label = "minute" if minutes == 1 else "minutes"
            time_str = f"{hours} {hours_label}, {minutes} {minutes_label}"

            # Display metrics
            st.markdown('<div class="performance-insights"><h3>Performance Insights</h3></div>', unsafe_allow_html=True)
            col11, col12 = st.columns(2)
            col21, col22 = st.columns(2)
            col11.metric("Total Quizzes", total_quizzes)
            col12.metric("Total Questions", total_questions)
            col21.metric("Average Score", f"{avg_score:.1f}%")
            col22.metric("Total Time Spent", time_str)
        except Exception as e:
            st.error(f"Error loading analytics from GitHub: {str(e)}")


def main():
    st.set_page_config(page_title="Drug Quiz", layout="wide")
    
    if 'selected' not in st.session_state:
        initialize_session()
    
    # Add signature
        # Add signature with better positioning
    st.markdown(
        """
        <style>
        .header {
            position: fixed;
            left: 0;
            top: 0;
            width: 100%;
            text-align: center;
            color: #666;
            padding: 10px;
            z-index: 1000;
        }        
        /* Add padding to prevent content overlap */
        .main .block-container {
            padding-bottom: 2rem;
        }
        </style>
        
        <div class="footer">
            by Jay Smith, Class of 2028
        </div>
        """,
        unsafe_allow_html=True
    )

    # Only show title before quiz starts
    if not st.session_state.get('quiz_started'):
        st.markdown(
            """
            <div style="text-align: center;">
                <h1>Top Drugs Quiz</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

    if not st.session_state.get('quiz_started'):
        # Show configuration in sidebar
        quiz_setup()  # This now only contains the sidebar controls

        # Add analytics toggle to sidebar
        show_minimal_analytics()

        # Centered start button in main area
        _, center_col, _ = st.columns([1, 3, 1])
        with center_col:
            st.write("\n" * 2)  # Add vertical space
            if st.button("ðŸš€ Start Quiz", key="main_start_btn", use_container_width=True, type="primary"):
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