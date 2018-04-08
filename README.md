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
  For debugging, enable `ALLOW_MANUAL_BUILD_TRIGGER`.
- In the `scipy-conference/scipy_proceedings` repo: in the webhooks add a payload 
  URL pointing to the webapp (such as `http://server.com:5000/webhook`). You must 
  select only Pull Requests in the checkbox menu.
- Install dependencies: `pip install -r requirements.txt`
- Fetch PRs by running `./update_prs`
- Launch by running `runserver.py`

Note: the server will run only on 3.6+

You need all the same dependencies as for building the proceedings as well.

This includes some packages on pypi which we'll install with `pip`. The easiest
way to do this is by pulling down the latest version of the file with `curl`:

```
pip install -r <(curl https://raw.githubusercontent.com/scipy-conference/scipy_proceedings/2018/requirements.txt)
```

Additionally, you will need to install a version of LaTeX and some external
packages. We encourage you to visit https://www.tug.org/texlive/ to see how to
best install LaTeX for your system.

 - IEEETran LaTeX class
     - (often packaged as `texlive-publishers`, or download from
       [CTAN](http://www.ctan.org/tex-archive/macros/latex/contrib/IEEEtran/))
 - AMSmath LaTeX classes (included in most LaTeX distributions)

If you can use `apt-get`, you are likely to install everything with:

```
apt-get install python-docutils texlive-latex-base texlive-publishers \
                texlive-latex-extra texlive-fonts-recommended \
                texlive-bibtex-extra
```


