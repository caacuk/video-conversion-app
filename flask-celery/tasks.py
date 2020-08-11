import os
import time
from celery import Celery

env=os.environ
CELERY_BROKER_URL=env.get('CELERY_BROKER_URL','redis://localhost:6379'),
CELERY_RESULT_BACKEND=env.get('CELERY_RESULT_BACKEND','redis://localhost:6379')

# Convert configuration
UPLOAD_FOLDER = '../appdata/'
RESULT_FOLDER = '../appdata/'

celery= Celery('tasks',
                broker=CELERY_BROKER_URL,
                backend=CELERY_RESULT_BACKEND)


@celery.task(name='convert.add',bind=True)
def convert(self, inputFilename, inputFormat, presetOption, resolutionOption, frameRateOption, outputFormat):

    outputFilename = 'converted-' +inputFilename + '-' + presetOption + '-' + resolutionOption + '-' + frameRateOption
    
    videoCodec = 'libx264'
    
    converted = os.system('ffmpeg -y -i ' + UPLOAD_FOLDER + inputFilename + inputFormat + ' -c:v ' + videoCodec + ' -preset ' + presetOption + ' -r ' + frameRateOption + ' -c:a copy -s ' + resolutionOption + ' ' + RESULT_FOLDER + outputFilename + outputFormat)
    
    # Remove input file immediately after conversion
    try:
        os.remove(UPLOAD_FOLDER + inputFilename + inputFormat)
    except Exception as error:
        print("Error removing or closing downloaded file handle", error)

    # 0 ia success, 1 is failed
    if converted == 0:
        return outputFilename + outputFormat
    else:
        return False
