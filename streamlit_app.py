import streamlit as st  
from utils.quiz_logic import load_questions, validate_answer  

def initialize_session():  
    if 'quiz_active' not in st.session_state:  
        st.session_state.update({  
            'current_question': 0,  
            'score': 0,  
            'selected_answer': None,  
            'show_explanation': False  
        })  

def main():  
    st.set_page_config(page_title="Drugs Quiz", layout="wide")  
    initialize_session()  
    
    st.title("Top 200 Drugs Quiz")  
    st.write("Choose your quiz version:")  
    
    # Quiz selection will go here  
    
if __name__ == "__main__":  
    main()  