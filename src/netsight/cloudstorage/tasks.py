# -- The contents of this file is copyright (c) 2011 Netsight Internet     -- #
# -- Solutions Ltd. All rights reserved. Please see COPYRIGHT.txt and      -- #
# -- LICENCE.txt for further information.                                  -- #
"""
Celery task definitions for netsight.cloudstorage
"""
from io import BytesIO
import logging
import math
import sys

from boto import elastictranscoder
from boto.gs.connection import Location
from boto.s3 import connect_to_region
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
        """
        Override default celery task failure handling to ensure required data
        is passed around
        """
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
        requests.get(error_callback, params=params)


def create_bucket(conn, bucket_name):
    bucket = conn.lookup(bucket_name)
    if bucket is None:
        logger.warn(
            'No bucket with name %s exists, creating a new one' %
            bucket_name
        )
        # TODO: location needs to be configurable
        bucket = conn.create_bucket(bucket_name, location=Location.EU)
    return bucket


def create_s3_connection(aws_key, aws_secret_key):
    # TODO: make region configurable
    region = u'eu-west-1'
    conn = connect_to_region(
        region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret_key
    )
    logger.info('Connected to S3 region: %s', conn._connection[0])
    return conn


@app.task(base=S3Task)
def upload_to_s3(bucket_name,
                 pipeline_name,
                 source_url,
                 callback_url,
                 errorback_url,
                 field,
                 security_token,
                 aws_key,
                 aws_secret_key):
    """
    Upload a file from the given Plone path to S3

    :param pipeline_name: Name of the transcoding pipeline to create
    :type pipeline_name: str
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
    conn = create_s3_connection(aws_key, aws_secret_key)
    in_bucket = create_bucket(conn, bucket_name)
    logger.info('Using bucket %s', bucket_name)
    k = Key(in_bucket)
    dest_filename = '%s-%s' % (field['name'], field['context_uid'])
    k.key = dest_filename
    logger.info('Fetching %s from %s', field['name'], source_url)

    params = {
        'identifier': field['name'],
        'security_token': security_token
    }
    # TODO: Stream file download
    r = requests.get(source_url, params=params)
    file_data = BytesIO(r.content)
    file_size = sys.getsizeof(r.content, 0)
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
    retval = {
        'params': params,
        'callback_url': callback_url,
        'dest_filename': dest_filename,
        'aws_key': aws_key,
        'aws_secret_key': aws_secret_key,
        'pipeline_name': pipeline_name,
    }
    return retval


@app.task
def upload_callback(upload_result):
    """
    When a file is successfully uploaded to S3, alert Plone to this fact

    :param upload_result: The callback_url and the params required to validate
                          it
    :type upload_result: dict
    """
    params = upload_result['params']
    callback_url = upload_result['callback_url']
    logger.info(
        'Calling %s to alert Plone that %s is uploaded',
        callback_url,
        params['identifier']
    )
    params['activity'] = 'upload'
    r = requests.get(callback_url, params=params)
    logger.info('HTTP: %s when calling %s', r.status_code, callback_url)
    if r.status_code != 200:
        logger.error('Callback request failed: %s', str(vars(r)))
        raise requests.RequestException(response=r)
    return upload_result


@app.task()
def transcode_video(upload_result):
    """
    If the uploaded file is a video, then trigger a transcoding job.

    :param upload_result: The result of the previous celery task (upload_to_s3)
    """
    aws_key = upload_result['aws_key']
    aws_secret_key = upload_result['aws_secret_key']
    source_file = upload_result['dest_filename']
    pipeline_name = '%s-pipeline' % upload_result['pipeline_name']

    transcoder = elastictranscoder.connect_to_region(
        'eu-west-1',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret_key
    )
    pipelines = dict((
        (x.get('Name'), x.get('Id'))
        for x in transcoder.list_pipelines().get('Pipelines', [])
    ))
    if pipeline_name in pipelines:
        pipeline_id = pipelines[pipeline_name]
    else:
        logger.error('Pipeline %s does not exist. Please contact sysadmin',
                     pipeline_name)
        return

    logger.info('Creating transcoding job for %s', source_file)
    transcode_input = {
        'Key': source_file,
        'FrameRate': 'auto',
        'Resolution': 'auto',
        'AspectRatio': 'auto',
        'Interlaced': 'auto',
        'Container': 'auto'
    }
    transcode_output = {
        # TODO: Configurable preset
        'PresetId': '1351620000001-000020',
        'Key': source_file
    }
    transcoder.create_job(
        pipeline_id=pipeline_id,
        input_name=transcode_input,
        output=transcode_output
    )
    return upload_result


@app.task
def transcode_callback(transcode_result):
    """
    When a file is successfully uploaded to S3, alert Plone to this fact

    :param transcode_result: The callback_url and the params required to
                             validate it
    :type transcode_result: dict
    """
    params = transcode_result['params']
    callback_url = transcode_result['callback_url']
    logger.info(
        'Calling %s to alert Plone that %s is being transcoded',
        callback_url,
        params['identifier']
    )
    params['activity'] = 'transcode'
    requests.get(callback_url, params=params)
    return transcode_result
