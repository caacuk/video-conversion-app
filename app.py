from flask import Flask, render_template, flash, request, redirect, url_for, send_file, after_this_request
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = './video_input/'
RESULT_FOLDER = './video_output/'
ALLOWED_EXTENSIONS = {'mov', 'mp4', 'mkv', 'avi', 'flv', 'mpg', 'ogv', 'webm', 'wmv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret'

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # CHECK IF THE POST REQUEST HAS THE FILE PART
        if 'file' not in request.files:
            flash('No file part')
            return 'No File.', 400

        file = request.files['file']
        presetOption = request.form['preset']
        resolutionOption = request.form['resolution']
        frameRateOption = request.form['framerate']
        outputFormat = request.form['format']

        #  IF FILENAME IS EMPTY
        if file.filename == '':
            flash('No selected file')
            return 'Filename is empty.', 400

        if file and allowed_file(file.filename):
            try:
                # must async (1)
                upload(file)

                # must async (2)
                resultFilename = convert(file, presetOption, resolutionOption, frameRateOption, outputFormat)

                if resultFilename == False:
                    return 'Conversion Failed!', 400

                file_extension = os.path.splitext(file.filename)[1]

                @after_this_request
                def remove_file(response):
                    try:
                        os.remove(UPLOAD_FOLDER + 'input' + file_extension)
                        os.remove(RESULT_FOLDER + resultFilename)
                    except Exception as error:
                        app.logger.error("Error removing or closing downloaded file handle", error)
                    return response

                path = RESULT_FOLDER + resultFilename
                return send_file(path, as_attachment=True), 200
            except Exception as e:
                return 'Conversion Failed! ' + e, 400

    elif request.method == 'GET':
        return render_template('index.html'), 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload(file):
    # MAKE video_input EMPTY
    # for f in os.listdir(UPLOAD_FOLDER):
    #     os.remove(UPLOAD_FOLDER + f)

    # SAVE FILE TO video_input WITH FILENAME is input.<extension>
    file_extension = os.path.splitext(file.filename)[1]
    filename = 'input' + file_extension
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

def convert(file, presetOption, resolutionOption, frameRateOption, outputFormat):
    # for f in os.listdir(RESULT_FOLDER):
    #     os.remove(RESULT_FOLDER + f)

    # INPUT
    inputDir = UPLOAD_FOLDER
    inputFilename = 'input'
    inputFormat = os.path.splitext(file.filename)[1]

    # Output
    outputDir = RESULT_FOLDER
    outputFilename = 'converted-' + presetOption + '-' + resolutionOption + '-' + frameRateOption
    # outputFilename = 'output'
    
    converted = os.system('ffmpeg -y -i ' + inputDir + inputFilename + inputFormat + ' -c:v libx264 -preset ' + presetOption + ' -r ' + frameRateOption + ' -c:a copy -s ' + resolutionOption + ' ' + outputDir + outputFilename + outputFormat)
    
    if converted == 0:
        return outputFilename + outputFormat
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)