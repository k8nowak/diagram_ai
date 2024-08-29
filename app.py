from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
import subprocess
import time
import re
import logging


load_dotenv()
api_key = os.getenv('API_KEY')
use_model = 'gpt-4o-mini'

client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the UPLOAD_FOLDER directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def compile_latex_to_pdf(latex_file, output_dir):
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"Attempt {attempt} to compile LaTeX to PDF...")
        try:
            subprocess.run(['pdflatex', '-output-directory', output_dir, latex_file], check=True, stdout=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError as e:
            if attempt == max_attempts - 1:
                raise e
            time.sleep(1)  # Wait for 1 second before retrying
    return False

def convert_pdf_to_svg(pdf_file, svg_file):
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"Attempt {attempt} to convert PDF to SVG...")
        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
            try:
                time.sleep(0.5)  # Add a small delay before conversion
                subprocess.run(['pdf2svg', pdf_file, svg_file], check=True, stdout=subprocess.DEVNULL)
                return True
            except subprocess.CalledProcessError as e:
                if attempt == max_attempts - 1:
                    raise e
        time.sleep(1)  # Wait for 1 second before retrying
    return False

def postprocess_latex_code(latex_code):
    # Extract the content between \begin{tikzpicture} and \end{tikzpicture}
    match = re.search(r'(\\begin{tikzpicture}.*?\\end{tikzpicture})', latex_code, re.DOTALL)
    if match:
        tikz_content = match.group(1)
    else:
        tikz_content = latex_code  # fallback in case the pattern is not found
    
    # Define your specific preamble and postamble
    preamble = '\\documentclass{nicegram}\n\\usepackage{tikz}\n\\usepackage{calc}\n\\usepackage{tikz-3dplot}\n\\begin{document}\n'
    postamble = '\n\\end{document}'

    # Wrap the tikz content with the preamble and postamble
    final_latex_code = f"{preamble}{tikz_content}{postamble}"
    
    return final_latex_code


def make_api_call(prompt):
    result = client.chat.completions.create(
        model=use_model,
        messages=[
            {"role": "system", "content": "You are an expert at writing LaTeX code to generate mathematical diagrams using the tikz library. Only reply with the updated code, with no commentary."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        timeout=10
        
    )

    response = result.choices[0].message.content.strip()
    
    # Remove backticks and leading "latex\n" from the response
    response = response.replace("```latex", "").replace("```", "").strip()
    if response.startswith("latex\n"):
        response = response[6:].strip()


    response = postprocess_latex_code(response)
    
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    response = None
    file_path = None
    error_message = None
    current_time=None
    user_input = ''
    width = 300  # Default width
    height = 300  # Default height
    
    if request.method == 'POST':
        action = request.form.get('action')            
            
        if action == 'apply-change':
            # Get the existing LaTeX code and the user's description of the change
            response = request.form['edited_latex']
            change_description = request.form['change_description']
            width = int(request.form.get('width', 300))
            height = int(request.form.get('height', 300))
            
            if not change_description:
                response = request.form['edited_latex']
                width = int(request.form.get('width', 300))
                height = int(request.form.get('height', 300))
            
            else:
                # Create the prompt for GPT
                prompt = f"""Here is some LaTeX code that generates a diagram using the tikz 
                library:\n{response}\n\nMake the following changes: {change_description}.\n\n
                Return the updated LaTeX code."""

                # Make the API call
                response=make_api_call(prompt)
                

        else:
            # User has submitted a new description
            user_input = request.form['user_input']
            prompt = f"""Write me a LaTeX file that uses the tikz library, and create code 
            that would precisely and accurately create the mathematical diagram described 
            below. Ensure the document includes \\documentclass{{nicegram}}, 
            \\usepackage{{tikz}}, \\begin{{document}}, and \\end{{document}}. Assume the
            rendered output will be a 300x300 pixel image, and make sure all the labels 
            and line weights will
            be legible at 100% zoom. Enclose any variables or math notation in $ signs.
            Here is the description of the diagram: {user_input}"""
            # Make the API call
            response=make_api_call(prompt)
            

        # Save the LaTeX code to a .tex file
        latex_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.tex')
        with open(latex_file, 'w') as f:
            f.write(response)


        # Compile the LaTeX file to PDF
        try:
            if not compile_latex_to_pdf(latex_file, app.config['UPLOAD_FOLDER']):
                raise Exception("Failed to compile LaTeX after multiple attempts")
        except Exception as e:
            error_message = f"Error compiling LaTeX: {e} Try resubmitting."
            logging.error(error_message)
            return render_template('index.html', response=response, file_path=file_path, user_input=user_input, width=width, height=height, current_time=current_time, error_message=error_message)

        # Convert the PDF to SVG
        pdf_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.pdf')
        svg_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.svg')
        
        try:
            if not convert_pdf_to_svg(pdf_file, svg_file):
                raise Exception("Failed to convert PDF to SVG after multiple attempts")
        except Exception as e:
            error_message = f"Error converting PDF to SVG: {e} Try resubmitting."
            logging.error(error_message)
            return render_template('index.html', response=response, file_path=file_path, user_input=user_input, width=width, height=height, current_time=current_time, error_message=error_message)    

            
        # Check if the files were created
        if os.path.exists(svg_file):
            file_path = 'output.svg'
            
    # Pass the current time to the template
    current_time = int(time.time())
    print("The current time is "+str(current_time))

    return render_template('index.html', response=response, file_path=file_path, user_input=user_input, width=width, height=height, current_time=current_time, error_message=error_message)



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

