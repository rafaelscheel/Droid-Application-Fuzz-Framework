"""
Fuzz Server
"""
import os
import re
import sys
import atexit
from AppCommunication.app import App
from distutils import util

from flask import (
    Flask,
    abort,
    send_from_directory,
    request,
    jsonify
)
from browser_fuzz import (
    generate_html,
    start_browser_fuzz
)
from pdf_fuzz import (
    start_pdf_fuzz
)

import settings
import utils
from json import JSONEncoder

sys.tracebacklimit = 0
APP = Flask(__name__)
FILENAME_REGEX = re.compile(r"^[^\\\/]*\.(\w{3,4})$")
appFarm = dict()

'''SCRA 06.10.21: Allow classes to implement "to_json" and get json serializable'''
'''Will re-write this application to an actual language soon...'''
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default


@APP.route('/register')
def app_register():
    appFarm[utils.stripAllExceptAlphanumericAndDot(request.args.get('deviceID'))] = App(
        utils.stripAllExceptAlphanumericAndDot(request.args.get('deviceID')),
        utils.stripAllExceptAlphanumericAndDot(request.args.get('ip')),
        int(request.args.get('port')),
        utils.stripAllExceptAlphanumericAndDot(request.args.get('package')),
        utils.stripAllExceptAlphanumericAndDot(request.args.get('intentLauncher')),
        bool(util.strtobool(request.args.get('ready')))
    )
    return appFarm[utils.stripAllExceptAlphanumericAndDot(request.args.get('deviceID'))].asHTML()


@APP.route('/apps')
def app_list():
    return appFarm


@APP.route('/app')
def app_get():
    if appFarm.has_key(request.args.get('deviceID')):
        return appFarm[request.args.get('deviceID')].to_json()
    abort(404)


@APP.route('/appRemove')
def app_remove():
    if appFarm.has_key(request.args.get('deviceID')):
        del appFarm[request.args.get('deviceID')]
        return "deleted"
    abort(404)


@APP.route('/appUpdateStatus')
def app_update_status():
    if appFarm.has_key(request.args.get('deviceID')):
        appFarm[request.args.get('deviceID')].ready = bool(util.strtobool(request.args.get('ready')))
        return appFarm[request.args.get('deviceID')].to_json()
    abort(404)


@APP.route('/html/<filename>')
def serve_html_pregenerated_files(filename):
    """Pre Generated HTML Files"""
    if filename.endswith(".html") and re.match(FILENAME_REGEX, filename):
        pregen_html_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "generators/html/htmls/")
        return send_from_directory(pregen_html_dir, filename)
    abort(404)


@APP.route('/pdf/<filename>')
def serve_pdf_pregenerated_files(filename):
    """Pre Generated Files"""
    if filename.endswith(".pdf") and re.match(FILENAME_REGEX, filename):
        pregen_pdf_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "generators/pdf/pdfs")
        return send_from_directory(pregen_pdf_dir, filename)
    abort(404)


@APP.route('/fuzz_html/<req_id>', methods=['GET', 'POST'])
def gen_fuzz_html(req_id):
    """Generate Fuzz HTML"""
    if req_id.isdigit():
        return generate_html(req_id)
    abort(404)


@APP.route('/fuzz_pdf/<filename>')
def serve_pdf_fuzz_files(filename):
    """Fuzzer Generated Files"""
    if filename.endswith(".pdf") and re.match(FILENAME_REGEX, filename):
        fuzz_output_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "fuzz_files")
        return send_from_directory(fuzz_output_dir, filename)
    abort(404)


@APP.route('/browser_fuzz', methods=['POST'])
def browser_fuzz():
    """Start Browser Fuzzer"""
    browser = request.form.get('browser')
    fuzzer = request.form.get('fuzzer')
    iteration = request.form.get('iteration')
    start_browser_fuzz(browser, fuzzer, int(iteration))
    return "Browser Fuzzing Started"


@APP.route('/pdf_fuzz', methods=['POST'])
def pdf_fuzz():
    """Start PDF Fuzzer"""
    pdf_reader = request.form.get('pdf_reader')
    fuzzer = request.form.get('fuzzer')
    iteration = request.form.get('iteration')
    start_pdf_fuzz(pdf_reader, fuzzer, int(iteration))
    return "PDF Reader Fuzzing Started"


@APP.route('/crashes', methods=['POST'])
def get_crashes():
    """Get Crashes if any"""
    crash_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "crash")
    if os.path.exists(crash_dir):
        allfiles = os.listdir(crash_dir)
        file_list = [filename for filename in allfiles if filename.endswith(
            ".html") or filename.endswith(".pdf")]
        if len(file_list) > 0:
            return jsonify({"crash": len(file_list), "files": file_list})
    return jsonify({"crash": 0, "files": []})


@APP.route('/stop', methods=['POST'])
def shutdown():
    """Shut down the server"""
    utils.adb_kill()
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@APP.route('/js/<path:path>')
def send_js(path):
    js_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "static", "js")
    return send_from_directory(js_dir, path)


@APP.route('/css/<path:path>')
def send_css(path):
    css_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "static", "css")
    return send_from_directory(css_dir, path)


@APP.route('/', methods=['GET'])
def main():
    """UI"""
    with open('static/index.html', 'r') as filep:
        return filep.read()


def cleanup():
    utils.adb_kill()


if __name__ == '__main__':
    atexit.register(cleanup)
    APP.run(threaded=True, host=settings.SERVER_IP,
            port=settings.SERVER_PORT, debug=settings.DEBUG)
