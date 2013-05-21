from flask import Flask, render_template, url_for, send_file
import json
import os

from builder import build as build_paper

app = Flask(__name__)

pr_info = json.load(open('data/pr_info.json'))

papers = [(str(n), pr) for n, pr in enumerate(pr_info)]


if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("/tmp/flask.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)


@app.route('/')
def index():
    return render_template('index.html', papers=papers,
                           build_url=url_for('build', nr=''))

@app.route('/build/<nr>')
def build(nr):
    pr = pr_info[int(nr)]
    pdf = ''
    try:
        pdf = build_paper(user=pr['user'], branch=pr['branch'], target=nr)
    except RuntimeError as e:
        render_template('build.html', error=e.message, pdf=pdf)

        #    data = open(pdf, 'r').read()
        #    response = make_response(data)
        #    response["Content-Disposition"] = "attachment; filename=%s.pdf" % nr
        #    return response
    return send_file(pdf)


if __name__ == "__main__":
    app.run(debug=True)
