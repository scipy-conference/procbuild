# SciPy Proceedings Builder

- Customize `server.py` to update this year's branch.
- Launch by running `server.py`.

You need all the same dependencies as for building the proceedings as well:

 - IEEETran (often packaged as ``texlive-publishers``, or download from
   [CTAN](http://www.ctan.org/tex-archive/macros/latex/contrib/IEEEtran/)
   LaTeX class
 - AMSmath LaTeX classes (included in most LaTeX distributions)
 - `docutils` 0.8 or later (``easy_install docutils``)
 - `pygments` for code highlighting (``easy_install pygments``)


```
sudo apt-get install python-docutils texlive-latex-base texlive-publishers \
                     texlive-latex-extra texlive-fonts-recommended
```

