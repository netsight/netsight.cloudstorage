import os
from plone import api
from App.config import getConfiguration
from moto import mock_s3

from .base import BaseTestCase
from ..interfaces import ICloudStorage


def test_file_data():
    filename = os.path.join(os.path.dirname(__file__),
                            u'test.pdf')
    return open(filename).read()


class TestCloudStorage(BaseTestCase):

    def setUp(self):
        super(TestCloudStorage, self).setUp()

        # Lower the minimum file size for tests
        api.portal.set_registry_record(
            'netsight.cloudstorage.interfaces.ICloudStorageSettings.'
            'min_file_size',
            0,
        )
        api.portal.set_registry_record(
            'netsight.cloudstorage.interfaces.ICloudStorageSettings.'
            'bucket_name',
            u'testing',
        )
        portal = api.portal.get()

        main_config = getConfiguration()
        main_config.product_config = {
            'netsight.cloudstorage': {
                'plone_url': portal.absolute_url(),
            }
        }

        self.login_as_portal_owner()
        self.a_file = api.content.create(
            container=self.portal,
            type='File',
            id='test.pdf',
        )
        data = test_file_data()
        self.a_file.setFile(data,
                            filename='test.pdf')
        self.doc = api.content.create(
            container=self.portal,
            type='Document',
            title='A document',
        )

    def test__getFields(self):
        fields = ICloudStorage(self.a_file)._getFields(ignore_empty=True)
        self.assertEqual(len(fields), 1)

        fields = ICloudStorage(self.a_file)._getFields(ignore_empty=False)
        self.assertGreater(len(fields), 0)

        fields = ICloudStorage(self.doc)._getFields()
        self.assertEqual(len(fields), 0)

    @mock_s3
    def test_enqueue(self):
        """
        Not actually testing Celery or AWS.

        1. enqueue an object
        2. check that it has "in_progress" fields

        """
        ICloudStorage(self.a_file).enqueue()
