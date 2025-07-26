import random
import time
import sys

def read_file(filename):
    # Lists to hold each column
    generic_names_list = []
    brand_names1 = []
    brand_names2 = []
    brand_names3 = []
    brand_names4 = []
    brand_names_list = []
    drug_classes_list = []
    indications = []
    indications_list = []
    week_indexes = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip() in ['1','2','3','4','5','6','7','8','9','10']:
                    week_index = int(line.strip())
                    continue
                week_indexes.append(week_index)

                columns = line.split(';')
                # Append each column to its respective list
                generic_names_list.append(columns[0])
                brand_names_list.append(columns[1])
                brand_names_list.append(columns[2])
                brand_names_list.append(columns[3])
                brand_names_list.append(columns[4])
                brand_names1.append(columns[1])
                brand_names2.append(columns[2])
                brand_names3.append(columns[3])
                brand_names4.append(columns[4])
                drug_classes_list.append(columns[5])
                indications.append(columns[6].strip().split(','))
                indications_list.append(''.join(columns[6].strip().split(',')))  # Remove trailing newline
        cleaned_brand_names = [name for name in brand_names_list if name.strip() != ""]
        return {
            "Week Indexes": week_indexes,
            "Generic Names": generic_names_list,
            "Brand Names List": brand_names_list,
            "Cleaned Brand Names List": cleaned_brand_names,
            "Brand Names 1": brand_names1,
            "Brand Names 2": brand_names2,
            "Brand Names 3": brand_names3,
            "Brand Names 4": brand_names4,
            "Drug Classes": drug_classes_list,
            "Indications": indications,
            "Indications List": indications_list
        }

    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None


def get_random_options(correct_answer, options_list):
    """Get 4 random incorrect options from the list."""
    incorrect_options = random.sample([option for option in options_list if option != correct_answer], 4)
    if type(incorrect_options[0]) == type([]):
        for each in range(len(incorrect_options)):
            while True:
                option = random.choice(incorrect_options[each])
                if correct_answer != option:
                    incorrect_options[each] = option
                    break
    incorrect_options = list(set(incorrect_options))
    all_options = [correct_answer] + incorrect_options
    random.shuffle(all_options)
    return all_options

def quiz_chatbot():
    print("Welcome to the Medication Quiz!")
    while True:
        chart = input("Would you like to study top 100 drugs, top 200 drugs, or both? (type: 100, 200, or both)")
        if chart == '100':
            filename = 'top_100_Drugs_formatted.txt'  # Replace with your file name
            break
        elif chart == '200':
            filename = 'top_200_Drugs_formatted.txt'  # Replace with your file name
            break
        elif chart == 'both':
            filename = 'top_Drugs_formatted_all200.txt'
            break
        else:
            print("User input error. Try again. Type 100, 200, or both")

    while True:
        if chart == 'both':
            week_number = 0
            break # don't ask question if they want to study all top 200
        week = input("Would you like to study a specific week? (type: y/n)")
        if week == 'n':
            week_number = 0
            break
        elif week == 'y':
            week_number = int(input("Which week would you like to study? (type: 1-10)"))
            if week_number in [1,2,3,4,5,6,7,8,9,10]:
                break
            else:
                print("User input error. Try again. ")
        else:
            print("User input error. Try again. Type 100, 200, or both")

    question_types = ["generic_to_brand", "brand_to_generic", "generic_to_class",
                      "brand_to_class", "generic_to_indication", "brand_to_indication"]
    selected_types = question_types.copy()

    while True:
        type_pref = input("\nWould you like to focus on specific question types? (y/n): ").lower()
        if type_pref == 'y':
            print("\nAvailable question types:")
            print("1. Generic to Brand\n2. Brand to Generic\n3. Generic to Class")
            print("4. Brand to Class\n5. Generic to Indication\n6. Brand to Indication")
            choice = input("Enter numbers separated by commas (e.g., 1,3,5) or 'all': ").strip()

            if choice.lower() == 'all':
                break

            try:
                selected_numbers = [int(num.strip()) for num in choice.split(',')]
                valid_numbers = [n for n in selected_numbers if 1 <= n <= 6]
                selected_types = [question_types[n - 1] for n in valid_numbers]

                if len(selected_types) > 0:
                    type_names = "\n".join([f"- {t.replace('_', ' ').title()}"
                                            for t in selected_types])
                    print(f"\nSelected question types:\n{type_names}")
                    break

            except ValueError:
                print("Invalid input. Using all question types.")

        elif type_pref == 'n':
            break
        else:
            print("Please enter 'y' or 'n'")

    data = read_file(filename)
    report_info = {
        "questions": 0,
        "correct": 0,
        "time": time.time()
    }
    try:
        while True:
            # Randomly select a question type
            question_type = random.choice(selected_types)

            if question_type == "generic_to_brand":
                while True:
                    generic_name = random.choice(data["Generic Names"])
                    current_drug_index = data["Generic Names"].index(generic_name)
                    correct_answer = data["Brand Names List"][current_drug_index*4+random.randint(0,3)]
                    # print("week number", week_number)
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Cleaned Brand Names List"])
                print(f"What is the brand name of {generic_name}?")
            elif question_type == "brand_to_generic":
                while True:
                    brand_name = random.choice(data["Cleaned Brand Names List"])
                    current_drug_index = data["Brand Names List"].index(brand_name)//4
                    correct_answer = data["Generic Names"][current_drug_index]
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Generic Names"])
                print(f"What is the generic name of {brand_name}?")
            elif question_type == "generic_to_class":
                while True:
                    generic_name = random.choice(data["Generic Names"])
                    current_drug_index = data["Generic Names"].index(generic_name)
                    correct_answer = data["Drug Classes"][current_drug_index]
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Drug Classes"])
                print(f"What is the class of {generic_name}?")
            elif question_type == "brand_to_class":
                while True:
                    brand_name = random.choice(data["Cleaned Brand Names List"])
                    current_drug_index = data["Brand Names List"].index(brand_name)//4
                    correct_answer = data["Drug Classes"][current_drug_index]
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Drug Classes"])
                print(f"What is the class of {brand_name}?")
            elif question_type == "generic_to_indication":
                while True:
                    generic_name = random.choice(data["Generic Names"])
                    current_drug_index = data["Generic Names"].index(generic_name)
                    correct_answer = random.choice(data["Indications"][current_drug_index])
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Indications"])
                print(f"What does {generic_name} treat?")
            elif question_type == "brand_to_indication":
                while True:
                    brand_name = random.choice(data["Cleaned Brand Names List"])
                    current_drug_index = data["Brand Names List"].index(brand_name)//4
                    correct_answer = random.choice(data["Indications"][current_drug_index])
                    if week_number != 0:
                        if data["Week Indexes"][current_drug_index] == week_number:
                            if correct_answer.strip() != '':
                                break
                    else:
                        if correct_answer.strip() != '':
                            break
                options = get_random_options(correct_answer, data["Indications"])
                print(f"What does {brand_name} treat?")

            # Display options
            for i, option in enumerate(options):
                print(f"{chr(97 + i)}) {option}")

            # Get user's answer
            user_answer = input("Enter your answer (a/b/c/d/e): ")

            # Check if the answer is correct
            correct_index = options.index(correct_answer)
            if chr(97 + correct_index) == user_answer:
                print("\nCorrect!\n")
            else:
                print(f"Incorrect. The correct answer is {chr(97 + correct_index)}) {correct_answer}\n")

            # Display Drug information
            print("--- Drug Information ---")
            print(f"Generic Name: {data['Generic Names'][current_drug_index]}")

            # Get brand names and filter empty values
            brands = [
                data['Brand Names 1'][current_drug_index],
                data['Brand Names 2'][current_drug_index],
                data['Brand Names 3'][current_drug_index],
                data['Brand Names 4'][current_drug_index]
            ]
            clean_brands = [b.strip() for b in brands if b.strip()]
            print(f"Brand Names: {', '.join(clean_brands)}")
            print(f"Drug Class: {data['Drug Classes'][current_drug_index]}")
            print(f"Indications: {', '.join(data['Indications'][current_drug_index])}\n")

            # Update counters
            report_info["questions"] += 1
            if chr(97 + correct_index) == user_answer:
                report_info["correct"] += 1
    except KeyboardInterrupt:
        elapsed = time.time() - report_info["time"]
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        print("\n\n--- Quiz Performance Report ---")
        print(f"Total questions answered: {report_info['questions']}")
        print(f"Correct answers: {report_info['correct']}")
        print(f"Time spent: {minutes}m {seconds:.2f}s")  # Updated formatting
        if report_info['questions'] > 0:
            accuracy = (report_info['correct'] / report_info['questions']) * 100
            print(f"Accuracy: {accuracy:.1f}%")

        sys.exit(0)


quiz_chatbot()

