import os
import openai
from dotenv import dotenv_values
config = dotenv_values(".env")
openai.api_key = config['OPENAI_API_KEY']

from flask import Flask, request, render_template, session, redirect

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

max_attempts = 6

def generate_feedback(word, guess):
    """Generates feedback for a guess with HTML class styling."""
    if len(guess) != len(word):
        return "Guesses must be 5 letters."
    
    feedback = []
    for gw, ww in zip(guess, word):
        if gw == ww:
            feedback.append('correct')
        elif gw in word:
            feedback.append('present')
        else:
            feedback.append('absent')
    return feedback

def is_valid_guess(guess):
    """Check if the guess is exactly 5 letters."""
    return len(guess) == 5

def get_five_letter_word():

    prompt = f"""You are a dictionary API. Please provide a five-letter random word.
    
    Q: "give me a five letter random word: "
    A: tiger
    
    Q: "give me a five letter random word: "
    A: house
    
    Q: "give me a five letter random word: "
    A: steak

    Q: "give me a five letter random word: "
    A: 
     
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        # Assuming the response structure aligns with chat completions, extract the word.
        word = response.choices[0].message['content'].strip().lower()
        # Print the word for debugging
        print("Generated word:", word)
        # Ensure the word is exactly 5 letters. If not, you can handle accordingly.
        if len(word) == 5 and word.isalpha():
            return word
        else:
            # Handling case where the word does not meet criteria
            return "retry"  # Placeholder, consider a retry mechanism or default word
    except Exception as e:
        print(f"Error fetching word from OpenAI: {e}")
        # Return a default word or handle the exception as needed
        return "apple"  # Placeholder for error handling

def is_real_word(guess):
    prompt = f"Is '{guess}' a real English word?"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a highly knowledgeable assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16,  # Adjusted to ensure enough room for a response
            temperature=0.5  # A bit of variability but aiming for consistency
        )
        answer = response.choices[0].message['content'].strip().lower()
        # Interpret the model's response
        return "yes" in answer
    except Exception as e:
        print(f"Error checking word validity: {e}")
        return False  # Assume invalid if there's an error, or handle differently


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main game route for displaying the game and processing guesses."""
    if 'new_game' in request.form or 'word_to_guess' not in session:
        session['word_to_guess'] = get_five_letter_word()
        session['attempts'] = 0
        session['game_over'] = False
        session['guesses'] = []

    game_over_message = ''
    error_message = ''

    if request.method == 'POST' and not session['game_over']:
        guess = request.form.get('guess', '').lower()

        if is_valid_guess(guess):
            if is_real_word(guess):
                if session['attempts'] < max_attempts:
                    session['attempts'] += 1
                    feedback = generate_feedback(session['word_to_guess'], guess)

                    # Store the guess and feedback as a list of dictionaries
                    guess_feedback = [{'letter': letter, 'class': cls} for letter, cls in zip(guess, feedback)]
                    session['guesses'].append(guess_feedback)

                    if guess == session['word_to_guess']:
                        session['game_over'] = True
                        game_over_message = 'Congratulations, you won!'
                    elif session['attempts'] == max_attempts:
                        session['game_over'] = True
                        game_over_message = 'Game over! The word was: {}'.format(session['word_to_guess'])
            else:
                error_message = "Invalid guess. Please enter a valid 5-letter word."
        else:
            error_message = "Invalid guess. Please enter a valid 5-letter word."

    guesses_left = max_attempts - session['attempts']
    empty_guesses = max_attempts - len(session['guesses'])

    # Pass the guesses to the template as they are
    return render_template(
        "index.html",
        guesses=session['guesses'],
        guesses_left=guesses_left,
        empty_guesses=empty_guesses,
        game_over_message=game_over_message,
        error_message=error_message
    )

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    """Route to reset the game state and start a new game."""
    session.clear()
    return redirect('/')

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)


