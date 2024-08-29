\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{nicegram}[2024/08/19 Custom class for TikZ standalone images]

% Load the standalone class with TikZ
\LoadClass[border=0.5cm]{standalone}

% Load necessary packages
\RequirePackage{tikz}
%\RequirePackage{mathpazo} % Example for using Palatino
\RequirePackage{helvet} % use Helvetica

% Define custom settings for TikZ
\tikzset{
    mydefault/.style={
        font=\sffamily\large, % Change \sffamily to \rmfamily or \ttfamily
        draw=blue!50!black,
        fill=blue!20,
        thick,
        line width=1mm,
    },
    every node/.append style={font=\sffamily\large}, % Force font for all nodes
    every path/.style={
        line width=1.2pt, % Override default to ensure all lines are thick
        line join=round, % Round line joins
        miter limit=1, % Miter limit
    },
    every axis/.style={
        line width=1.2pt, % This ensures all axes are thick
        tick style={line width=1.2pt}, % Ensures that the tick marks are also thick
        major grid style={line width=1.2pt}, % Thickens the major grid lines
        minor grid style={line width=0.8pt}, % Optionally, you can thicken minor grid lines
        ->, % Arrow style
        >=latex, % Arrowhead style
    },
}

\endinput
