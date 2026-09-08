.PHONY: all

all: paper-draft.pdf

TEMPLATE = template/ceurart.cls template/cc-by.pdf template/ceur-ws-logo.pdf

paper-draft.pdf: main.tex sources.bib $(TEMPLATE) Makefile
	mkdir -p .build
	cp main.tex sources.bib $(TEMPLATE) .build/
	cd .build && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
	cp .build/main.pdf paper-draft.pdf
