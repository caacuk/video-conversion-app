from flask import Flask, render_template, request, redirect, url_for, send_file, after_this_request, jsonify
import os
import random
import string
from celery import Celery

# Convert configuration
UPLOAD_FOLDER = './video_input/'
RESULT_FOLDER = './video_output/'
ALLOWED_EXTENSIONS = {'mov', 'mp4', 'mkv', 'avi', 'flv', 'wmv'}

# Flask configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload(file, generateFilename):
    # SAVE FILE TO video_input WITH FILENAME is input.<extension>
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

@celery.task(bind=True)
def convert(self, inputFilename, inputFormat, presetOption, resolutionOption, frameRateOption, outputFormat):

    outputFilename = 'converted-' +inputFilename + '-' + presetOption + '-' + resolutionOption + '-' + frameRateOption
    
    videoCodec = 'libx264'
    
    converted = os.system('ffmpeg -y -i ' + UPLOAD_FOLDER + inputFilename + inputFormat + ' -c:v ' + videoCodec + ' -preset ' + presetOption + ' -r ' + frameRateOption + ' -c:a copy -s ' + resolutionOption + ' ' + RESULT_FOLDER + outputFilename + outputFormat)
    
    # Remove input file immediately after conversion
    try:
        os.remove(UPLOAD_FOLDER + inputFilename + inputFormat)
    except Exception as error:
        app.logger.error("Error removing or closing downloaded file handle", error)

    # 0 ia success, 1 is failed
    if converted == 0:
        return outputFilename + outputFormat
    else:
        return False

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Check if the POST request has the file
        if 'file' not in request.files:
            return 'No File.', 400

        file = request.files['file']
        presetOption = request.form['preset']
        resolutionOption = request.form['resolution']
        frameRateOption = request.form['framerate']
        outputFormat = request.form['format']

        # If filename is empty
        if file.filename == '':
            return 'Filename is empty.', 400

        if file and allowed_file(file.filename):
            try:
                # Genarate filename (avoid overwrite file)
                generateFilename = get_random_string(10)
                inputFormat = os.path.splitext(file.filename)[1]

                # Upload file
                upload(file, generateFilename)

                # Asynchronous task
                task = convert.delay(generateFilename, inputFormat, presetOption, resolutionOption, frameRateOption, outputFormat)

                return jsonify({'status' : 'File accepted'}), 202, {'Location': url_for('taskstatus', task_id=task.id)}
            except Exception as e:
                return 'Conversion Failed! ' + str(e), 400

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
        return str(e), 404

# Get Task Status
@app.route('/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = convert.AsyncResult(task_id)
    if task.info:
        file = str(task.info)
    else:
        file = ""

    return jsonify({'state': task.state, 'info': task.info, 'result_url': url_for('download_file', file=file)}), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


# celery -A app.celery worker --loglevel=info