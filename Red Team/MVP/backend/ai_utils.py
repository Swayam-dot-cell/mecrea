import os
import openai

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_ai_insights(log_text: str):
    """
    Send log text to AI model and get suggestions.
    If no API key is set, return dummy insights.
    """
    if not openai.api_key:
        return [
            "No AI key provided. Returning sample insights.",
            "Consider blocking suspicious IPs detected in logs.",
            "Implement stronger rate limiting against repeated requests.",
            "Review exposed forms for potential flooding attempts."
        ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst."},
                {"role": "user", "content": f"Analyze these logs and provide security insights:\n{log_text}"}
            ],
            max_tokens=300
        )

        ai_text = response.choices[0].message["content"].strip()
        return ai_text.split("\n")

    except Exception as e:
        return [f"Error generating AI insights: {str(e)}"]
