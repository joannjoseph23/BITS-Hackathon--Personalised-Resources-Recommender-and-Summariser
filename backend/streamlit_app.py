import streamlit as st
import openai
import requests
import os
import re
from dotenv import load_dotenv
from googleapiclient.discovery import build
from Tets import get_texts  # Ensure this is correctly imported

# Load API keys from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=api_key,
    base_url="https://aiproxy.sanand.workers.dev/openai/v1"
)

# Function to get PDF text
pdf_text = get_texts()  # Get text data

def generate_questions(text, num_questions=10):
    """
    Generates MCQ questions from the given text.
    """
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

    # Requesting correct answers
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

def parse_questions(questions_text):
    """Parse the questions into a proper list format"""
    # Split the text by question prefix (Q1:, Q2:, etc.)
    questions = re.split(r'Q\d+:', questions_text)
    # Remove the first empty element if it exists
    if questions and not questions[0].strip():
        questions.pop(0)
    # Prefix each question with its number again for display
    parsed_questions = []
    for i in range(len(questions)):
        parsed_questions.append(f"Q{i+1}:{questions[i]}")
    return parsed_questions

def extract_answers_dict(answers_list):
    """Extract answers into a dictionary format"""
    answers_dict = {}
    for answer in answers_list:
        parts = answer.split(":")
        if len(parts) >= 2:
            question_num = parts[0].strip()
            correct_letter = parts[1].strip()
            answers_dict[question_num] = correct_letter
    return answers_dict

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
        st.error(f"Error searching Google: {e}")
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
        st.error(f"Error searching YouTube: {e}")
        return []

# Function to generate learning resources for incorrect answers
def generate_learning_resources(incorrect_questions):
    summary = "📘 **Learning Resources for Incorrect Answers** 📘\n\n"
    
    for item in incorrect_questions:
        question_num = item["question"]
        question_text = item["question_text"]
        correct_answer = item["correct_answer"]

        summary += f"❌ **Question:** {question_text}\n"
        summary += f"✅ **Correct Answer:** {correct_answer}\n\n"

        # Extract the main question text without the options
        main_question = question_text.split("A)")[0].strip()
        
        # Progress indicator
        with st.spinner(f"Finding resources for {question_num}..."):
            # Search for research papers with a more focused query
            research_results = search_google(f"{main_question} site:researchgate.net OR site:arxiv.org")
            if research_results:
                summary += "📄 **Research Papers:**\n"
                for result in research_results:
                    summary += f"- [{result['title']}]({result['link']})\n"
                summary += "\n"
            else:
                summary += "📄 **Research Papers:** No relevant papers found.\n\n"

            # Search for YouTube videos - ensure we get results
            youtube_results = search_youtube(main_question)
            if youtube_results:
                summary += "📺 **YouTube Videos:**\n"
                for video in youtube_results:
                    summary += f"- [{video['title']}]({video['url']})\n"
                summary += "\n"
            else:
                # Try a more general search if specific search fails
                fallback_query = " ".join(main_question.split()[:10]) + " tutorial"
                youtube_results = search_youtube(fallback_query)
                if youtube_results:
                    summary += "📺 **YouTube Videos:**\n"
                    for video in youtube_results:
                        summary += f"- [{video['title']}]({video['url']})\n"
                    summary += "\n"
                else:
                    summary += "📺 **YouTube Videos:** No relevant videos found.\n\n"

    # Save summary to a text file
    try:
        with open("learning_summary.txt", "w", encoding="utf-8") as file:
            file.write(summary)
        st.success("📑 Learning summary saved as learning_summary.txt")
    except Exception as e:
        st.error(f"Error saving learning summary: {e}")
    
    return summary

# Initialize session state if not already done
if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "score" not in st.session_state:
    st.session_state.score = 0
if "resources_generated" not in st.session_state:
    st.session_state.resources_generated = False
if "learning_summary" not in st.session_state:
    st.session_state.learning_summary = ""

# Streamlit UI
st.title("📚 AI-Powered MCQ Quiz")

# Generate button
if st.button("Generate Quiz") or st.session_state.quiz_generated:
    # Only generate new questions if not already generated
    if not st.session_state.quiz_generated:
        with st.spinner("Generating quiz questions..."):
            raw_questions, raw_answers = generate_questions(pdf_text, num_questions=5)
            st.session_state.questions = parse_questions(raw_questions)
            st.session_state.correct_answers = extract_answers_dict(raw_answers)
            st.session_state.quiz_generated = True
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.score = 0
            st.session_state.resources_generated = False
            st.session_state.learning_summary = ""
    
    # Display each question and answer options
    for i, question in enumerate(st.session_state.questions):
        q_num = f"Q{i+1}"
        st.subheader(f"Question {i+1}")
        st.write(question)
        
        # Create radio buttons for each question
        selected_option = st.radio(
            f"Select your answer for Question {i+1}:",
            options=["A", "B", "C", "D"],
            key=f"q{i}",
            index=None
        )
        
        # Store the selected answer
        if selected_option:
            st.session_state.user_answers[q_num] = selected_option
        
        st.markdown("---")
    
    # Submit answers button
    if st.button("Submit Answers"):
        st.session_state.submitted = True
        
        # Calculate score
        score = 0
        results = []
        incorrect_questions = []
        
        for q_num, correct_answer in st.session_state.correct_answers.items():
            q_index = int(q_num[1:]) - 1
            question_text = st.session_state.questions[q_index] if q_index < len(st.session_state.questions) else "Question not found"
            user_answer = st.session_state.user_answers.get(q_num, "")
            is_correct = user_answer == correct_answer
            
            if is_correct:
                score += 1
            else:
                incorrect_questions.append({
                    "question": q_num,
                    "question_text": question_text,
                    "correct_answer": correct_answer
                })
                
            results.append({
                "question": q_num,
                "question_text": question_text,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })
        
        st.session_state.score = score
        st.session_state.results = results
        st.session_state.incorrect_questions = incorrect_questions
    
    # Display results if submitted
    if st.session_state.submitted:
        st.header("Quiz Results")
        st.markdown(f"### 🎯 Your Score: {st.session_state.score}/5")
        
        for result in st.session_state.results:
            if result["is_correct"]:
                st.success(f"✅ {result['question']}: Correct!")
            else:
                st.error(f"❌ {result['question']}: Incorrect. The correct answer is {result['correct_answer']}.")
            
            st.write(result["question_text"])
            st.markdown("---")
        
        # Generate learning resources for incorrect answers
        if st.session_state.incorrect_questions and not st.session_state.resources_generated:
            if st.button("Generate Learning Resources"):
                with st.spinner("Generating learning resources..."):
                    learning_summary = generate_learning_resources(st.session_state.incorrect_questions)
                    st.session_state.learning_summary = learning_summary
                    st.session_state.resources_generated = True
        
        # Display learning resources if generated
        if st.session_state.resources_generated:
            st.header("Learning Resources")
            st.markdown(st.session_state.learning_summary)
            
            # Option to download the learning summary
            st.download_button(
                label="Download Learning Summary",
                data=st.session_state.learning_summary,
                file_name="learning_summary.txt",
                mime="text/plain"
            )
        
        if st.button("Take Another Quiz"):
            st.session_state.quiz_generated = False
            st.session_state.submitted = False
            st.session_state.user_answers = {}
            st.session_state.score = 0
            st.session_state.resources_generated = False
            st.session_state.learning_summary = ""
            st.rerun()
            
else:
    st.write("Click 'Generate Quiz' to start a new quiz!")
    
# Show debugging info (can be removed in production)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.write("Session State Variables:")
    st.sidebar.write(f"Quiz Generated: {st.session_state.quiz_generated}")
    st.sidebar.write(f"Submitted: {st.session_state.submitted}")
    st.sidebar.write(f"Resources Generated: {st.session_state.resources_generated}")
    if "questions" in st.session_state:
        st.sidebar.write(f"Number of Questions: {len(st.session_state.questions)}")
    st.sidebar.write("User Answers:")
    st.sidebar.write(st.session_state.user_answers)
    if "correct_answers" in st.session_state:
        st.sidebar.write("Correct Answers:")
        st.sidebar.write(st.session_state.correct_answers)
