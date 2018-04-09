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


## Pushing the Docker image to SciPy's DockerHub repository

We have files listed in `.dockerignore` that should not be included in the repository. Otherwise all other files in the directory will be included.

Before you begin the following, you should be sure to set the `MASTER_BRANCH` evironment variable. 

```bash
export MASTER_BRANCH=2018
```

If you want to push the image to DockerHub so that it can be publicly available you would need to assign it the `scipyproc/procbuild` tag. 


```bash
docker build -t scipyproc/procbuild .
```

You should also increment the version number. You do this by adding a new tag.

```bash
docker tag scipyproc/procbuild scipyproc/procbuild:x.y.$MASTER_BRANCH
```

Then you should push these up to the DockerHub repository (the default repository). This should push up both the latest version and the version number.

```bash
docker push scipyproc/procbuild:latest
docker push scipyproc/procbuild:x.y.$MASTER_BRANCH
```

## Pushing the Docker image to Heroku's repository

We run the server on in a Heroku called procbuild, found at [http://procbuild.herokuapp.com](http://procbuild.herokuapp.com). 

In order to update the deployed version of the app, we need to push the image from our local repository to the heroku repository.

This requires first retagging the image, specifically we need to tag the image in a way that the heroku registry expects. 

You can do this with the same tagging functionality

```bash
docker tag scipyproc/procbuild registry.heroku.com/procbuild/web
```

Then you need to push it to the heroku registry

```bash
docker push registry.heroku.com/procbuild/web
```

## Working with Travis

[Travis](https://travis-ci.org/scipy-conference/procbuild) is our continuous
integration system. We use it to run tests (via `pytest`) and to build and
deploy our docker images to DockerHub and Heroku, which backs the [procbuild.scipy.org](http://procbuild.scipy.org) website.

### Updating the year

When running Travis, we need to know the `MASTER_BRANCH` so that we can create
appropriate docker image numbers.

```bash
travis env set MASTER_BRANCH $MASTER_BRANCH --public
```

### What should travis do when you make a PR?

We have set Travis up to attempt to build a Docker image from the Dockerfile on 
every PR and commit.

If you want to change this behaviour, you will need to change the top-level
`script` field in `.travis.yml`. But, you will also need to change the scripts
in the `build_scripts/` directory to handle whatever changes you make.

### What should travis do when `master` changes?

We have set Travis up to deploy and push the docker images it builds to
[DockerHub](https://hub.docker.com/r/scipyproc/procbuild/) and to 
[Heroku's Docker registry](https://devcenter.heroku.com/articles/container-registry-and-runtime#logging-in-to-the-registry).

This deploy script should be triggered every time any commit is made to master.
This includes both PRs being merged into master and commits made directly to
master.

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


