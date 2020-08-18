import os
import string
import random
from flask import Flask, render_template, request, redirect, url_for, send_file, after_this_request, jsonify
from worker import celery
from celery.result import AsyncResult
import celery.states as states

# Convert configuration
UPLOAD_FOLDER = '../appdata/'
RESULT_FOLDER = '../appdata/'
ALLOWED_EXTENSIONS = {'mov', 'mp4', 'mkv', 'avi', 'flv', 'wmv'}

env=os.environ
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload(file, generateFilename):
    # Save file to appdata
    file_extension = os.path.splitext(file.filename)[1]
    filename = generateFilename + file_extension
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

@app.before_first_request
def cleanUp():
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            os.remove(UPLOAD_FOLDER + filename)

        for filename in os.listdir(RESULT_FOLDER):
            os.remove(RESULT_FOLDER + filename)

        print("Temporary files have been cleaned.")
    except Exception as e:
        print(str(e))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Check if the POST request has the file
        if 'file' not in request.files:
            return jsonify({'status' : 'No File.'}), 400

        file = request.files['file']
        presetOption = request.form['preset']
        resolutionOption = request.form['resolution']
        frameRateOption = request.form['framerate']
        outputFormat = request.form['format']

        # If filename is empty
        if file.filename == '':
            return jsonify({'status' : 'Filename is empty.'}), 400

        if file and allowed_file(file.filename):
            try:
                # Genarate filename (avoid overwrite file)
                generateFilename = get_random_string(10)
                inputFormat = os.path.splitext(file.filename)[1]

                # Upload file
                upload(file, generateFilename)

                # Asynchronous task
                task = celery.send_task('convert.add', args=[generateFilename, inputFormat, presetOption, resolutionOption, frameRateOption, outputFormat], kwargs={})

                return jsonify({'status' : 'File Accepted'}), 202, {'Location': url_for('taskstatus', task_id=task.id)}
            except Exception as e:
                return jsonify({'status' : 'Conversion Failed! ' + str(e)}), 400

    elif request.method == 'GET':
        return render_template('index.html'), 200

# Download file
@app.route('/download/<file>', methods=['GET'])
def download_file(file):
    try:
        # Remove converted file after downloaded
        @after_this_request
        def remove_file(response):
            try:
                os.remove(RESULT_FOLDER + file)
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

        path = RESULT_FOLDER + file
        return send_file(path, as_attachment=True), 200
    except Exception as e:
        return jsonify({'status' : 'Download Failed! ' + str(e)}), 404

# Get Task Status
@app.route('/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = celery.AsyncResult(task_id)
    if task.info:
        file = str(task.info)
    else:
        file = ""

    return jsonify({'state': task.state, 'info': task.info, 'result_url': url_for('download_file', file=file)}), 200


if __name__ == '__main__':
    app.run()
