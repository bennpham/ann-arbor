import os
import shutil
from unittest import TestCase
from pytest_socket import disable_socket

from config.app import PROJECT_ROOT

#
# Module Constants and Vars
#
TEST_PATH = os.path.join(PROJECT_ROOT, 'tests')
TEST_FIXTURES_PATH = os.path.join(TEST_PATH, 'fixtures')
TEST_FIXTURE_FILES_PATH = os.path.join(TEST_FIXTURES_PATH, 'files')


#
# Module Functions
#
def fixture_file_path(fname):
    return os.path.join(TEST_FIXTURE_FILES_PATH, fname)


def delete_directory(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    return dir_path


#
# Project Test Class with Custom Asserts
#
class AppTestCase(TestCase):
    def setUp(self):
        disable_socket()

    def tearDown(self):
        pass

    def assertPathExists(self, path):
        self.assertTrue(os.path.exists(path))

    def assertPathDoesNotExist(self, path):
        self.assertFalse(os.path.exists(path))
