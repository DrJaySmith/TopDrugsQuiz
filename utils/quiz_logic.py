import json  

def load_questions(version=100):  
    file_path = f"data/drugs_{version}.json"  
    with open(file_path) as f:  
        return json.load(f)['drugs']  

def validate_answer(question, user_answer):  
    correct_answers = question['brand_names'] + [question['generic_name']]  
    return user_answer.strip().lower() in [a.lower() for a in correct_answers]  