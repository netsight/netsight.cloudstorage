"""
Celery task definitions for netsight.cloudstorage
"""
from celery import Celery
from boto.s3.connection import S3Connection

from aws_key import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

app = Celery()

@app.task
def upload_to_s3():
    conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    print "Got connection"