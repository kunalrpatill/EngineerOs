from app import create_app
from app.extensions import db
from app.models.practice import PracticeQuestion
import json

def seed_questions():
    app = create_app()
    with app.app_context():
        # Check if questions already exist
        if PracticeQuestion.query.count() > 0:
            print("Questions already exist. Skipping seed.")
            return

        print("Seeding verified practice questions...")

        questions = [
            # Java - OOP
            PracticeQuestion(
                title="What is inheritance in Java?",
                description="Which of the following best describes inheritance in Java?",
                language="Java",
                topic="OOP",
                subtopic="Inheritance",
                difficulty="Easy",
                question_type="MCQ",
                options=[
                    "The ability of a class to hide its data.",
                    "The mechanism by which one class acquires the properties and behaviors of another class.",
                    "The process of defining multiple methods with the same name.",
                    "A way to prevent a class from being instantiated."
                ],
                correct_answer="The mechanism by which one class acquires the properties and behaviors of another class.",
                explanation="Inheritance allows a new class (subclass) to inherit attributes and methods from an existing class (superclass), promoting code reusability.",
                verified=True
            ),
            PracticeQuestion(
                title="Which keyword is used for inheritance?",
                description="In Java, which keyword is used by a class to inherit from another class?",
                language="Java",
                topic="OOP",
                subtopic="Inheritance",
                difficulty="Easy",
                question_type="MCQ",
                options=[
                    "implements",
                    "inherits",
                    "extends",
                    "super"
                ],
                correct_answer="extends",
                explanation="The 'extends' keyword is used to indicate that a class is inherited from another class.",
                verified=True
            ),
            PracticeQuestion(
                title="Predict the output of this inheritance program",
                description="What is the output of the following Java code?\n```java\nclass A {\n    public A() {\n        System.out.print(\"A\");\n    }\n}\nclass B extends A {\n    public B() {\n        System.out.print(\"B\");\n    }\n}\npublic class Main {\n    public static void main(String[] args) {\n        B obj = new B();\n    }\n}\n```",
                language="Java",
                topic="OOP",
                subtopic="Inheritance",
                difficulty="Medium",
                question_type="Output Prediction",
                correct_answer="AB",
                explanation="When an object of subclass B is created, it first implicitly calls the constructor of its superclass A before executing its own constructor.",
                verified=True
            ),
            PracticeQuestion(
                title="Identify the error in this inheritance code",
                description="Why will the following code fail to compile?\n```java\nfinal class Vehicle {}\nclass Car extends Vehicle {}\n```",
                language="Java",
                topic="OOP",
                subtopic="Inheritance",
                difficulty="Medium",
                question_type="Debugging",
                correct_answer="Cannot inherit from final class",
                explanation="A class marked with the 'final' keyword cannot be subclassed.",
                verified=True
            ),
            
            # C - Pointers
            PracticeQuestion(
                title="Size of pointer in C",
                description="What does the sizeof() operator return for a char* compared to an int* on a typical 64-bit system?",
                language="C",
                topic="Pointers",
                subtopic="Basics",
                difficulty="Medium",
                question_type="MCQ",
                options=[
                    "char* is 1 byte, int* is 4 bytes",
                    "Both are 8 bytes",
                    "char* is 4 bytes, int* is 8 bytes",
                    "Both are 4 bytes"
                ],
                correct_answer="Both are 8 bytes",
                explanation="On a 64-bit architecture, memory addresses are 64 bits (8 bytes) long, regardless of the data type they point to.",
                verified=True
            ),

            # SQL - JOIN
            PracticeQuestion(
                title="Difference between INNER and LEFT JOIN",
                description="Which statement correctly describes a LEFT JOIN?",
                language="SQL",
                topic="JOIN",
                subtopic="Outer Joins",
                difficulty="Easy",
                question_type="MCQ",
                options=json.dumps([
                    "Returns only the rows that have matching values in both tables.",
                    "Returns all rows from the left table, and the matched rows from the right table.",
                    "Returns all rows when there is a match in either left or right table.",
                    "Returns the Cartesian product of the two tables."
                ],
                correct_answer="Returns all rows from the left table, and the matched rows from the right table.",
                explanation="A LEFT JOIN ensures all records from the left (first) table are included, filling in NULLs for the right table columns where no match exists.",
                verified=True
            )
        ]

        db.session.add_all(questions)
        db.session.commit()
        print(f"Successfully seeded {len(questions)} verified questions.")

if __name__ == '__main__':
    seed_questions()
