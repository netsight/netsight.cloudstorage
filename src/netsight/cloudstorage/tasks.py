"""
Celery task definitions for netsight.cloudstorage
"""
from io import BytesIO
import logging
import math
import sys

from boto import elastictranscoder
from boto.gs.connection import Location
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from celery import Celery, Task
import requests

logger = logging.getLogger('netsight.cloudstorage.celery_tasks')
# TODO: Make broker_url customisable (OMG SO HARD!!)
broker_url = 'redis://localhost:6379/0'
app = Celery('netsight.cloudstorage.tasks', broker=broker_url)


class S3Task(Task):
    """
    Subclass of Celery Task to add failure handling for dodgy S3 gubbins
    """
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        field = kwargs['field']
        security_token = kwargs['security_token']
        source_url = kwargs.get('source_url', 'Unknown URL')
        error_callback = kwargs.get('errorback_url')
        logger.error('%s', einfo.traceback)
        logger.error('While uploading %s.', source_url)
        params = {
            'identifier': field['name'],
            'security_token': security_token
        }
        r = requests.get(error_callback, params=params)


@app.task(base=S3Task)
def upload_to_s3(bucket_name,
                 source_url,
                 callback_url,
                 errorback_url,
                 field,
                 security_token,
                 aws_key,
                 aws_secret_key):
    """
    Upload a file from the given Plone path to S3



    :param errorback_url: URL to call if the task fails
    :type errorback_url: str
    :param callback_url: URL to call once the upload has completed
    :type callback_url: str
    :param bucket_name: name of the bucket to upload to/create
    :type bucket_name: str
    :param source_url: path to the object to be uploaded
    :type source_url: str
    :param field: field information of the file to be uploaded
    :type field: dict
    :param security_token: security token to authorise retrieving the file
    :type security_token: str
    :param aws_key: AWS Access Key
    :type aws_key: str
    :param aws_secret_key: AWS Secret Access Key
    :type aws_secret_key: str
    :return: Callback URL and security params for callback task
    :rtype: tuple
    """
    s3 = S3Connection(aws_key, aws_secret_key)
    in_bucket = s3.lookup(bucket_name)
    if in_bucket is None:
        logger.warn(
            'No bucket with name %s exists, creating a new one' %
            bucket_name
        )
        in_bucket = s3.create_bucket(bucket_name, location=Location.EU)

    k = Key(in_bucket)
    dest_filename = '%s-%s' % (field['name'], field['context_uid'])
    k.key = dest_filename

    logger.info('Fetching %s from %s', field['name'], source_url)

    params = {
        'identifier': field['name'],
        'security_token': security_token
    }
    #TODO: Stream file download
    r = requests.get(source_url, params=params)
    file_data = BytesIO(r.content)
    file_size = sys.getsizeof(r.content)
    chunk_size = 10 * 1024 * 1024  # 1MB chunk size
    chunk_count = int(math.ceil(file_size / chunk_size))
    multipart = in_bucket.initiate_multipart_upload(dest_filename)

    logger.info(
        'Uploading some data to %s with key: %s' %
        (in_bucket.name, k.key)
    )
    for i in range(chunk_count + 1):
        offset = chunk_size * i
        num_bytes = min(chunk_size, file_size - offset)
        with BytesIO(file_data.read(num_bytes)) as chunk:
            multipart.upload_part_from_file(chunk, part_num=i+1)
    multipart.complete_upload()

    logger.info('Upload complete')
    # Returning the params here so they can be used in the callback
    return params, callback_url


@app.task
def upload_callback(args):
    """
    When a file is successfully uploaded to S3, alert Plone to this fact

    :param args: The callback_url and the params required to validate it
    :type args: tuple
    """
    params = args[0]
    callback_url = args[1]
    logger.info(
        'Calling %s to alert Plone that %s is uploaded',
        callback_url,
        params['identifier']
    )
    requests.get(callback_url, params=params)


@app.task()
def transcode_video():
    transcoder = elastictranscoder.connect_to_region('eu-west-1')
    pipelines = transcoder.list_pipelines()
    if 'Pipelines' in pipelines and len(pipelines['Pipelines']) > 0:
        pipeline = [
            x for x in pipelines['Pipelines'] if
            'awstest-transcoder' in x['Name']
        ][0]
    else:
        pipeline_name = "awstest-pipeline"
        print "Creating new pipeline with name: " + pipeline_name
        pipeline = transcoder.create_pipeline(
            'awstest-pipeline',
            in_bucket.name,
            out_bucket.name,
            role='arn:aws:iam::377178956182:role/Transcoding',
            notifications={
                "Progressing": "",
                "Completed": "",
                "Warning": "",
                "Error": "",
            })
