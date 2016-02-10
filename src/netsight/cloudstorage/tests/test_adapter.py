from plone import api

from .base import BaseTestCase
from ..interfaces import ICloudStorage


class TestCloudStorage(BaseTestCase):

    def setUp(self):
        super(TestCloudStorage, self).setUp()
        self.login_as_portal_owner()
        self.a_file = api.content.create(
            self.portal,
            'File',
            'example-file',
            'file.txt'
        )
        self.doc = api.content.create(
            self.portal,
            'Document',
            'example-document',
            'A document'
        )

    def test__getFields(self):
        fields = ICloudStorage(self.a_file)._getFields(ignore_empty=True)
        self.assertEqual(len(fields), 0)

        fields = ICloudStorage(self.a_file)._getFields(ignore_empty=False)
        self.assertGreater(len(fields), 0)

        fields = ICloudStorage(self.doc)._getFields()
        self.assertEqual(len(fields), 0)

    def test_enqueue(self):
        """
        Not actually testing Celery or AWS.

        1. enqueue an object
        2. check that it has "in_progress" fields

        """
        self.fail()
