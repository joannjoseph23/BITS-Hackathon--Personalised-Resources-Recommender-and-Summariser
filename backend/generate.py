from googleapiclient.discovery import build
import openai
import requests
import os
from dotenv import load_dotenv
from Tets import get_texts

# Load API keys from .env file
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = openai.OpenAI(
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDA4MTNAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.nPKeq-eyBGukb9oFj-0NIc1iZLlMv1NQfG3boAB2SL4",  # Replace with your key
    base_url="https://aiproxy.sanand.workers.dev/openai/v1"
)


pdf_text = get_texts()  # Get text data

# Function to generate quiz questions
def generate_questions(text, num_questions=5):
    prompt = f"""
    Generate exactly {num_questions} MCQ quiz questions from the following text. 
    Each question must have four options (A, B, C, D), clearly labeled.
    Format each question with a "Q1:" prefix and number them sequentially.
    Format:
    Q1: [Question here]
    A) [Option 1]
    B) [Option 2]
    C) [Option 3]
    D) [Option 4]

    Do not include the correct answer in this part.

    Text: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    questions = response.choices[0].message.content.strip()

    # Get correct answers
    prompt1 = f"""
    Provide the correct answers for the following {num_questions} questions.
    Return answers in the format:
    Q1: A
    Q2: C
    Q3: D
    Q4: B
    Q5: A
    (Only return the correct letter without explanations)
    
    Questions:
    {questions}
    """

    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt1}]
    )

    correct_answers = response1.choices[0].message.content.strip().split("\n")

    return questions, correct_answers

# Function to search for research papers
def search_google(query, max_results=5):
    url = "https://serpapi.com/search"
    params = {"q": query, "api_key": SERPAPI_KEY, "num": max_results}

    try:
        response = requests.get(url, params=params)
        data = response.json()

        search_results = []
        for result in data.get("organic_results", []):
            search_results.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet")
            })

        return search_results
    except Exception as e:
        print(f"Error searching Google: {e}")
        return []

# Function to search YouTube videos
def search_youtube(query, max_results=3):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(q=query, part="snippet", type="video", maxResults=max_results)
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "description": item["snippet"]["description"]
            })

        return videos
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []

# Function to parse questions into a list
def parse_questions(questions_text):
    # Split the text by question prefix (Q1:, Q2:, etc.)
    import re
    questions = re.split(r'Q\d+:', questions_text)
    # Remove the first empty element if it exists
    if questions and not questions[0].strip():
        questions.pop(0)
    # Prefix each question with its number again for display
    for i in range(len(questions)):
        questions[i] = f"Q{i+1}:{questions[i]}"
    return questions

# Function to generate quiz and resources
def quiz_user():
    questions, correct_answers = generate_questions(pdf_text, num_questions=5)
    
    # Parse the questions to ensure all 5 are properly separated
    mcq_list = parse_questions(questions)
    
    # Ensure we have exactly the expected number of questions
    print(f"Total questions generated: {len(mcq_list)}")
    
    score = 0
    total = min(len(mcq_list), 5)  # Ensure we handle exactly 5 questions
    incorrect_questions = []

    for i in range(total):
        print(f"\n🔹 **Question {i+1}:**")
        print(mcq_list[i])  # Display the question with choices

        user_answer = input("\nEnter your answer (A, B, C, or D): ").strip().upper()

        while user_answer not in ["A", "B", "C", "D"]:
            print("❌ Invalid choice! Please enter A, B, C, or D.")
            user_answer = input("\nEnter your answer (A, B, C, or D): ").strip().upper()

        # Extract the correct answer letter only
        correct_answer = correct_answers[i].split(":")[-1].strip()

        if user_answer == correct_answer:
            print("✅ Correct!\n")
            score += 1
        else:
            print(f"❌ Incorrect. The correct answer was {correct_answer}.\n")
            incorrect_questions.append({"question": mcq_list[i], "correct_answer": correct_answer})

    print(f"\n🎯 Your final score: {score}/{total}")

    if incorrect_questions:
        generate_learning_summary(incorrect_questions)

# Function to generate learning summary
def generate_learning_summary(incorrect_questions):
    summary = "📘 **Learning Resources for Incorrect Answers** 📘\n\n"

    for item in incorrect_questions:
        question = item["question"]
        correct_answer = item["correct_answer"]

        summary += f"❌ **Question:** {question}\n"
        summary += f"✅ **Correct Answer:** {correct_answer}\n\n"

        # Extract the main question text without the options
        question_text = question.split("A)")[0].strip()
        
        # Search for research papers with a more focused query
        research_results = search_google(f"{question_text} site:researchgate.net OR site:arxiv.org")
        if research_results:
            summary += "📄 **Research Papers:**\n"
            for result in research_results:
                summary += f"- [{result['title']}]({result['link']})\n"
            summary += "\n"
        else:
            summary += "📄 **Research Papers:** No relevant papers found.\n\n"

        # Search for YouTube videos - ensure we get results
        youtube_results = search_youtube(question_text)
        if youtube_results:
            summary += "📺 **YouTube Videos:**\n"
            for video in youtube_results:
                summary += f"- [{video['title']}]({video['url']})\n"
            summary += "\n"
        else:
            # Try a more general search if specific search fails
            fallback_query = " ".join(question_text.split()[:10]) + " tutorial"
            youtube_results = search_youtube(fallback_query)
            if youtube_results:
                summary += "📺 **YouTube Videos:**\n"
                for video in youtube_results:
                    summary += f"- [{video['title']}]({video['url']})\n"
                summary += "\n"
            else:
                summary += "📺 **YouTube Videos:** No relevant videos found.\n\n"

    # Save summary to a text file
    with open("learning_summary.txt", "w", encoding="utf-8") as file:
        file.write(summary)

    print("\n📑 **Learning summary saved as learning_summary.txt**")

# Run the quiz
quiz_user()