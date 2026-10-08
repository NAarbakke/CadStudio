% CadStudio technical report class: a plain article in Latin Modern, in the manner of a research
% memorandum. Compile with LuaLaTeX (tools/latex_report.py does this).
% Text block is 150 mm wide; latex_report.TEXT_WIDTH_IN matches it.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{cadstudio}[2026/10/08 CadStudio technical report]
\LoadClass[11pt,a4paper]{article}

\RequirePackage[a4paper,hmargin=30mm,top=30mm,bottom=32mm,headheight=14pt]{geometry}
\RequirePackage{amsmath}
\RequirePackage{unicode-math}   % Latin Modern text and maths, the LuaLaTeX defaults
\RequirePackage{microtype}
\RequirePackage{graphicx}
\RequirePackage{array,booktabs,tabularx}
\RequirePackage{siunitx}
\RequirePackage{float}
\RequirePackage{caption}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage{multicol}
\RequirePackage[hidelinks]{hyperref}

\sisetup{per-mode=symbol,group-minimum-digits=5,table-align-text-after=false}
\setlist{topsep=3pt,itemsep=0pt,parsep=2pt}
\captionsetup{font=small,labelfont=bf,labelsep=period,width=0.92\textwidth}
\captionsetup[table]{position=top,skip=6pt}
\renewcommand{\arraystretch}{1.15}
\g@addto@macro\@floatboxreset{\centering}
\renewcommand{\topfraction}{0.9}\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.1}\renewcommand{\floatpagefraction}{0.8}

% Document data
\newcommand{\cs@subtitle}{}\newcommand{\cs@id}{}\newcommand{\cs@revision}{A}
\newcommand{\subtitle}[1]{\renewcommand{\cs@subtitle}{#1}}
\newcommand{\documentid}[1]{\renewcommand{\cs@id}{#1}}
\newcommand{\revision}[1]{\renewcommand{\cs@revision}{#1}}
\author{CadStudio}
\AtBeginDocument{\let\cs@title\@title   % \maketitle clears \@title; the running head still needs it
  \hypersetup{pdftitle={\@title: \cs@subtitle},pdfauthor={\@author},pdfcreator={CadStudio}}}

% Title block: report number, title, subtitle, author, date
\renewcommand{\@maketitle}{%
  \newpage\null
  \begin{center}
    {\small\textsc{CadStudio Technical Report}\quad\cs@id\quad\textsc{Revision}~\cs@revision\par}
    \vskip 2.2em
    {\LARGE\@title\par}
    \vskip 0.6em
    {\large\itshape\cs@subtitle\par}
    \vskip 1.6em
    {\large\@author\par}
    \vskip 0.5em
    {\@date\par}
  \end{center}
  \vskip 1.5em}

% Running head
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\itshape\cs@title}
\fancyhead[R]{\small\cs@id, Rev.~\cs@revision}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% \begin{nomenclature} \item[$A$] flow area ... \end{nomenclature}: a two-column symbol list
\newenvironment{nomenclature}{\section*{Nomenclature}\begin{multicols}{2}\raggedright
  \begin{description}[font=\normalfont,labelwidth=3em,leftmargin=3.8em,labelsep=0.8em,itemsep=0pt,topsep=0pt]}
  {\end{description}\end{multicols}}

% Text set under a table
\newcommand{\tablenote}[1]{\par\vspace{3pt}{\footnotesize #1\par}}
