from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from io import BytesIO
import json
import logging

app = Flask(__name__)

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load processes and tasks
abilities_df = pd.read_csv('abilities.csv')

# Separate processes and tasks based on the 'parent' column
processes = abilities_df[abilities_df['parent'].isnull()][['id', 'name']].to_dict(orient='records')
tasks = abilities_df[abilities_df['parent'].notnull()][['id', 'name', 'parent']].to_dict(orient='records')

@app.route('/')
def index():
    # Sort processes and tasks by name
    sorted_processes = sorted(processes, key=lambda x: x['name'])
    sorted_tasks = sorted(tasks, key=lambda x: x['name'])
    return render_template('index.html', processes=sorted_processes, tasks=sorted_tasks)

@app.route('/generate_csv', methods=['POST'])
def generate_csv():
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        if not data or 'questions' not in data:
            app.logger.error("Invalid data received")
            return jsonify({"error": "Invalid data"}), 400

        # CSV header
        csv_content = 'statement,ability,subability,explanation,options,associatedText\n'
        for idx, question in enumerate(data['questions'], start=1):
            app.logger.debug(f"Processing question: {question}")

            correct_option = question.get('correct_option', '').strip()
            app.logger.debug(f"Correct option for question {idx}: {correct_option}")

            if not correct_option.isdigit():
                app.logger.error(f"Question {idx} is missing a valid correct option.")
                return jsonify({"error": f"La pregunta {idx} no tiene una respuesta correcta seleccionada."}), 400

            ability_id = question['ability']
            subability_id = question['subability']
            explanation = question['explanation']
            associated_text = question['associated_text']
            options = [
                {"isCorrect": i + 1 == int(correct_option), "text": option}
                for i, option in enumerate(question['options'])
            ]
            csv_content += f'"{question["statement"]}","{ability_id}","{subability_id}","{explanation}","{json.dumps(options, ensure_ascii=False)}","{associated_text}"\n'

        csv_data = BytesIO(csv_content.encode('utf-8'))
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name='questions.csv'
        )
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
