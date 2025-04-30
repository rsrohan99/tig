from typing import Dict
import inquirer
from textwrap import dedent
import re


def format_response(question: str, answer: str) -> str:
    return dedent(f"""
    [ask_followup_question for '{question}'] Result:
    <answer>
    {answer}
    </answer>
    """)


def ask_followup_questions(arguments: Dict) -> str:
    """
    Asks the user for follow-up questions to gather more information.

    Args:
        arguments: A dictionary containing the arguments for the follow-up questions.
        inside arguments:
        'question': the question to ask the user
        'follow_up': dictionary containing suggested answers in the 'suggest' key
            - 'suggest' could be just a string of a list of strings

    Returns:
        A string containing the answer to the question, either selecting one of the follow-up suggestions or manually entering the answer
    """

    if "question" not in arguments:
        return "Error: No question provided. Try asking again."

    if "follow_up" in arguments:
        suggestions = re.findall(
            r"<suggest>(.*?)</suggest>", arguments["follow_up"], re.DOTALL
        )
        manual_answer_prompt = "Let me enter my own answer"
        suggestions.append(manual_answer_prompt)
        print(f"\nTig wants to know: {arguments['question']}")
        questions = [
            inquirer.List(
                "answer",
                message="Please select an answer or enter your own:",
                choices=suggestions,
            )
        ]
        answers = inquirer.prompt(questions)
        if answers:
            answer = answers["answer"]
            if answer == manual_answer_prompt:
                answer = input(f"\n{arguments['question']}: ")
            return format_response(arguments["question"], answer)
        else:
            return format_response(
                arguments["question"],
                "Error: User didn't provide any answer. Try asking again.",
            )
    else:
        answer = input(f"\n{arguments['question']}: ")
        if answer:
            return format_response(arguments["question"], answer)
        else:
            return format_response(
                arguments["question"],
                "Error: User didn't provide any answer. Try asking again.",
            )
