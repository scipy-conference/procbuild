# SciPy Proceedings Builder

## Quickstart: Docker Container

If you already have docker engine setup, you should be able to run a version of the proceedings server by running 

```bash
docker run -it -p 7001:7001 scipyproc/procbuild
```

Then, if you go to localhost:7001, you should see the server interface, and you
can manually trigger builds by clicking the button on the right hand side.

This will occupy the terminal, when you want to shut down the server and stop
running the image you will need to type <kbd>ctrl</kbd><kbd>C</kbd>. This should
shutdown the server and stop running the image.

## Building the Docker image

If you want to build the Docker image from the Dockerfile contained here you should run:

```bash
docker build -t yourname/procbuild .
```

which will create a docker image in your local repository that you can run with:

```bash
docker run -it -p 7001:7001 yourname/procbuild
```

## General notes

- Customize `runserver.py` to update this year's branch.
  For debugging, enable ``ALLOW_MANUAL_BUILD_TRIGGER``.
- In the `scipy-conference/scipy_proceedings` repo: in the webhooks add a payload 
  URL pointing to the webapp (such as `http://server.com:5000/webhook`). You must 
  select only Pull Requests in the checkbox menu.
- Install dependencies: ``pip install -r requirements.txt``
- Fetch PRs by running `./update_prs`
- Launch by running `runserver.py`

Note: the server should run on both Python 2 and 3.

You need all the same dependencies as for building the proceedings as well:

 - IEEETran (often packaged as ``texlive-publishers``, or download from
   [CTAN](http://www.ctan.org/tex-archive/macros/latex/contrib/IEEEtran/)
   LaTeX class
 - AMSmath LaTeX classes (included in most LaTeX distributions)
 - `docutils` 0.11 or later (``easy_install docutils``)
 - `pygments` for code highlighting (``easy_install pygments``)

```
sudo apt-get install python-docutils texlive-latex-base texlive-publishers \
                     texlive-latex-extra texlive-fonts-recommended \
                     texlive-bibtex-extra
```


