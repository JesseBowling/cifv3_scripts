'''
A hunter that simply creates a log file with indicators submitted to CIF, minus some fields
Set a full path file location in /etc/cif.env with the variable CIF_HUNTER_SUBMISSION_LOGGING_FILE
Be sure hunters are enabled; there must be an integer value set for CIF_HUNTER_THREADS to enable hunters
'''
import logging
import os
import json

CIF_HUNTER_SUBMISSION_LOGGING_FILE = os.getenv('CIF_HUNTER_SUBMISSION_LOGGING_FILE', '/home/cif/submissions.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.handlers.WatchedFileHandler(CIF_HUNTER_SUBMISSION_LOGGING_FILE)
logger.addHandler(fh)


class SubmissionLogging(object):

    def __init__(self):
        self.is_advanced = False

    def process(self, i, router):
        l = i.__dict__()
        # Remove fields not useful for this log
        for field in ['uuid', 'tlp', 'confidence', 'group']:
            l.pop(field)
        logger.info('{}'.format(json.dumps(l)))


Plugin = SubmissionLogging
