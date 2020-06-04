from os.path import dirname, realpath, join as path_join

PROJECT_ROOT = dirname(dirname(realpath(__file__)))
AUDITS_DIR = path_join(PROJECT_ROOT, 'audits')
